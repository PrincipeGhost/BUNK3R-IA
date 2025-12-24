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

from flask import Flask, jsonify, render_template, Response, abort
from BUNK3R_IA.config import get_config
from BUNK3R_IA.api.routes import ai_bp, set_db_manager
from BUNK3R_IA.api.project_routes import projects_bp
from BUNK3R_IA.api.github_routes import github_bp
from BUNK3R_IA.api.automation_routes import automation_bp

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_class=None):
    """Factory para crear la aplicación Flask"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app = Flask(__name__, 
                template_folder=os.path.join(base_dir, 'templates'),
                static_folder=os.path.join(base_dir, 'static'))
    
    if config_class is None:
        config_class = get_config()
    
    app.config.from_object(config_class)
    
    app.register_blueprint(ai_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(github_bp)
    app.register_blueprint(automation_bp)
    
    # Habilitar CORS para permitir peticiones externas (necesario para integración)
    from flask_cors import CORS
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    @app.after_request
    def add_header(response):
        # Cache control
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        # Permitir Embedding (Iframe)
        # Esto es crucial para que la página parezca "incrustada" en el otro sitio
        response.headers['X-Frame-Options'] = 'ALLOWALL' 
        response.headers['Content-Security-Policy'] = "frame-ancestors *;"
        response.headers['Access-Control-Allow-Origin'] = "*"
        response.headers['Access-Control-Allow-Methods'] = "GET, POST, OPTIONS, PUT, DELETE"
        response.headers['Access-Control-Allow-Headers'] = "Content-Type, Authorization"
        
        return response
    
    @app.route('/')
    def index():
        return render_template('workspace.html')
    
    @app.route('/preview/<session_id>')
    def serve_preview(session_id):
        """Serve generated HTML preview"""
        from BUNK3R_IA.core.live_preview import live_preview
        
        safe_session = ''.join(c for c in session_id if c.isalnum() or c in '-_')
        
        if not safe_session:
            abort(400, "Invalid session ID")
        
        html_content = live_preview.get_project_html(safe_session)
        
        if html_content:
            return Response(html_content, mimetype='text/html')
        else:
            return Response(
                '''<!DOCTYPE html>
                <html>
                <head><title>Preview No Disponible</title>
                <style>
                    body { 
                        font-family: system-ui, -apple-system, sans-serif; 
                        display: flex; justify-content: center; align-items: center; 
                        height: 100vh; margin: 0; 
                        background: #1a1a2e; color: #eee; 
                    }
                    .container { text-align: center; }
                    h1 { color: #FFD700; }
                </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Preview No Disponible</h1>
                        <p>El proyecto solicitado no existe o ha expirado.</p>
                    </div>
                </body>
                </html>''',
                status=404,
                mimetype='text/html'
            )
    
    @app.route('/api/info')
    def api_info():
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
