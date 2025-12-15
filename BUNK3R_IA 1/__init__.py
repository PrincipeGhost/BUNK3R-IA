"""
BUNK3R_IA - Sistema de Inteligencia Artificial Avanzado
========================================================

Módulo principal que contiene toda la lógica de IA para BUNK3R.

Componentes principales:
- AIService: Servicio multi-proveedor de chat con fallback automático
- AIConstructorService: Constructor de código con arquitectura de 8 fases
- AICoreOrchestrator: Orquestador de decisiones y workflows
- AIToolkit: Herramientas para manipulación de archivos y comandos
- AIFlowLogger: Sistema de logging para debug
- AIProjectContext: Contexto persistente de proyecto

Uso básico:
    from BUNK3R_IA.core import AIService, get_ai_service
    from BUNK3R_IA.core import AIConstructorService
    from BUNK3R_IA.core import AICoreOrchestrator

Para ejecutar como servidor independiente:
    python -m BUNK3R_IA.main

Versión: 1.0.0
"""

__version__ = '1.0.0'
__author__ = 'BUNK3R Team'

from BUNK3R_IA.core import (
    AIService,
    get_ai_service,
    AIConstructorService,
    AICoreOrchestrator,
    AIDecisionEngine,
    IntentType,
    Intent,
    AIFlowLogger,
    flow_logger,
    AIProjectContext,
    AIFileToolkit,
    AICommandExecutor,
    AIErrorDetector,
    AIProjectAnalyzer
)

__all__ = [
    'AIService',
    'get_ai_service',
    'AIConstructorService',
    'AICoreOrchestrator',
    'AIDecisionEngine',
    'IntentType',
    'Intent',
    'AIFlowLogger',
    'flow_logger',
    'AIProjectContext',
    'AIFileToolkit',
    'AICommandExecutor',
    'AIErrorDetector',
    'AIProjectAnalyzer',
]
