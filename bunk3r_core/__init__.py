# BUNK3R IA Core - Motor de Singularidad Unificado (Gravity v3)
import sys
import importlib

# --- PUENTE DE COMPATIBILIDAD GHOST (Gravity v2 -> v3) ---
# Redirigir módulos antiguos internos al archivo para no romper imports absolutos.
legacy_modules = [
    'database', 'workers', 'automation', 'gravity', 'ai_constructor', 
    'ai_core_engine', 'ai_flow_logger', 'ai_project_context', 'ai_toolkit',
    'web_search_service', 'live_preview', 'context_manager'
]

for mod in legacy_modules:
    old_path = f"bunk3r_core.{mod}"
    new_path = f"bunk3r_core.legacy_v1_archive.{mod}"
    if old_path not in sys.modules:
        try:
            # Alias dinámico en el registro de módulos de Python
            sys.modules[old_path] = importlib.import_module(new_path)
        except Exception:
            pass

# LOS 3 NÚCLEOS MAESTROS
from .singularity import singularity, Singularity
from .nervous_system import nervous_system, NervousSystem
from .gravity_core import gravity_core, GravityCore

# Interfaz de Servicio
from .ai_service import AIService, get_ai_service

__all__ = [
    'singularity', 'Singularity',
    'nervous_system', 'NervousSystem',
    'gravity_core', 'GravityCore',
    'AIService', 'get_ai_service'
]
