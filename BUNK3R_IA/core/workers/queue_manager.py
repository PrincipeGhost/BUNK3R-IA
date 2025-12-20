import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from BUNK3R_IA.core.database.manager import manager as db_manager

logger = logging.getLogger(__name__)

class QueueManager:
    """
    Gestor de Cola de Tareas (Task Queue) basado en SQLite.
    Se integra con la BD Central para persistencia.
    """
    
    def __init__(self):
        self.db = db_manager
        self._init_queue_table()

    def _init_queue_table(self):
        """Inicializa la tabla de tareas en la BD Central"""
        conn = self.db._get_connection(self.db.central_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_queue (
                task_id TEXT PRIMARY KEY,
                task_type TEXT NOT NULL,
                payload TEXT NOT NULL, -- JSON
                priority INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending', -- pending, processing, completed, failed
                user_id TEXT,
                project_id TEXT,
                result TEXT, -- JSON
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

    def enqueue_task(self, task_type: str, payload: Dict[str, Any], user_id: str, project_id: str = None, priority: int = 0) -> str:
        """Agrega una nueva tarea a la cola"""
        import uuid
        task_id = str(uuid.uuid4())
        payload_json = json.dumps(payload)
        
        conn = self.db._get_connection(self.db.central_db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO task_queue (task_id, task_type, payload, priority, user_id, project_id, status)
                VALUES (?, ?, ?, ?, ?, ?, 'pending')
            ''', (task_id, task_type, payload_json, priority, user_id, project_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        
        logger.info(f"Task enqueued: {task_id} [{task_type}]")
        return task_id

    def fetch_next_task(self) -> Optional[Dict[str, Any]]:
        """Obtiene la siguiente tarea pendiente (FIFO con Prioridad) y la marca como processing"""
        conn = self.db._get_connection(self.db.central_db_path)
        conn = self.db._get_connection(self.db.central_db_path)
        # Asegurar uso de Row Factory para este scope
        import sqlite3
        conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        
        # Transacción para asegurar atomicidad básica
        try:
            cursor.execute('BEGIN IMMEDIATE')
            
            cursor.execute('''
                SELECT * FROM task_queue 
                WHERE status = 'pending'
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
            ''')
            row = cursor.fetchone()
            
            if row:
                # Row es un objeto sqlite3.Row
                task_data = dict(row)
                task_id = task_data['task_id']
                
                cursor.execute('''
                    UPDATE task_queue 
                    SET status = 'processing', updated_at = CURRENT_TIMESTAMP
                    WHERE task_id = ?
                ''', (task_id,))
                
                conn.commit()
                return task_data
            else:
                conn.commit()
                return None
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Error fetching task: {e}")
            return None

    def update_task_status(self, task_id: str, status: str, result: Dict[str, Any] = None, error: str = None):
        """Actualiza el estado de una tarea"""
        conn = self.db._get_connection(self.db.central_db_path)
        cursor = conn.cursor()
        
        result_json = json.dumps(result) if result else None
        
        cursor.execute('''
            UPDATE task_queue 
            SET status = ?, result = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
            WHERE task_id = ?
        ''', (status, result_json, error, task_id))
        conn.commit()

# Instancia global
queue_manager = QueueManager()
