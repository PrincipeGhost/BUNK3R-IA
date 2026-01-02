from datetime import datetime
from BUNK3R_IA.config import get_config
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class OAuth(db.Model):
    __tablename__ = 'flask_dance_oauth'
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    token = db.Column(db.JSON, nullable=False)
    
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)

class GlobalSetting(db.Model):
    __tablename__ = 'global_settings'
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get(cls, key, default=None):
        setting = cls.query.get(key)
        return setting.value if setting else default

    @classmethod
    def set(cls, key, value):
        setting = cls.query.get(key)
        if not setting:
            setting = cls(key=key)
            db.session.add(setting)
        setting.value = str(value)
        db.session.commit()

# --- GRAVITY CORE MODELS ---

class SolutionKnowledge(db.Model):
    """Capa 1: Verdad verificada - Soluciones probadas y estables."""
    __tablename__ = 'ai_solution_knowledge'
    id = db.Column(db.Integer, primary_key=True)
    problem_hash = db.Column(db.String(64), unique=True, nullable=False)
    problem_desc = db.Column(db.Text, nullable=False)
    solution_code = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(255))
    status = db.Column(db.String(20), default='verified') # verified, tentative, rejected
    success_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)

class BugMemory(db.Model):
    """Memoria de errores históricos para evitar recurrencia."""
    __tablename__ = 'ai_bug_memory'
    id = db.Column(db.Integer, primary_key=True)
    error_pattern = db.Column(db.String(255), unique=True, nullable=False)
    error_context = db.Column(db.Text)
    fix_approach = db.Column(db.Text)
    occurrence_count = db.Column(db.Integer, default=1)
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

class ArchitectureLog(db.Model):
    """Registro de decisiones arquitectónicas y su por qué."""
    __tablename__ = 'ai_architecture_log'
    id = db.Column(db.Integer, primary_key=True)
    decision_title = db.Column(db.String(255), nullable=False)
    reasoning = db.Column(db.Text, nullable=False)
    alternatives = db.Column(db.Text)
    impact_level = db.Column(db.String(20), default='medium')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ModelBenchmark(db.Model):
    """Registro de rendimiento real de modelos."""
    __tablename__ = 'ai_model_benchmarks'
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), nullable=False)
    task_type = db.Column(db.String(50))
    latency_ms = db.Column(db.Integer)
    success = db.Column(db.Boolean, default=True)
    quality_score = db.Column(db.Integer) # 1-10 (opcional)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class UserPreferenceModel(db.Model):
    """Preferencias implícitas detectadas por el comportamiento del usuario."""
    __tablename__ = 'ai_user_preferences'
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.JSON)
    confidence = db.Column(db.Float, default=0.5)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class ProjectGraph(db.Model):
    """Mapeo del grafo de dependencias del proyecto."""
    __tablename__ = 'ai_project_graph'
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(255), nullable=False)
    imports = db.Column(db.JSON) # Lista de archivos que importa
    exports = db.Column(db.JSON) # Funciones/Clases que exporta
    last_scanned = db.Column(db.DateTime, default=datetime.utcnow)

class GitHubRepo(db.Model):
    """Repositorios de GitHub sincronizados del usuario."""
    __tablename__ = 'github_repos'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey(User.id), nullable=False)
    repo_name = db.Column(db.String(255), nullable=False)  # ej: "PrincipeGhost/tracking_correos"
    local_path = db.Column(db.String(500), nullable=False)
    last_synced = db.Column(db.DateTime, nullable=True)
    sync_status = db.Column(db.String(20), default='pending')  # pending, syncing, ready, error
    commit_hash = db.Column(db.String(40), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship(User, backref='github_repos')
    
    __table_args__ = (UniqueConstraint('user_id', 'repo_name', name='uq_user_repo'),)
