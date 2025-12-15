"""
BUNK3R_IA - Configuración del sistema de IA
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuración principal de BUNK3R_IA"""
    
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('BUNK3R_IA_HOST', '0.0.0.0')
    PORT = int(os.getenv('BUNK3R_IA_PORT', 5001))
    
    DATABASE_URL = os.getenv('DATABASE_URL', '')
    
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    HF_TOKEN = os.getenv('HF_TOKEN', '')
    CEREBRAS_API_KEY = os.getenv('CEREBRAS_API_KEY', '')
    
    PROJECT_ROOT = os.getenv('BUNK3R_IA_PROJECT_ROOT', os.getcwd())
    AI_GENERATED_DIR = os.path.join(PROJECT_ROOT, 'ai_generated')
    CHECKPOINTS_DIR = os.path.join(PROJECT_ROOT, '.ai_checkpoints')
    
    MAX_FILE_SIZE = 10 * 1024 * 1024
    MAX_READ_LINES = 5000
    COMMAND_TIMEOUT = 60
    
    BLOCKED_PATHS = [
        '.env', '.git', '__pycache__', 'node_modules',
        '.replit', '.config', '.cache', '.local',
        'venv', '.venv', 'env'
    ]
    
    BLOCKED_EXTENSIONS = ['.pyc', '.pyo', '.so', '.dll', '.exe', '.bin']
    
    WHITELISTED_COMMANDS = [
        'pip', 'npm', 'yarn', 'pnpm', 'node', 'python', 'python3',
        'git', 'ls', 'cat', 'echo', 'mkdir', 'touch', 'rm', 'cp', 'mv',
        'npx', 'cargo', 'go', 'rustc', 'tsc', 'prettier', 'eslint'
    ]

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Obtener configuración según el entorno"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])()
