import os
import sqlite3
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Gestor de bases de datos para BUNK3R-IA.
    Maneja la conexión a la BD Central y permite conexiones dinámicas
    a BDs de usuario y proyecto.
    """
    
    def __init__(self, central_db_path: str):
        self.central_db_path = central_db_path
        self.connections: Dict[str, sqlite3.Connection] = {}
        self._init_central_db()

    def _get_connection(self, path: str) -> sqlite3.Connection:
        """Obtiene o crea una conexión SQLite"""
        if path not in self.connections:
            # Asegurar que el directorio existe
            os.makedirs(os.path.dirname(path), exist_ok=True)
            conn = sqlite3.connect(path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self.connections[path] = conn
        return self.connections[path]

    def _init_central_db(self):
        """Inicializa la tabla central de usuarios si no existe"""
        conn = self._get_connection(self.central_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                user_db_path TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

    def register_user(self, user_id: str) -> str:
        """Registra un nuevo usuario y define su ruta de BD"""
        user_db_path = os.path.join(os.path.dirname(self.central_db_path), f"user_{user_id}.db")
        conn = self._get_connection(self.central_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, user_db_path)
            VALUES (?, ?)
        ''', (user_id, user_db_path))
        conn.commit()
        
        # Inicializar la BD del usuario
        self._init_user_db(user_db_path)
        return user_db_path

    def _init_user_db(self, path: str):
        """Inicializa las tablas en la BD del usuario"""
        conn = self._get_connection(path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                render_url TEXT,
                render_credentials TEXT, -- Cifrado en producción
                github_repo TEXT,
                use_project_db BOOLEAN DEFAULT 0,
                project_db_path TEXT,
                status TEXT DEFAULT 'creating',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT,
                message TEXT,
                level TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

    def get_user_db(self, user_id: str) -> Optional[sqlite3.Connection]:
        """Obtiene la conexión a la BD de un usuario específico"""
        conn_central = self._get_connection(self.central_db_path)
        cursor = conn_central.cursor()
        cursor.execute('SELECT user_db_path FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        if row:
            return self._get_connection(row['user_db_path'])
        return None

    def register_project(self, user_id: str, project_id: str, name: str):
        """Registra un nuevo proyecto en la BD del usuario"""
        user_conn = self.get_user_db(user_id)
        if not user_conn:
            raise ValueError(f"User {user_id} not found")
        
        project_db_path = os.path.join(os.path.dirname(self.central_db_path), f"proj_{project_id}.db")
        cursor = user_conn.cursor()
        cursor.execute('''
            INSERT INTO projects (project_id, name, project_db_path)
            VALUES (?, ?, ?)
        ''', (project_id, name, project_db_path))
        user_conn.commit()

# Instancia global por defecto (para simplificar integración inicial)
db_base_path = os.path.join(os.getcwd(), 'BUNK3R_IA', 'core', 'database')
central_db = os.path.join(db_base_path, 'central.db')
manager = DatabaseManager(central_db)
