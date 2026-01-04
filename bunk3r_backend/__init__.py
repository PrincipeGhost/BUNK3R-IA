"""
BUNK3R_IA - Sistema de Inteligencia Artificial Unificado (SINGULARITY)
=====================================================================

Módulo principal rediseñado bajo la Arquitectura de Singularidad.

NÚCLEOS MAESTROS:
- Singularity: El Alma (Racionamiento y Planificación)
- NervousSystem: El Cuerpo (Ejecución de herramientas y Sandbox)
- GravityCore: El Corazón (Memoria, Monitoreo y Autonomía)

Uso básico:
    from BUNK3R_IA import singularity, nervous_system, gravity_core
"""

__version__ = '3.0.0 (Singularity)'
__author__ = 'BUNK3R Team'

from bunk3r_core import (
    singularity,
    Singularity,
    nervous_system,
    NervousSystem,
    gravity_core,
    GravityCore,
    AIService,
    get_ai_service
)

__all__ = [
    'singularity',
    'Singularity',
    'nervous_system',
    'NervousSystem',
    'gravity_core',
    'GravityCore',
    'AIService',
    'get_ai_service',
]
