# BUNK3R IA Core - Motor principal de IA

# Servicios principales
from .ai_service import AIService, get_ai_service
from .ai_constructor import AIConstructorService
from .ai_core_engine import AICoreOrchestrator, AIDecisionEngine, IntentType, Intent
from .ai_flow_logger import AIFlowLogger, flow_logger
from .ai_project_context import AIProjectContext
from .ai_toolkit import AIFileToolkit, AICommandExecutor, AIErrorDetector, AIProjectAnalyzer

# Nuevos componentes (34.3 - 34.19)
from .output_verifier import OutputVerifier, output_verifier, verify_code, quick_validate as quick_validate_code
from .clarification_manager import ClarificationManager, clarification_manager, needs_clarification, generate_clarification_questions
from .plan_presenter import PlanPresenter, plan_presenter, create_plan, format_plan
from .smart_retry import SmartRetrySystem, smart_retry, RetryConfig, RetryStrategy
from .pre_execution_validator import PreExecutionValidator, pre_execution_validator, validate_action

__all__ = [
    # Servicios principales
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
    
    # Nuevos componentes
    'OutputVerifier',
    'output_verifier',
    'verify_code',
    'quick_validate_code',
    'ClarificationManager',
    'clarification_manager',
    'needs_clarification',
    'generate_clarification_questions',
    'PlanPresenter',
    'plan_presenter',
    'create_plan',
    'format_plan',
    'SmartRetrySystem',
    'smart_retry',
    'RetryConfig',
    'RetryStrategy',
    'PreExecutionValidator',
    'pre_execution_validator',
    'validate_action',
]
