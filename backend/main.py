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
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, render_template, Response, abort, session
from backend.config import get_config
from backend.api.routes import ai_bp, set_db_manager
from backend.api.project_routes import projects_bp
from backend.api.github_routes import github_api_bp
from backend.api.automation_routes import automation_bp
from backend.api.terminal_routes import terminal_bp
from backend.api.repo_manager import repo_mgr_bp
from backend.api.preview_routes import preview_bp
from backend.api.extension_routes import extension_bp
from backend.api.ide_routes import ide_bp
from backend.api.github_sync_routes import github_sync_bp
from backend.api.workspace_manager import workspace_bp
from backend.models import db
from backend.replit_auth import login_manager, require_login

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
                static_folder=os.path.join(base_dir, 'static'),
                static_url_path='/bunk3r-static')
    
    if config_class is None:
        config_class = get_config()
    
    app.config.from_object(config_class)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    app.config['SESSION_COOKIE_NAME'] = 'bunk3r_session' # Prevent collision with code-server
    
    # Force HTTPS for OAuth in production (Render uses proxies)
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Allow OAuth over HTTP internally
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'   # Ignore scope order changes from GitHub
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Database Flask-SQLAlchemy
    # Check for DATABASE_URL or NEON_BRIDGE_DATABASE_URL
    db_url = os.environ.get("DATABASE_URL") or os.environ.get("NEON_BRIDGE_DATABASE_URL") or "sqlite:///users.db"
    
    # Fix for generic Postgres URLs in SQLAlchemy (postgres:// -> postgresql://)
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Session Security Config
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['REMEMBER_COOKIE_SECURE'] = True
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    
    db.init_app(app)
    
    # Initialize SINGULARITY CORE (Gravity Core v3)
    from core.gravity_core import gravity_core
    gravity_core.init_app(app)
    gravity_core.start_autonomy()
    
    # Initialize our custom DB Manager for AI Service/Constructor
    init_database()
    
    # GitHub Auth setup
    from backend.replit_auth import setup_github_auth
    setup_github_auth(app)
    
    from backend.api.git_routes import git_bp
    
    app.register_blueprint(ai_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(github_api_bp)
    app.register_blueprint(automation_bp)
    app.register_blueprint(terminal_bp)
    app.register_blueprint(repo_mgr_bp)
    app.register_blueprint(preview_bp)
    app.register_blueprint(extension_bp)
    app.register_blueprint(ide_bp)
    app.register_blueprint(github_sync_bp)
    app.register_blueprint(git_bp)
    app.register_blueprint(workspace_bp)
    
    @app.before_request
    def make_session_permanent():
        session.permanent = True

    with app.app_context():
        # Log which database we are actually using (masking password)
        db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
        safe_uri = db_uri.split("@")[-1] if "@" in db_uri else "sqlite_local"
        logging.info(f"Connecting to database: ...@{safe_uri}")
        
        try:
            db.create_all()
            logging.info("Database tables verified/created")
            
            # Manual Migration: Add sync status columns if they don't exist
            # SQLite doesn't support 'IF NOT EXISTS' for ADD COLUMN in older versions, 
            # but Neon (Postgres) does. We'll use a generic approach or check dialect.
            from sqlalchemy import text
            if "postgresql" in db_uri:
                db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS sync_status VARCHAR(20) DEFAULT 'none'"))
                db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS current_sync_repo VARCHAR(255)"))
                db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS sync_error TEXT"))
                db.session.commit()
                logging.info("PostgreSQL schema migration completed.")
        except Exception as e:
            logging.warning(f"Database table creation/migration skipped: {e}")
            db.session.rollback()
    
    # CORS Configuration - Restringido a tu web principal
    CORS(app, resources={r"/*": {
        "origins": ["https://bunk3r-w3b.onrender.com"],
        "methods": ["GET", "POST", "OPTIONS", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "supports_credentials": True
    }})

    @app.after_request
    def add_header(response):
        # Cache control
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        # Permitir Embedding (Iframe) - RESTRINGIDO A TU DOMINIO
        # Usamos Content-Security-Policy frame-ancestors en lugar del obsoleto X-Frame-Options
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self' https://bunk3r-w3b.onrender.com; default-src * 'unsafe-inline' 'unsafe-eval'; script-src * 'unsafe-inline' 'unsafe-eval'; style-src * 'unsafe-inline'; img-src * data: 'unsafe-inline'; connect-src *;"
        response.headers['Access-Control-Allow-Origin'] = "https://bunk3r-w3b.onrender.com"
        response.headers['Access-Control-Allow-Methods'] = "GET, POST, OPTIONS, PUT, DELETE"
        response.headers['Access-Control-Allow-Headers'] = "Content-Type, Authorization, X-Requested-With"
        response.headers['Access-Control-Allow-Credentials'] = "true"
        
        return response

    @app.context_processor
    def inject_user():
        from flask_login import current_user
        return dict(current_user=current_user)

    @app.route('/reset-session')
    def reset_session():
        from flask import session, redirect, url_for, make_response
        from flask_login import logout_user
        session.clear()
        logout_user()
        response = make_response(redirect(url_for('index')))
        response.delete_cookie('bunk3r_ready', path='/')
        return response

    @app.route('/')
    def index():
        from flask_login import current_user
        from flask import make_response, redirect, url_for, request
        import logging
        
        logging.info(f"Index access. User authenticated: {current_user.is_authenticated}")
        logging.info(f"Cookies received: {list(request.cookies.keys())}")
        
        if not current_user.is_authenticated:
            logging.info("User not authenticated, rendering landing page")
            return render_template('landing.html')
        
        # If authenticated, check sync status
        from backend.api.workspace_manager import workspace_mgr
        user_id = str(current_user.id)
        logging.info(f"User {user_id} authenticated. Checking sync status.")
        
        logging.info(f"Sync Status for {user_id}: {current_user.sync_status}")
        
        # If syncing is in progress, show sync page
        if current_user.sync_status == "syncing":
            return redirect('/syncing')
        
        # If not started, start sync internally
        if not current_user.sync_status or current_user.sync_status == "none":
             from flask import session, current_app
             token = session.get('github_token')
             if token:
                 workspace_mgr.sync_user_repos(user_id, token, current_app._get_current_object())
                 return redirect('/syncing')
             else:
                 # Token missing, force re-login
                 return redirect(url_for('github.login'))

        # If completed, serve IDE directly and set the "Bypass" cookie for Nginx
        if current_user.sync_status == "completed":
            import os
            workspace_path = workspace_mgr.get_user_workspace(user_id)
            
            # 1. Stale Check: If folder is empty, re-sync.
            if not os.path.exists(workspace_path) or not os.listdir(workspace_path):
                logging.info(f"Workspace for {user_id} is empty despite 'completed' status. Re-syncing.")
                from flask import session, current_app
                token = session.get('github_token')
                if token:
                    workspace_mgr.sync_user_repos(user_id, token, current_app._get_current_object())
                    return redirect('/syncing')
                else:
                    logging.warning(f"No GitHub token in session for {user_id}. Forcing login.")
                    return redirect(url_for('github.login'))

            # 2. Folder Redirection: Ensure the IDE opens the correct user folder
            if not request.args.get('folder'):
                logging.info(f"Redirecting user {user_id} to folder-specific IDE URL.")
                response = make_response(redirect(f"/?folder=/workspace/{current_user.id}"))
                response.set_cookie('bunk3r_ready', '1', max_age=3600*24, path='/', samesite='Lax')
                return response

            # 3. Serve IDE: Fallback if Nginx haven't bypassed yet
            logging.info(f"Sync complete for {user_id}. Serving IDE via X-Accel-Redirect.")
            response = make_response("")
            response.headers['X-Accel-Redirect'] = '/@ide'
            response.set_cookie('bunk3r_ready', '1', max_age=3600*24, path='/', samesite='Lax')
            return response
            
        # If not authenticated, or sync not started/completed, render landing page
        return render_template('landing.html')
    
    @app.route('/syncing')
    def syncing():
        return render_template('sync.html')

    @app.route('/ide')
    def ide():
        """Premium IDE interface"""
        # This will be proxied or handled after sync
        return render_template('ide.html')
    
    @app.route('/quick-login', methods=['POST'])
    def quick_login():
        """Quick login without GitHub OAuth"""
        from flask_login import login_user
        from backend.models import User
        import uuid
        
        # Try to get existing demo user
        user = User.query.filter_by(email="demo@bunkr.local").first()
        
        if not user:
            # Create new demo user if doesn't exist
            demo_user_id = "demo_" + str(uuid.uuid4())[:8]
            user = User()
            user.id = demo_user_id
            user.first_name = "Usuario"
            user.last_name = "Demo"
            user.email = "demo@bunkr.local"
            user.profile_image_url = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23F0B90B'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3C/svg%3E"
            db.session.add(user)
            db.session.commit()
        
        session.permanent = True
        login_user(user, remember=True)
        return jsonify({"success": True, "user_id": user.id})
    
    @app.route('/preview/<session_id>')
    def serve_preview(session_id):
        """Serve generated HTML preview"""
        from core.legacy_v1_archive.live_preview import live_preview
        
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
    
    @app.route('/api/auth/check')
    def auth_check():
        from flask_login import current_user
        if current_user.is_authenticated:
            return "OK", 200
        else:
            return "Unauthorized", 401
    
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
        from core.ai_service import get_ai_service
        
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
    
    @app.route('/api/ai-providers', methods=['GET'])
    def ai_providers():
        """Get list of available AI providers"""
        from core.ai_service import get_ai_service
        
        try:
            ai_service = get_ai_service(None)
            if ai_service:
                providers = ai_service.get_available_providers()
                return jsonify({
                    'success': True,
                    'providers': providers,
                    'count': len(providers),
                    'configured': {
                        'openai': bool(os.environ.get('OPENAI_API_KEY')),
                        'gemini': bool(os.environ.get('GEMINI_API_KEY')),
                        'baidu': bool(os.environ.get('BAIDU_API_KEY')),
                        'groq': bool(os.environ.get('GROQ_API_KEY')),
                        'deepseek': bool(os.environ.get('DEEPSEEK_API_KEY')),
                        'cerebras': bool(os.environ.get('CEREBRAS_API_KEY'))
                    }
                })
            else:
                return jsonify({'success': False, 'error': 'AI service not available'}), 503
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return app

def init_database(database_url=None):
    """Inicializar conexión a base de datos"""
    from backend.api.routes import set_db_manager
    
    if database_url is None:
        database_url = os.getenv('DATABASE_URL')
    
    # Intento con PostgreSQL si hay URL
    if database_url:
        try:
            import psycopg2
            from psycopg2 import pool
            
            class PostgresDBManager:
                def __init__(self, url):
                    self.pool = pool.SimpleConnectionPool(1, 10, url)
                
                def get_connection(self):
                    return self.pool.getconn()
                
                def release_connection(self, conn):
                    self.pool.putconn(conn)
            
            db_manager = PostgresDBManager(database_url)
            set_db_manager(db_manager)
            logger.info("Database connection established (PostgreSQL)")
            return db_manager
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}. Falling back to SQLite.")

    # Fallback o default: SQLite (Nuestra propia base de datos)
    try:
        from core.legacy_v1_archive.database.manager import manager as sqlite_manager
        
        # Necesitamos que el manager tenga get_connection para ser compatible con el código que espera pools
        if not hasattr(sqlite_manager, 'get_connection'):
            # El manager original tiene _get_connection(path), vamos a envolverlo
            class SQLiteAdapter:
                def __init__(self, mgr):
                    self.mgr = mgr
                def get_connection(self):
                    # Retorna la conexión central por defecto
                    return self.mgr._get_connection(self.mgr.central_db_path)
                def release_connection(self, conn):
                    pass # SQLite no suele usar pools de la misma forma aquí
            
            adapted_manager = SQLiteAdapter(sqlite_manager)
            set_db_manager(adapted_manager)
        else:
            set_db_manager(sqlite_manager)
            
        logger.info("Database connection established (internal SQLite)")
        return sqlite_manager
    except Exception as e:
        logger.error(f"Critical Error: Failed to initialize any database: {e}")
        return None

# Gunicorn entrypoint (WSGI)
app = create_app()


def main():
    """Punto de entrada principal"""
    config = get_config()
    
    logger.info("=" * 50)
    logger.info("BUNK3R_IA - Sistema de Inteligencia Artificial")
    logger.info("=" * 50)
    
    init_database()
    
    app = create_app(config)
    
    host = config.HOST
    # Priorizar el puerto de la variable de entorno para Render
    port = int(os.environ.get("PORT", config.PORT))
    debug = config.DEBUG
    
    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()

