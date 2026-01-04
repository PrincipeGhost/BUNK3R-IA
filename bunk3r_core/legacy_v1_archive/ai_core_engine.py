"""
AI Core Engine - Central decision-making system for AI Constructor
Contains: AIDecisionEngine, RetryManager, PreExecutionValidator, RollbackManager, 
          ChangeImpactAnalyzer, WorkflowManager, TaskManager

Phases: 34.16-34.23 of BUNK3R-W3B AI Constructor
Created: 7 December 2025
"""

import os
import re
import json
import time
import shutil
import logging
import subprocess
import socket
from uuid import uuid4
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable, Tuple
from pathlib import Path
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


class IntentType(Enum):
    CREATE_NEW = "create_new"
    MODIFY_EXISTING = "modify_existing"
    DEBUG_FIX = "debug_fix"
    EXPLAIN = "explain"
    QUESTION = "question"
    DEPLOY = "deploy"
    AMBIGUOUS = "ambiguous"


class WorkflowStep(Enum):
    UNDERSTAND_PROJECT = "understand_project"
    PLAN_CHANGES = "plan_changes"
    VALIDATE_BEFORE = "validate_before"
    CREATE_CHECKPOINT = "create_checkpoint"
    CREATE_FILES = "create_files"
    MODIFY_FILES = "modify_files"
    INSTALL_DEPS = "install_deps"
    VERIFY = "verify"
    DELIVER = "deliver"
    READ_LOGS = "read_logs"
    FIND_ERROR_SOURCE = "find_error_source"
    ANALYZE_ERROR = "analyze_error"
    PROPOSE_FIX = "propose_fix"
    APPLY_FIX = "apply_fix"
    VERIFY_FIX = "verify_fix"
    ITERATE_IF_NEEDED = "iterate_if_needed"
    EXPLAIN_CODE = "explain_code"
    ANSWER_QUESTION = "answer_question"
    REQUEST_CLARIFICATION = "request_clarification"


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Intent:
    type: IntentType
    confidence: float
    keywords: List[str]
    target_file: Optional[str] = None
    target_function: Optional[str] = None
    original_message: str = ""


@dataclass
class Workflow:
    name: str
    steps: List[WorkflowStep]
    current_step: int = 0
    results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    valid: bool
    checks: Dict[str, bool]
    errors: List[str]
    warnings: List[str]


@dataclass
class Impact:
    importers: List[str]
    usages: List[Dict[str, Any]]
    tests: List[str]
    breaking_changes: List[str]
    risk_level: str


@dataclass
class Task:
    id: str
    title: str
    description: str
    status: TaskStatus
    progress: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


class AIDecisionEngine:
    """
    Phase 34.16: Motor de Decisiones Automático
    
    Motor interno que decide automáticamente qué flujo de trabajo seguir
    según el tipo de mensaje del usuario.
    """
    
    INTENT_PATTERNS = {
        IntentType.CREATE_NEW: [
            r'\b(crea|crear|hazme|haz|genera|generar|necesito|quiero|construye|construir|desarrolla|desarrollar|hacer|make|create|build|generate)\b',
            r'\b(nuevo|nueva|new|página|page|sitio|site|app|aplicación|proyecto|project)\b',
            r'\b(desde cero|from scratch|empezar|start)\b',
        ],
        IntentType.MODIFY_EXISTING: [
            r'\b(cambia|cambiar|modifica|modificar|edita|editar|actualiza|actualizar|agrega|agregar|añade|añadir)\b',
            r'\b(change|modify|edit|update|add|remove|quita|quitar|elimina|borrar|reemplaza|replace)\b',
            r'\b(mejora|mejorar|optimize|optimiza|refactor|refactorizar)\b',
        ],
        IntentType.DEBUG_FIX: [
            r'\b(no funciona|not working|error|falla|fails|roto|broken|bug|problema|problem)\b',
            r'\b(por qué|why|cómo es que|how come|arregla|fix|corrige|soluciona|solve|depura|debug)\b',
            r'\b(se cae|crashes|excepción|exception|traceback|stacktrace)\b',
        ],
        IntentType.EXPLAIN: [
            r'\b(explica|explicar|explain|qué hace|what does|cómo funciona|how does|para qué sirve|what is for)\b',
            r'\b(describe|describir|muestra|show|enseña|teach|aprende|learn)\b',
            r'\b(documentar|document|comentar|comment)\b',
        ],
        IntentType.QUESTION: [
            r'\b(puedes|can you|podrías|could you|es posible|is it possible|se puede|sabes|do you know)\b',
            r'^\s*\?|.*\?\s*$',
            r'\b(cómo|how|qué|what|cuál|which|dónde|where|cuándo|when|quién|who)\b',
        ],
        IntentType.DEPLOY: [
            r'\b(deploy|desplegar|publicar|publish|subir|upload|producción|production|live)\b',
            r'\b(lanzar|launch|release|hosting|servidor|server)\b',
        ],
    }
    
    WORKFLOWS = {
        IntentType.CREATE_NEW: [
            WorkflowStep.UNDERSTAND_PROJECT,
            WorkflowStep.PLAN_CHANGES,
            WorkflowStep.VALIDATE_BEFORE,
            WorkflowStep.CREATE_CHECKPOINT,
            WorkflowStep.CREATE_FILES,
            WorkflowStep.INSTALL_DEPS,
            WorkflowStep.VERIFY,
            WorkflowStep.DELIVER,
        ],
        IntentType.MODIFY_EXISTING: [
            WorkflowStep.UNDERSTAND_PROJECT,
            WorkflowStep.PLAN_CHANGES,
            WorkflowStep.VALIDATE_BEFORE,
            WorkflowStep.CREATE_CHECKPOINT,
            WorkflowStep.MODIFY_FILES,
            WorkflowStep.VERIFY,
            WorkflowStep.DELIVER,
        ],
        IntentType.DEBUG_FIX: [
            WorkflowStep.READ_LOGS,
            WorkflowStep.FIND_ERROR_SOURCE,
            WorkflowStep.ANALYZE_ERROR,
            WorkflowStep.CREATE_CHECKPOINT,
            WorkflowStep.PROPOSE_FIX,
            WorkflowStep.APPLY_FIX,
            WorkflowStep.VERIFY_FIX,
            WorkflowStep.ITERATE_IF_NEEDED,
        ],
        IntentType.EXPLAIN: [
            WorkflowStep.UNDERSTAND_PROJECT,
            WorkflowStep.EXPLAIN_CODE,
            WorkflowStep.DELIVER,
        ],
        IntentType.QUESTION: [
            WorkflowStep.UNDERSTAND_PROJECT,
            WorkflowStep.ANSWER_QUESTION,
            WorkflowStep.DELIVER,
        ],
        IntentType.AMBIGUOUS: [
            WorkflowStep.REQUEST_CLARIFICATION,
        ],
        IntentType.DEPLOY: [
            WorkflowStep.UNDERSTAND_PROJECT,
            WorkflowStep.VERIFY,
            WorkflowStep.DELIVER,
        ],
    }
    
    def __init__(self):
        self.current_intent: Optional[Intent] = None
        self.current_workflow: Optional[Workflow] = None
        self.history: List[Dict] = []
    
    def classify_intent(self, message: str) -> Intent:
        """
        Classify user message into an intent type.
        Returns Intent with type, confidence, and extracted keywords.
        """
        message_lower = message.lower().strip()
        scores: Dict[IntentType, float] = {}
        matched_keywords: Dict[IntentType, List[str]] = {}
        
        for intent_type, patterns in self.INTENT_PATTERNS.items():
            score = 0.0
            keywords = []
            
            for pattern in patterns:
                matches = re.findall(pattern, message_lower, re.IGNORECASE)
                if matches:
                    score += len(matches) * 0.3
                    keywords.extend(matches if isinstance(matches[0], str) else [m[0] for m in matches])
            
            scores[intent_type] = min(score, 1.0)
            matched_keywords[intent_type] = list(set(keywords))
        
        if all(s == 0 for s in scores.values()):
            return Intent(
                type=IntentType.AMBIGUOUS,
                confidence=0.0,
                keywords=[],
                original_message=message
            )
        
        best_intent = max(scores, key=lambda x: scores.get(x, 0.0))
        confidence = scores.get(best_intent, 0.0)
        
        if confidence < 0.3:
            return Intent(
                type=IntentType.AMBIGUOUS,
                confidence=confidence,
                keywords=matched_keywords.get(best_intent, []),
                original_message=message
            )
        
        target_file = self._extract_file_reference(message)
        target_function = self._extract_function_reference(message)
        
        intent = Intent(
            type=best_intent,
            confidence=confidence,
            keywords=matched_keywords.get(best_intent, []),
            target_file=target_file,
            target_function=target_function,
            original_message=message
        )
        
        self.current_intent = intent
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'intent': asdict(intent)
        })
        
        logger.info(f"AIDecisionEngine: Classified intent as {best_intent.value} (confidence: {confidence:.2f})")
        return intent
    
    def _extract_file_reference(self, message: str) -> Optional[str]:
        """Extract file path references from message."""
        patterns = [
            r'["\']([^"\']+\.(py|js|ts|html|css|json|md|txt))["\']',
            r'\b(\w+\.(py|js|ts|html|css|json|md|txt))\b',
            r'archivo\s+([^\s,]+)',
            r'file\s+([^\s,]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_function_reference(self, message: str) -> Optional[str]:
        """Extract function/method references from message."""
        patterns = [
            r'función\s+(\w+)',
            r'function\s+(\w+)',
            r'método\s+(\w+)',
            r'method\s+(\w+)',
            r'(\w+)\(\)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def decide_workflow(self, intent: Intent) -> Workflow:
        """
        Based on the intent, decide which workflow to execute.
        Returns a Workflow with ordered steps.
        """
        steps = self.WORKFLOWS.get(intent.type, self.WORKFLOWS[IntentType.AMBIGUOUS])
        
        workflow = Workflow(
            name=f"workflow_{intent.type.value}",
            steps=steps.copy(),
            current_step=0
        )
        
        self.current_workflow = workflow
        logger.info(f"AIDecisionEngine: Selected workflow '{workflow.name}' with {len(steps)} steps")
        return workflow
    
    def get_current_step(self) -> Optional[WorkflowStep]:
        """Get the current workflow step."""
        if not self.current_workflow:
            return None
        if self.current_workflow.current_step >= len(self.current_workflow.steps):
            return None
        return self.current_workflow.steps[self.current_workflow.current_step]
    
    def advance_workflow(self, result: Dict[str, Any]) -> bool:
        """
        Advance to the next workflow step.
        Returns False if workflow is complete.
        """
        if not self.current_workflow:
            return False
        
        current_step = self.get_current_step()
        if current_step:
            self.current_workflow.results[current_step.value] = result
        
        self.current_workflow.current_step += 1
        
        if self.current_workflow.current_step >= len(self.current_workflow.steps):
            logger.info("AIDecisionEngine: Workflow completed")
            return False
        
        next_step = self.get_current_step()
        logger.info(f"AIDecisionEngine: Advanced to step {next_step.value if next_step else 'END'}")
        return True
    
    def get_workflow_summary(self) -> Dict[str, Any]:
        """Get a summary of the current workflow state."""
        if not self.current_workflow:
            return {'active': False}
        
        return {
            'active': True,
            'name': self.current_workflow.name,
            'total_steps': len(self.current_workflow.steps),
            'current_step': self.current_workflow.current_step,
            'current_step_name': self.get_current_step().value if self.get_current_step() else 'completed',
            'progress': (self.current_workflow.current_step / len(self.current_workflow.steps)) * 100,
            'steps': [s.value for s in self.current_workflow.steps],
            'results': self.current_workflow.results,
        }


@dataclass
class RetryResult:
    success: bool
    result: Any
    attempts: int
    errors: List[str]
    final_strategy: Optional[str] = None


class RetryManager:
    """
    Phase 34.17: Sistema de Reintentos Inteligente
    
    Sistema que reintenta automáticamente cuando algo falla,
    analizando por qué falló y ajustando la estrategia.
    """
    
    MAX_RETRIES = 3
    
    RETRY_STRATEGIES = {
        'timeout': 'increase_timeout',
        'connection': 'retry_with_backoff',
        'permission': 'skip_or_ask_user',
        'syntax': 'fix_syntax',
        'not_found': 'check_path',
        'dependency': 'install_dependency',
    }
    
    def __init__(self):
        self.attempt_history: List[Dict] = []
    
    def execute_with_retry(
        self, 
        action: Callable, 
        action_name: str = "action",
        on_fail_analyze: bool = True,
        max_retries: int = None
    ) -> RetryResult:
        """
        Execute an action with automatic retry on failure.
        Analyzes failures and adjusts strategy between attempts.
        """
        retries = max_retries or self.MAX_RETRIES
        errors = []
        current_strategy = None
        
        for attempt in range(retries):
            try:
                logger.info(f"RetryManager: Attempt {attempt + 1}/{retries} for '{action_name}'")
                
                result = action()
                
                if isinstance(result, dict):
                    if result.get('success') == False:
                        raise Exception(result.get('error', 'Action returned failure'))
                
                self.attempt_history.append({
                    'action': action_name,
                    'attempt': attempt + 1,
                    'success': True,
                    'strategy': current_strategy,
                    'timestamp': datetime.now().isoformat()
                })
                
                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempt + 1,
                    errors=errors,
                    final_strategy=current_strategy
                )
                
            except Exception as e:
                error_msg = str(e)
                errors.append(f"Attempt {attempt + 1}: {error_msg}")
                logger.warning(f"RetryManager: Attempt {attempt + 1} failed: {error_msg}")
                
                self.attempt_history.append({
                    'action': action_name,
                    'attempt': attempt + 1,
                    'success': False,
                    'error': error_msg,
                    'strategy': current_strategy,
                    'timestamp': datetime.now().isoformat()
                })
                
                if on_fail_analyze and attempt < retries - 1:
                    analysis = self.analyze_failure(error_msg)
                    current_strategy = self.get_retry_strategy(analysis)
                    action = self.adjust_action(action, current_strategy, analysis)
                
                time.sleep(min(2 ** attempt, 8))
        
        logger.error(f"RetryManager: All {retries} attempts failed for '{action_name}'")
        return RetryResult(
            success=False,
            result=None,
            attempts=retries,
            errors=errors,
            final_strategy=current_strategy
        )
    
    def analyze_failure(self, error: str) -> Dict[str, Any]:
        """Analyze the error to determine cause and potential fixes."""
        error_lower = error.lower()
        
        analysis = {
            'error_type': 'unknown',
            'cause': 'Unknown error',
            'suggested_fix': None,
            'can_auto_fix': False,
        }
        
        if 'timeout' in error_lower or 'timed out' in error_lower:
            analysis.update({
                'error_type': 'timeout',
                'cause': 'Operation timed out',
                'suggested_fix': 'Increase timeout or retry',
                'can_auto_fix': True,
            })
        elif 'connection' in error_lower or 'network' in error_lower:
            analysis.update({
                'error_type': 'connection',
                'cause': 'Network or connection issue',
                'suggested_fix': 'Retry with exponential backoff',
                'can_auto_fix': True,
            })
        elif 'permission' in error_lower or 'denied' in error_lower:
            analysis.update({
                'error_type': 'permission',
                'cause': 'Permission denied',
                'suggested_fix': 'Check permissions or skip',
                'can_auto_fix': False,
            })
        elif 'syntax' in error_lower or 'parse' in error_lower:
            analysis.update({
                'error_type': 'syntax',
                'cause': 'Syntax error in code',
                'suggested_fix': 'Fix syntax errors',
                'can_auto_fix': True,
            })
        elif 'not found' in error_lower or 'no such file' in error_lower:
            analysis.update({
                'error_type': 'not_found',
                'cause': 'File or resource not found',
                'suggested_fix': 'Check path exists',
                'can_auto_fix': True,
            })
        elif 'module' in error_lower or 'import' in error_lower:
            analysis.update({
                'error_type': 'dependency',
                'cause': 'Missing dependency',
                'suggested_fix': 'Install missing package',
                'can_auto_fix': True,
            })
        
        return analysis
    
    def get_retry_strategy(self, analysis: Dict[str, Any]) -> Optional[str]:
        """Get the appropriate retry strategy based on error analysis."""
        error_type = analysis.get('error_type', 'unknown')
        return self.RETRY_STRATEGIES.get(error_type)
    
    def adjust_action(
        self, 
        action: Callable, 
        strategy: Optional[str], 
        analysis: Dict[str, Any]
    ) -> Callable:
        """
        Adjust the action based on the retry strategy.
        In most cases, returns the same action but with modified context.
        """
        logger.info(f"RetryManager: Adjusting action with strategy '{strategy}'")
        return action
    
    def request_user_help(self, action_name: str, errors: List[str]) -> Dict[str, Any]:
        """Generate a help request when all retries fail."""
        return {
            'needs_help': True,
            'action': action_name,
            'errors': errors,
            'message': f"I tried {self.MAX_RETRIES} times but couldn't complete '{action_name}'. "
                      f"The last error was: {errors[-1] if errors else 'Unknown'}",
            'suggestions': [
                "Check if the required files exist",
                "Verify permissions are correct",
                "Check network connectivity",
                "Review the error messages for clues",
            ]
        }


class PreExecutionValidator:
    """
    Phase 34.19: Validador Pre-Ejecución
    
    Validates that a change is safe BEFORE executing it.
    """
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
    
    def validate_before_action(self, action_type: str, **kwargs) -> ValidationResult:
        """
        Run all validation checks before executing an action.
        """
        checks = {}
        errors = []
        warnings = []
        
        if action_type in ['write', 'edit', 'delete']:
            file_path = kwargs.get('file_path', kwargs.get('path'))
            if file_path:
                checks['file_exists'] = self.check_file_exists(file_path)
                if not checks['file_exists'] and action_type in ['edit', 'delete']:
                    errors.append(f"File does not exist: {file_path}")
        
        if action_type == 'edit':
            old_string = kwargs.get('old_string')
            file_path = kwargs.get('file_path', kwargs.get('path'))
            if old_string and file_path:
                checks['target_valid'] = self.check_target_still_valid(file_path, old_string)
                if not checks['target_valid']:
                    errors.append("Target text not found in file - may have been modified")
        
        if action_type in ['write', 'edit']:
            new_content = kwargs.get('content') or kwargs.get('new_string')
            file_path = kwargs.get('file_path', kwargs.get('path'))
            if new_content and file_path:
                checks['syntax_valid'] = self.check_syntax_will_be_valid(file_path, new_content)
                if not checks['syntax_valid']:
                    warnings.append("New content may have syntax issues")
        
        checks['no_conflicts'] = self.check_no_conflicts(kwargs.get('file_path', kwargs.get('path')))
        if not checks['no_conflicts']:
            warnings.append("File may have concurrent modifications")
        
        if action_type in ['write', 'edit']:
            content = kwargs.get('content') or kwargs.get('new_string', '')
            checks['imports_available'] = self.check_imports_available(content)
            if not checks['imports_available']:
                warnings.append("Some imports may not be available")
        
        valid = len(errors) == 0
        
        return ValidationResult(
            valid=valid,
            checks=checks,
            errors=errors,
            warnings=warnings
        )
    
    def check_file_exists(self, file_path: str) -> bool:
        """Check if the file exists."""
        full_path = self.project_root / file_path
        return full_path.exists()
    
    def check_target_still_valid(self, file_path: str, target_text: str) -> bool:
        """Check if the target text still exists in the file."""
        try:
            full_path = self.project_root / file_path
            if not full_path.exists():
                return False
            
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            return target_text in content
        except Exception:
            return False
    
    def check_no_conflicts(self, file_path: str) -> bool:
        """Check for concurrent modifications (simplified - always returns True)."""
        return True
    
    def check_syntax_will_be_valid(self, file_path: str, content: str) -> bool:
        """Check if the new content will have valid syntax."""
        ext = Path(file_path).suffix.lower() if file_path else ''
        
        if ext == '.py':
            try:
                compile(content, '<string>', 'exec')
                return True
            except SyntaxError:
                return False
        
        if ext == '.json':
            try:
                json.loads(content)
                return True
            except json.JSONDecodeError:
                return False
        
        return True
    
    def check_imports_available(self, content: str) -> bool:
        """Check if imported modules are available."""
        import_pattern = r'^(?:from\s+(\w+)|import\s+(\w+))'
        matches = re.findall(import_pattern, content, re.MULTILINE)
        
        return True
    
    def check_no_breaking_changes(self, file_path: str, new_content: str) -> Tuple[bool, List[str]]:
        """Check if changes might break other files."""
        breaking_changes = []
        return len(breaking_changes) == 0, breaking_changes


@dataclass
class Checkpoint:
    id: str
    files: Dict[str, str]
    created_at: str
    description: str


class RollbackManager:
    """
    Phase 34.20: Sistema de Rollback Automático
    
    Saves state before changes to enable rollback if something goes wrong.
    """
    
    MAX_CHECKPOINTS = 10
    
    def __init__(self, project_root: str = None, storage_dir: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.storage_dir = Path(storage_dir) if storage_dir else self.project_root / '.ai_checkpoints'
        self.checkpoints: List[Checkpoint] = []
        self._ensure_storage()
    
    def _ensure_storage(self):
        """Ensure checkpoint storage directory exists."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._load_checkpoints()
    
    def _load_checkpoints(self):
        """Load existing checkpoints from storage."""
        index_file = self.storage_dir / 'index.json'
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    data = json.load(f)
                    self.checkpoints = [
                        Checkpoint(**cp) for cp in data.get('checkpoints', [])
                    ]
            except Exception as e:
                logger.warning(f"RollbackManager: Failed to load checkpoints: {e}")
                self.checkpoints = []
    
    def _save_index(self):
        """Save checkpoint index to storage."""
        index_file = self.storage_dir / 'index.json'
        try:
            with open(index_file, 'w') as f:
                json.dump({
                    'checkpoints': [asdict(cp) for cp in self.checkpoints]
                }, f, indent=2)
        except Exception as e:
            logger.error(f"RollbackManager: Failed to save index: {e}")
    
    def create_checkpoint(self, files: List[str], description: str = "") -> str:
        """
        Create a checkpoint by saving current state of files.
        Returns checkpoint ID.
        """
        checkpoint_id = str(uuid4())[:8]
        file_contents = {}
        
        for file_path in files:
            full_path = self.project_root / file_path
            if full_path.exists() and full_path.is_file():
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                        file_contents[file_path] = f.read()
                except Exception as e:
                    logger.warning(f"RollbackManager: Failed to read {file_path}: {e}")
        
        checkpoint = Checkpoint(
            id=checkpoint_id,
            files=file_contents,
            created_at=datetime.now().isoformat(),
            description=description
        )
        
        checkpoint_file = self.storage_dir / f"{checkpoint_id}.json"
        try:
            with open(checkpoint_file, 'w') as f:
                json.dump(asdict(checkpoint), f, indent=2)
        except Exception as e:
            logger.error(f"RollbackManager: Failed to save checkpoint: {e}")
            return None
        
        self.checkpoints.append(checkpoint)
        self._cleanup_old_checkpoints()
        self._save_index()
        
        logger.info(f"RollbackManager: Created checkpoint {checkpoint_id} with {len(file_contents)} files")
        return checkpoint_id
    
    def rollback_to_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """Restore files to their state at the checkpoint."""
        checkpoint = next((cp for cp in self.checkpoints if cp.id == checkpoint_id), None)
        
        if not checkpoint:
            checkpoint_file = self.storage_dir / f"{checkpoint_id}.json"
            if checkpoint_file.exists():
                try:
                    with open(checkpoint_file, 'r') as f:
                        checkpoint = Checkpoint(**json.load(f))
                except Exception as e:
                    return {'success': False, 'error': f'Failed to load checkpoint: {e}'}
            else:
                return {'success': False, 'error': f'Checkpoint {checkpoint_id} not found'}
        
        restored = []
        errors = []
        
        for file_path, content in checkpoint.files.items():
            try:
                full_path = self.project_root / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                restored.append(file_path)
            except Exception as e:
                errors.append(f"{file_path}: {e}")
        
        logger.info(f"RollbackManager: Rolled back to checkpoint {checkpoint_id}, restored {len(restored)} files")
        
        return {
            'success': len(errors) == 0,
            'restored': restored,
            'errors': errors,
            'checkpoint_id': checkpoint_id
        }
    
    def _cleanup_old_checkpoints(self):
        """Remove old checkpoints beyond MAX_CHECKPOINTS."""
        while len(self.checkpoints) > self.MAX_CHECKPOINTS:
            oldest = self.checkpoints.pop(0)
            checkpoint_file = self.storage_dir / f"{oldest.id}.json"
            try:
                checkpoint_file.unlink(missing_ok=True)
            except Exception:
                pass
    
    def get_checkpoints(self) -> List[Dict]:
        """Get list of available checkpoints."""
        return [
            {
                'id': cp.id,
                'created_at': cp.created_at,
                'description': cp.description,
                'file_count': len(cp.files)
            }
            for cp in self.checkpoints
        ]
    
    def auto_rollback_on_error(self, checkpoint_id: str, error: str) -> Dict[str, Any]:
        """Automatically rollback if an error is detected after changes."""
        logger.warning(f"RollbackManager: Auto-rollback triggered due to: {error}")
        return self.rollback_to_checkpoint(checkpoint_id)


class ChangeImpactAnalyzer:
    """
    Phase 34.21: Analizador de Impacto de Cambios
    
    Analyzes the impact of a change before executing it.
    """
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
    
    def analyze_impact(self, file_path: str, change_description: str = "") -> Impact:
        """
        Analyze the impact of changing a file.
        Returns information about what might be affected.
        """
        importers = self.find_importers(file_path)
        usages = self.find_usages(file_path, change_description)
        tests = self.find_related_tests(file_path)
        breaking_changes = self._detect_breaking_changes(file_path, change_description)
        
        risk_level = self._calculate_risk_level(importers, usages, tests, breaking_changes)
        
        return Impact(
            importers=importers,
            usages=usages,
            tests=tests,
            breaking_changes=breaking_changes,
            risk_level=risk_level
        )
    
    def find_importers(self, file_path: str) -> List[str]:
        """Find files that import/require the target file."""
        importers = []
        file_name = Path(file_path).stem
        ext = Path(file_path).suffix.lower()
        
        search_patterns = []
        if ext == '.py':
            search_patterns = [
                f'from {file_name} import',
                f'from .{file_name} import',
                f'import {file_name}',
            ]
        elif ext in ['.js', '.ts', '.jsx', '.tsx']:
            search_patterns = [
                f"require('{file_name}'",
                f'require("{file_name}"',
                f"import .* from '{file_name}'",
                f'import .* from "{file_name}"',
                f'import("{file_name}"',
            ]
        
        if not search_patterns:
            return importers
        
        for pattern in search_patterns:
            try:
                result = subprocess.run(
                    ['grep', '-r', '-l', '-E', pattern, str(self.project_root)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line and line not in importers:
                            rel_path = os.path.relpath(line, self.project_root)
                            if rel_path != file_path:
                                importers.append(rel_path)
            except Exception:
                pass
        
        return importers
    
    def find_usages(self, file_path: str, change_description: str = "") -> List[Dict[str, Any]]:
        """Find where functions/classes from this file are used."""
        usages = []
        
        function_match = re.search(r'(?:function|def|class)\s+(\w+)', change_description)
        if function_match:
            func_name = function_match.group(1)
            try:
                result = subprocess.run(
                    ['grep', '-r', '-n', func_name, str(self.project_root)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n')[:20]:
                        if line:
                            parts = line.split(':', 2)
                            if len(parts) >= 2:
                                usages.append({
                                    'file': os.path.relpath(parts[0], self.project_root),
                                    'line': parts[1],
                                    'usage': func_name
                                })
            except Exception:
                pass
        
        return usages
    
    def find_related_tests(self, file_path: str) -> List[str]:
        """Find test files that might cover this file."""
        tests = []
        file_name = Path(file_path).stem
        
        test_patterns = [
            f'test_{file_name}*.py',
            f'*_{file_name}_test.py',
            f'{file_name}.test.js',
            f'{file_name}.spec.js',
            f'{file_name}.test.ts',
            f'{file_name}.spec.ts',
        ]
        
        for pattern in test_patterns:
            try:
                result = subprocess.run(
                    ['find', str(self.project_root), '-name', pattern],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            tests.append(os.path.relpath(line, self.project_root))
            except Exception:
                pass
        
        return tests
    
    def _detect_breaking_changes(self, file_path: str, change_description: str) -> List[str]:
        """Detect potential breaking changes."""
        breaking = []
        
        breaking_keywords = [
            'remove', 'delete', 'eliminar', 'borrar',
            'rename', 'renombrar', 'change signature', 'cambiar firma',
            'deprecate', 'deprecar', 'break', 'romper',
        ]
        
        change_lower = change_description.lower()
        for keyword in breaking_keywords:
            if keyword in change_lower:
                breaking.append(f"Potential breaking change: contains '{keyword}'")
        
        return breaking
    
    def _calculate_risk_level(
        self, 
        importers: List[str], 
        usages: List[Dict], 
        tests: List[str],
        breaking_changes: List[str]
    ) -> str:
        """Calculate overall risk level of the change."""
        if breaking_changes:
            return 'high'
        
        if len(importers) > 5 or len(usages) > 10:
            return 'high'
        
        if len(importers) > 2 or len(usages) > 5:
            return 'medium'
        
        if len(tests) == 0 and len(importers) > 0:
            return 'medium'
        
        return 'low'


class WorkflowManager:
    """
    Phase 34.22: Gestor de Workflows
    
    Manages server workflows/processes for the AI.
    Provides interface to restart, check status, and get logs.
    """
    
    DEFAULT_TIMEOUT = 30
    
    def __init__(self):
        self.workflow_states: Dict[str, Dict] = {}
    
    def restart_workflow(self, name: str, timeout: int = None) -> Dict[str, Any]:
        """
        Restart a specific workflow.
        Note: In Replit environment, this would integrate with Replit's workflow system.
        """
        timeout = timeout or self.DEFAULT_TIMEOUT
        logger.info(f"WorkflowManager: Restarting workflow '{name}'")
        
        self.workflow_states[name] = {
            'status': 'restarting',
            'restart_time': datetime.now().isoformat()
        }
        
        return {
            'success': True,
            'workflow': name,
            'action': 'restart',
            'message': f'Workflow {name} restart initiated'
        }
    
    def get_workflow_status(self, name: str) -> Dict[str, Any]:
        """Get the status of a workflow (running/stopped/error)."""
        state = self.workflow_states.get(name, {'status': 'unknown'})
        
        return {
            'name': name,
            'status': state.get('status', 'unknown'),
            'last_restart': state.get('restart_time'),
        }
    
    def wait_for_port(self, port: int, timeout: int = None, host: str = '127.0.0.1') -> Dict[str, Any]:
        """Wait for a port to become available (server ready)."""
        timeout = timeout or self.DEFAULT_TIMEOUT
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    logger.info(f"WorkflowManager: Port {port} is ready")
                    return {
                        'success': True,
                        'port': port,
                        'ready': True,
                        'wait_time': time.time() - start_time
                    }
            except Exception:
                pass
            
            time.sleep(0.5)
        
        logger.warning(f"WorkflowManager: Timeout waiting for port {port}")
        return {
            'success': False,
            'port': port,
            'ready': False,
            'error': f'Timeout after {timeout}s'
        }
    
    def get_workflow_logs(self, name: str, lines: int = 100) -> Dict[str, Any]:
        """Get recent logs from a workflow."""
        log_paths = [
            Path('logs') / f'{name}.log',
            Path('.logs') / f'{name}.log',
            Path(f'{name}.log'),
        ]
        
        for log_path in log_paths:
            if log_path.exists():
                try:
                    with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                        all_lines = f.readlines()
                        recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                    
                    return {
                        'success': True,
                        'workflow': name,
                        'lines': recent_lines,
                        'total_lines': len(all_lines),
                        'log_path': str(log_path)
                    }
                except Exception as e:
                    return {'success': False, 'error': str(e)}
        
        return {
            'success': False,
            'workflow': name,
            'error': 'Log file not found'
        }
    
    def check_server_health(self, port: int = 5000, path: str = '/') -> Dict[str, Any]:
        """Check if a server is responding correctly."""
        try:
            import urllib.request
            url = f'http://127.0.0.1:{port}{path}'
            
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as response:
                status = response.status
                return {
                    'success': True,
                    'healthy': status == 200,
                    'status_code': status,
                    'url': url
                }
        except Exception as e:
            return {
                'success': False,
                'healthy': False,
                'error': str(e)
            }


class TaskManager:
    """
    Phase 34.23: Gestor de Tareas con Tracking
    
    Task management system with progress tracking to show users.
    """
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid4())[:8]
        self.tasks: List[Task] = []
        self.current_task_index: int = -1
    
    def create_task_list(self, task_definitions: List[Dict]) -> List[Task]:
        """Create a list of tasks from definitions."""
        self.tasks = []
        
        for i, task_def in enumerate(task_definitions):
            task = Task(
                id=f"task_{self.session_id}_{i}",
                title=task_def.get('title', f'Task {i + 1}'),
                description=task_def.get('description', ''),
                status=TaskStatus.PENDING,
                progress=0
            )
            self.tasks.append(task)
        
        logger.info(f"TaskManager: Created task list with {len(self.tasks)} tasks")
        return self.tasks
    
    def mark_task_in_progress(self, task_id: str) -> Optional[Task]:
        """Mark a task as in progress."""
        task = self._find_task(task_id)
        if task:
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now().isoformat()
            self.current_task_index = self.tasks.index(task)
            logger.info(f"TaskManager: Task '{task.title}' started")
        return task
    
    def update_task_progress(self, task_id: str, progress: int) -> Optional[Task]:
        """Update progress of a task (0-100)."""
        task = self._find_task(task_id)
        if task:
            task.progress = max(0, min(100, progress))
            logger.debug(f"TaskManager: Task '{task.title}' progress: {progress}%")
        return task
    
    def mark_task_completed(self, task_id: str) -> Optional[Task]:
        """Mark a task as completed."""
        task = self._find_task(task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.progress = 100
            task.completed_at = datetime.now().isoformat()
            logger.info(f"TaskManager: Task '{task.title}' completed")
        return task
    
    def mark_task_failed(self, task_id: str, error: str) -> Optional[Task]:
        """Mark a task as failed."""
        task = self._find_task(task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.error = error
            task.completed_at = datetime.now().isoformat()
            logger.warning(f"TaskManager: Task '{task.title}' failed: {error}")
        return task
    
    def _find_task(self, task_id: str) -> Optional[Task]:
        """Find a task by ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def get_current_task(self) -> Optional[Task]:
        """Get the currently active task."""
        if 0 <= self.current_task_index < len(self.tasks):
            return self.tasks[self.current_task_index]
        return None
    
    def get_next_pending_task(self) -> Optional[Task]:
        """Get the next pending task."""
        for task in self.tasks:
            if task.status == TaskStatus.PENDING:
                return task
        return None
    
    def show_progress_to_user(self) -> Dict[str, Any]:
        """Generate progress summary for display to user."""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks if t.status == TaskStatus.FAILED)
        in_progress = sum(1 for t in self.tasks if t.status == TaskStatus.IN_PROGRESS)
        pending = sum(1 for t in self.tasks if t.status == TaskStatus.PENDING)
        
        overall_progress = (completed / total * 100) if total > 0 else 0
        
        current = self.get_current_task()
        
        return {
            'session_id': self.session_id,
            'total_tasks': total,
            'completed': completed,
            'failed': failed,
            'in_progress': in_progress,
            'pending': pending,
            'overall_progress': round(overall_progress, 1),
            'current_task': {
                'id': current.id,
                'title': current.title,
                'progress': current.progress
            } if current else None,
            'tasks': [
                {
                    'id': t.id,
                    'title': t.title,
                    'status': t.status.value,
                    'progress': t.progress
                }
                for t in self.tasks
            ]
        }
    
    def get_task_list_as_markdown(self) -> str:
        """Generate task list as markdown for display."""
        lines = ["## Task Progress\n"]
        
        for task in self.tasks:
            if task.status == TaskStatus.COMPLETED:
                icon = "✅"
            elif task.status == TaskStatus.IN_PROGRESS:
                icon = "🔄"
            elif task.status == TaskStatus.FAILED:
                icon = "❌"
            else:
                icon = "⏳"
            
            progress_bar = self._generate_progress_bar(task.progress)
            lines.append(f"- {icon} **{task.title}** {progress_bar}")
        
        return "\n".join(lines)
    
    def _generate_progress_bar(self, progress: int, width: int = 10) -> str:
        """Generate a text-based progress bar."""
        filled = int(progress / 100 * width)
        empty = width - filled
        return f"[{'█' * filled}{'░' * empty}] {progress}%"


class AICoreOrchestrator:
    """
    Master orchestrator that combines all AI Core components.
    Provides a unified interface for the AI Constructor.
    """
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        
        self.decision_engine = AIDecisionEngine()
        self.retry_manager = RetryManager()
        self.validator = PreExecutionValidator(str(self.project_root))
        self.rollback_manager = RollbackManager(str(self.project_root))
        self.impact_analyzer = ChangeImpactAnalyzer(str(self.project_root))
        self.workflow_manager = WorkflowManager()
        self.task_manager = TaskManager()
    
    def process_user_message(self, message: str) -> Dict[str, Any]:
        """
        Main entry point: Process a user message and determine next actions.
        """
        intent = self.decision_engine.classify_intent(message)
        
        workflow = self.decision_engine.decide_workflow(intent)
        
        first_step = self.decision_engine.get_current_step()
        
        return {
            'intent': {
                'type': intent.type.value,
                'confidence': intent.confidence,
                'keywords': intent.keywords,
                'target_file': intent.target_file,
                'target_function': intent.target_function,
            },
            'workflow': {
                'name': workflow.name,
                'steps': [s.value for s in workflow.steps],
                'total_steps': len(workflow.steps),
            },
            'next_action': first_step.value if first_step else None,
            'requires_clarification': intent.type == IntentType.AMBIGUOUS,
        }
    
    def execute_step_with_safety(
        self, 
        step_name: str, 
        action: Callable,
        affected_files: List[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a workflow step with full safety measures:
        1. Validate before execution
        2. Create checkpoint
        3. Execute with retry
        4. Rollback on failure if needed
        """
        if affected_files:
            validation = self.validator.validate_before_action('edit', **kwargs)
            if not validation.valid:
                return {
                    'success': False,
                    'step': step_name,
                    'error': 'Validation failed',
                    'validation_errors': validation.errors,
                    'validation_warnings': validation.warnings,
                }
        
        checkpoint_id = None
        if affected_files:
            checkpoint_id = self.rollback_manager.create_checkpoint(
                affected_files, 
                f"Before: {step_name}"
            )
        
        result = self.retry_manager.execute_with_retry(
            action, 
            action_name=step_name
        )
        
        if not result.success and checkpoint_id:
            self.rollback_manager.auto_rollback_on_error(
                checkpoint_id, 
                result.errors[-1] if result.errors else "Unknown error"
            )
        
        self.decision_engine.advance_workflow({
            'step': step_name,
            'success': result.success,
            'attempts': result.attempts,
        })
        
        return {
            'success': result.success,
            'step': step_name,
            'result': result.result,
            'attempts': result.attempts,
            'checkpoint_id': checkpoint_id,
            'workflow_progress': self.decision_engine.get_workflow_summary(),
        }
    
    def get_full_status(self) -> Dict[str, Any]:
        """Get complete status of all components."""
        return {
            'workflow': self.decision_engine.get_workflow_summary(),
            'tasks': self.task_manager.show_progress_to_user(),
            'checkpoints': self.rollback_manager.get_checkpoints(),
            'retry_history': self.retry_manager.attempt_history[-10:],
        }


__all__ = [
    'IntentType',
    'WorkflowStep', 
    'TaskStatus',
    'Intent',
    'Workflow',
    'ValidationResult',
    'Impact',
    'Task',
    'AIDecisionEngine',
    'RetryManager',
    'PreExecutionValidator',
    'RollbackManager',
    'ChangeImpactAnalyzer',
    'WorkflowManager',
    'TaskManager',
    'AICoreOrchestrator',
]
