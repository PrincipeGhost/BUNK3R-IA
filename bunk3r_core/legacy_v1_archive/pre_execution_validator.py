"""
BUNK3R AI - PreExecutionValidator (34.19)
Validador Pre-Ejecución Completo

Funcionalidades:
- Verificación de sintaxis antes de escribir
- Verificación de dependencias
- Verificación de permisos
- Alerta de cambios destructivos
"""

import os
import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from bunk3r_core.output_verifier import output_verifier, CodeLanguage
except ImportError:
    output_verifier = None
    CodeLanguage = None


class ValidationLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ActionType(Enum):
    CREATE_FILE = "create_file"
    MODIFY_FILE = "modify_file"
    DELETE_FILE = "delete_file"
    EXECUTE_COMMAND = "execute_command"
    INSTALL_PACKAGE = "install_package"
    DATABASE_OPERATION = "database_operation"
    NETWORK_REQUEST = "network_request"


@dataclass
class ValidationIssue:
    level: ValidationLevel
    message: str
    action_type: ActionType
    details: Dict[str, Any] = field(default_factory=dict)
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "level": self.level.value,
            "message": self.message,
            "action_type": self.action_type.value,
            "details": self.details,
            "suggestion": self.suggestion
        }


@dataclass
class ValidationResult:
    is_safe: bool
    can_proceed: bool
    issues: List[ValidationIssue]
    requires_confirmation: bool
    confirmation_message: Optional[str]
    validated_actions: List[Dict]
    
    def to_dict(self) -> Dict:
        return {
            "is_safe": self.is_safe,
            "can_proceed": self.can_proceed,
            "issues": [i.to_dict() for i in self.issues],
            "requires_confirmation": self.requires_confirmation,
            "confirmation_message": self.confirmation_message,
            "validated_actions": self.validated_actions
        }


class PreExecutionValidator:
    """
    Validador Pre-Ejecución
    
    Verifica que las acciones a ejecutar sean seguras y válidas
    antes de realizarlas.
    """
    
    PROTECTED_PATHS = [
        '.env', '.env.local', '.env.production',
        'requirements.txt', 'package.json', 'package-lock.json',
        '.git/', '.gitignore',
        'Dockerfile', 'docker-compose.yml',
        '__pycache__/', 'node_modules/',
        'venv/', '.venv/',
    ]
    
    CRITICAL_PATHS = [
        '/', '/etc', '/usr', '/bin', '/sbin',
        '/home', '/root', '/var',
        '..', '../..',
    ]
    
    DANGEROUS_COMMANDS = [
        'rm -rf', 'rm -r /', 'dd if=',
        'mkfs', 'fdisk', 'format',
        '> /dev/', 'chmod 777',
        'curl | bash', 'wget | sh',
        'sudo', 'su -',
    ]
    
    DESTRUCTIVE_SQL = [
        'DROP TABLE', 'DROP DATABASE', 'TRUNCATE',
        'DELETE FROM', 'ALTER TABLE.*DROP',
    ]
    
    REQUIRED_PACKAGES = {
        'python': {
            'flask': ['flask', 'werkzeug'],
            'fastapi': ['fastapi', 'uvicorn', 'pydantic'],
            'requests': ['requests'],
            'database': ['sqlalchemy', 'psycopg2-binary'],
        },
        'node': {
            'express': ['express'],
            'react': ['react', 'react-dom'],
            'next': ['next', 'react', 'react-dom'],
        }
    }
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.confirmation_required = False
        self.last_validation: Optional[ValidationResult] = None
    
    def validate_action(self, action_type: ActionType, 
                       action_data: Dict[str, Any]) -> ValidationResult:
        """
        Valida una acción antes de ejecutarla
        
        Args:
            action_type: Tipo de acción
            action_data: Datos de la acción
        
        Returns:
            ValidationResult con el resultado
        """
        issues = []
        requires_confirmation = False
        confirmation_message = None
        
        validators = {
            ActionType.CREATE_FILE: self._validate_create_file,
            ActionType.MODIFY_FILE: self._validate_modify_file,
            ActionType.DELETE_FILE: self._validate_delete_file,
            ActionType.EXECUTE_COMMAND: self._validate_command,
            ActionType.INSTALL_PACKAGE: self._validate_package,
            ActionType.DATABASE_OPERATION: self._validate_database,
        }
        
        validator = validators.get(action_type)
        if validator:
            validation_issues, needs_confirm, confirm_msg = validator(action_data)
            issues.extend(validation_issues)
            if needs_confirm:
                requires_confirmation = True
                confirmation_message = confirm_msg
        
        has_critical = any(i.level == ValidationLevel.CRITICAL for i in issues)
        has_errors = any(i.level == ValidationLevel.ERROR for i in issues)
        
        is_safe = not has_critical and not has_errors
        can_proceed = is_safe or (has_errors and requires_confirmation)
        
        result = ValidationResult(
            is_safe=is_safe,
            can_proceed=can_proceed,
            issues=issues,
            requires_confirmation=requires_confirmation,
            confirmation_message=confirmation_message,
            validated_actions=[{
                "type": action_type.value,
                "data": action_data,
                "validated": is_safe
            }]
        )
        
        self.last_validation = result
        return result
    
    def validate_batch(self, actions: List[Tuple[ActionType, Dict]]) -> ValidationResult:
        """
        Valida un lote de acciones
        
        Args:
            actions: Lista de tuplas (ActionType, action_data)
        
        Returns:
            ValidationResult agregado
        """
        all_issues = []
        requires_confirmation = False
        confirmation_messages = []
        validated_actions = []
        
        for action_type, action_data in actions:
            result = self.validate_action(action_type, action_data)
            all_issues.extend(result.issues)
            
            if result.requires_confirmation:
                requires_confirmation = True
                if result.confirmation_message:
                    confirmation_messages.append(result.confirmation_message)
            
            validated_actions.extend(result.validated_actions)
        
        has_critical = any(i.level == ValidationLevel.CRITICAL for i in all_issues)
        has_errors = any(i.level == ValidationLevel.ERROR for i in all_issues)
        
        return ValidationResult(
            is_safe=not has_critical and not has_errors,
            can_proceed=not has_critical,
            issues=all_issues,
            requires_confirmation=requires_confirmation,
            confirmation_message="\n".join(confirmation_messages) if confirmation_messages else None,
            validated_actions=validated_actions
        )
    
    def _validate_create_file(self, data: Dict) -> Tuple[List[ValidationIssue], bool, Optional[str]]:
        """Valida creación de archivo"""
        issues = []
        needs_confirm = False
        confirm_msg = None
        
        filepath = data.get("path", "")
        content = data.get("content", "")
        
        if self._is_path_protected(filepath):
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message=f"Creando archivo en ruta protegida: {filepath}",
                action_type=ActionType.CREATE_FILE,
                details={"path": filepath},
                suggestion="Verificar que es intencional modificar este archivo"
            ))
            needs_confirm = True
            confirm_msg = f"¿Confirmar creación de archivo protegido: {filepath}?"
        
        if self._is_path_critical(filepath):
            issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                message=f"Ruta crítica del sistema: {filepath}",
                action_type=ActionType.CREATE_FILE,
                details={"path": filepath},
                suggestion="No se permite crear archivos en rutas del sistema"
            ))
        
        full_path = self.project_root / filepath
        if full_path.exists():
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message=f"El archivo ya existe: {filepath}",
                action_type=ActionType.CREATE_FILE,
                details={"path": filepath},
                suggestion="Se sobrescribirá el archivo existente"
            ))
            needs_confirm = True
            confirm_msg = f"El archivo {filepath} ya existe. ¿Sobrescribir?"
        
        if content and output_verifier:
            report = output_verifier.verify(content, filepath)
            if not report.syntax_valid:
                for error in report.errors[:3]:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=f"Error de sintaxis: {error}",
                        action_type=ActionType.CREATE_FILE,
                        details={"path": filepath},
                        suggestion="Corregir error de sintaxis antes de crear archivo"
                    ))
        
        return issues, needs_confirm, confirm_msg
    
    def _validate_modify_file(self, data: Dict) -> Tuple[List[ValidationIssue], bool, Optional[str]]:
        """Valida modificación de archivo"""
        issues = []
        needs_confirm = False
        confirm_msg = None
        
        filepath = data.get("path", "")
        content = data.get("content", "")
        
        full_path = self.project_root / filepath
        if not full_path.exists():
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                message=f"Archivo no existe: {filepath}",
                action_type=ActionType.MODIFY_FILE,
                details={"path": filepath},
                suggestion="Usar acción CREATE_FILE para crear archivos nuevos"
            ))
        
        if self._is_path_protected(filepath):
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message=f"Modificando archivo protegido: {filepath}",
                action_type=ActionType.MODIFY_FILE,
                details={"path": filepath}
            ))
            needs_confirm = True
            confirm_msg = f"¿Confirmar modificación de archivo protegido: {filepath}?"
        
        if content and output_verifier:
            report = output_verifier.verify(content, filepath)
            if not report.syntax_valid:
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message="El código tiene errores de sintaxis",
                    action_type=ActionType.MODIFY_FILE,
                    details={"path": filepath, "errors": report.errors[:3]}
                ))
        
        return issues, needs_confirm, confirm_msg
    
    def _validate_delete_file(self, data: Dict) -> Tuple[List[ValidationIssue], bool, Optional[str]]:
        """Valida eliminación de archivo"""
        issues = []
        filepath = data.get("path", "")
        
        issues.append(ValidationIssue(
            level=ValidationLevel.WARNING,
            message=f"Eliminando archivo: {filepath}",
            action_type=ActionType.DELETE_FILE,
            details={"path": filepath},
            suggestion="Verificar que el archivo puede ser eliminado de forma segura"
        ))
        
        if self._is_path_protected(filepath):
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                message=f"No se puede eliminar archivo protegido: {filepath}",
                action_type=ActionType.DELETE_FILE,
                details={"path": filepath}
            ))
        
        confirm_msg = f"¿Confirmar eliminación de: {filepath}? Esta acción no se puede deshacer."
        
        return issues, True, confirm_msg
    
    def _validate_command(self, data: Dict) -> Tuple[List[ValidationIssue], bool, Optional[str]]:
        """Valida ejecución de comando"""
        issues = []
        needs_confirm = False
        confirm_msg = None
        
        command = data.get("command", "")
        
        for dangerous in self.DANGEROUS_COMMANDS:
            if dangerous.lower() in command.lower():
                issues.append(ValidationIssue(
                    level=ValidationLevel.CRITICAL,
                    message=f"Comando peligroso detectado: contiene '{dangerous}'",
                    action_type=ActionType.EXECUTE_COMMAND,
                    details={"command": command, "pattern": dangerous},
                    suggestion="Este comando podría causar daños irreversibles"
                ))
        
        if "pip install" in command or "npm install" in command:
            packages = command.split("install")[-1].strip().split()
            for pkg in packages:
                if pkg.startswith("-"):
                    continue
                issues.append(ValidationIssue(
                    level=ValidationLevel.INFO,
                    message=f"Instalando paquete: {pkg}",
                    action_type=ActionType.INSTALL_PACKAGE,
                    details={"package": pkg}
                ))
        
        if any(cmd in command for cmd in ['git commit', 'git push', 'git reset']):
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message="Comando Git que modifica historial",
                action_type=ActionType.EXECUTE_COMMAND,
                details={"command": command}
            ))
            needs_confirm = True
            confirm_msg = f"¿Ejecutar comando Git: {command[:50]}...?"
        
        return issues, needs_confirm, confirm_msg
    
    def _validate_package(self, data: Dict) -> Tuple[List[ValidationIssue], bool, Optional[str]]:
        """Valida instalación de paquete"""
        issues = []
        
        package = data.get("package", "")
        manager = data.get("manager", "pip")
        
        issues.append(ValidationIssue(
            level=ValidationLevel.INFO,
            message=f"Instalando paquete {package} con {manager}",
            action_type=ActionType.INSTALL_PACKAGE,
            details={"package": package, "manager": manager}
        ))
        
        return issues, False, None
    
    def _validate_database(self, data: Dict) -> Tuple[List[ValidationIssue], bool, Optional[str]]:
        """Valida operación de base de datos"""
        issues = []
        needs_confirm = False
        confirm_msg = None
        
        query = data.get("query", "")
        query_upper = query.upper()
        
        for pattern in self.DESTRUCTIVE_SQL:
            if re.search(pattern, query_upper):
                issues.append(ValidationIssue(
                    level=ValidationLevel.CRITICAL,
                    message=f"Operación SQL destructiva detectada: {pattern}",
                    action_type=ActionType.DATABASE_OPERATION,
                    details={"query": query[:100]},
                    suggestion="Las operaciones destructivas requieren confirmación explícita"
                ))
                needs_confirm = True
                confirm_msg = "⚠️ Esta operación modificará datos de forma irreversible. ¿Continuar?"
        
        if "SELECT" in query_upper and "WHERE" not in query_upper:
            row_limit = re.search(r'LIMIT\s+(\d+)', query_upper)
            if not row_limit or int(row_limit.group(1)) > 10000:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message="Query SELECT sin LIMIT podría retornar muchos registros",
                    action_type=ActionType.DATABASE_OPERATION,
                    details={"query": query[:100]},
                    suggestion="Agregar LIMIT para evitar sobrecarga"
                ))
        
        return issues, needs_confirm, confirm_msg
    
    def _is_path_protected(self, path: str) -> bool:
        """Verifica si una ruta está protegida"""
        path_lower = path.lower()
        for protected in self.PROTECTED_PATHS:
            if protected.lower() in path_lower:
                return True
        return False
    
    def _is_path_critical(self, path: str) -> bool:
        """Verifica si una ruta es crítica del sistema"""
        for critical in self.CRITICAL_PATHS:
            if path.startswith(critical):
                return True
        return False
    
    def check_dependencies(self, code: str, language: str = "python") -> List[ValidationIssue]:
        """
        Verifica que las dependencias importadas estén disponibles
        
        Args:
            code: Código a verificar
            language: Lenguaje del código
        
        Returns:
            Lista de issues de dependencias
        """
        issues = []
        
        if language == "python":
            import_pattern = r'^(?:from\s+(\w+)|import\s+(\w+))'
            imports = set()
            
            for match in re.finditer(import_pattern, code, re.MULTILINE):
                module = match.group(1) or match.group(2)
                if module:
                    imports.add(module)
            
            req_path = self.project_root / "requirements.txt"
            installed = set()
            
            if req_path.exists():
                with open(req_path) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            pkg = re.split(r'[=<>~!]', line)[0].strip()
                            installed.add(pkg.lower())
            
            stdlib = {
                'os', 'sys', 'json', 're', 'datetime', 'time', 'math', 'random',
                'collections', 'itertools', 'functools', 'typing', 'dataclasses',
                'logging', 'pathlib', 'uuid', 'hashlib', 'base64', 'copy', 'ast',
                'abc', 'enum', 'io', 'string', 'textwrap', 'struct', 'operator'
            }
            
            for module in imports:
                if module.lower() not in stdlib and module.lower() not in installed:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=f"Módulo '{module}' no encontrado en requirements.txt",
                        action_type=ActionType.CREATE_FILE,
                        details={"module": module},
                        suggestion=f"Agregar '{module}' a requirements.txt"
                    ))
        
        return issues
    
    def quick_check(self, action_type: ActionType, data: Dict) -> Tuple[bool, str]:
        """
        Verificación rápida de una acción
        
        Returns:
            Tupla (es_seguro, mensaje)
        """
        result = self.validate_action(action_type, data)
        
        if result.is_safe:
            return True, "Acción validada correctamente"
        
        errors = [i for i in result.issues if i.level in [ValidationLevel.ERROR, ValidationLevel.CRITICAL]]
        if errors:
            return False, errors[0].message
        
        if result.requires_confirmation:
            return True, result.confirmation_message or "Requiere confirmación"
        
        return True, "Validación completada con advertencias"


pre_execution_validator = PreExecutionValidator()


def validate_action(action_type: str, data: Dict) -> Dict:
    """Helper para validar una acción"""
    try:
        action = ActionType(action_type)
    except ValueError:
        return {"is_safe": False, "error": f"Tipo de acción desconocido: {action_type}"}
    
    result = pre_execution_validator.validate_action(action, data)
    return result.to_dict()


def quick_validate(action_type: str, data: Dict) -> Tuple[bool, str]:
    """Helper para validación rápida"""
    try:
        action = ActionType(action_type)
    except ValueError:
        return False, f"Tipo de acción desconocido: {action_type}"
    
    return pre_execution_validator.quick_check(action, data)
