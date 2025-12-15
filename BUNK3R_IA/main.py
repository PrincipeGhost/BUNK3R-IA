#!/usr/bin/env python3
"""
BUNK3R_IA - Servidor Principal de IA
Ejecuta el sistema de IA de forma independiente

Uso:
    python -m BUNK3R_IA.main
    o
    python BUNK3R_IA/main.py
"""
import os
import sys
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify
from BUNK3R_IA.config import get_config
from BUNK3R_IA.api.routes import ai_bp, set_db_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_class=None):
    """Factory para crear la aplicación Flask"""
    app = Flask(__name__)
    
    if config_class is None:
        config_class = get_config()
    
    app.config.from_object(config_class)
    
    app.register_blueprint(ai_bp)
    
    @app.route('/')
    def index():
        return jsonify({
            'service': 'BUNK3R_IA',
            'version': '1.0.0',
            'status': 'running',
            'timestamp': datetime.now().isoformat(),
            'endpoints': {
                'health': '/api/health',
                'ai_chat': '/api/ai/chat',
                'ai_constructor': '/api/ai-constructor/process',
                'ai_toolkit': '/api/ai-toolkit/*',
                'ai_core': '/api/ai-core/*'
            }
        })
    
    @app.route('/status')
    def status():
        from BUNK3R_IA.core.ai_service import get_ai_service
        
        ai_available = False
        providers = []
        
        try:
            ai = get_ai_service(None)
            if ai:
                ai_available = True
                providers = ai.get_available_providers()
        except:
            pass
        
        return jsonify({
            'success': True,
            'ai_service': ai_available,
            'providers': providers,
            'config': {
                'debug': app.config.get('DEBUG', False),
                'project_root': config_class.PROJECT_ROOT
            }
        })
    
    return app

def init_database(database_url=None):
    """Inicializar conexión a base de datos (opcional)"""
    if database_url is None:
        database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        logger.warning("No DATABASE_URL configured - running without database")
        return None
    
    try:
        import psycopg2
        from psycopg2 import pool
        
        class SimpleDBManager:
            def __init__(self, url):
                self.pool = pool.SimpleConnectionPool(1, 10, url)
            
            def get_connection(self):
                return self.pool.getconn()
            
            def release_connection(self, conn):
                self.pool.putconn(conn)
        
        db_manager = SimpleDBManager(database_url)
        set_db_manager(db_manager)
        logger.info("Database connection established")
        return db_manager
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return None

def main():
    """Punto de entrada principal"""
    config = get_config()
    
    logger.info("=" * 50)
    logger.info("BUNK3R_IA - Sistema de Inteligencia Artificial")
    logger.info("=" * 50)
    
    init_database()
    
    app = create_app(config)
    
    host = config.HOST
    port = config.PORT
    debug = config.DEBUG
    
    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()
