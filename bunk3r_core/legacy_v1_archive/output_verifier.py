"""
BUNK3R AI - OutputVerifier (34.5)
Sistema de Verificación de Código con Validación de Sintaxis y Score de Calidad

Funcionalidades:
- Validación de sintaxis por lenguaje (Python, JS, HTML, CSS)
- Verificación de imports y dependencias
- Detección de código incompleto
- Score de calidad 0-100
- Sugerencias de mejora automáticas
"""

import re
import ast
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class CodeLanguage(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    HTML = "html"
    CSS = "css"
    SQL = "sql"
    JSON = "json"
    UNKNOWN = "unknown"


@dataclass
class SyntaxIssue:
    line: int
    column: int
    message: str
    severity: str
    code: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ImportIssue:
    module: str
    issue_type: str
    suggestion: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class QualityMetric:
    name: str
    score: int
    max_score: int
    details: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class VerificationReport:
    is_valid: bool
    language: str
    syntax_valid: bool
    syntax_issues: List[SyntaxIssue]
    import_issues: List[ImportIssue]
    completeness_score: int
    quality_score: int
    quality_metrics: List[QualityMetric]
    suggestions: List[str]
    warnings: List[str]
    errors: List[str]
    code_stats: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            "is_valid": self.is_valid,
            "language": self.language,
            "syntax_valid": self.syntax_valid,
            "syntax_issues": [i.to_dict() for i in self.syntax_issues],
            "import_issues": [i.to_dict() for i in self.import_issues],
            "completeness_score": self.completeness_score,
            "quality_score": self.quality_score,
            "quality_metrics": [m.to_dict() for m in self.quality_metrics],
            "suggestions": self.suggestions,
            "warnings": self.warnings,
            "errors": self.errors,
            "code_stats": self.code_stats
        }


class OutputVerifier:
    """
    Verificador de Output - Valida código generado antes de entrega
    
    Capacidades:
    - Validación sintáctica multi-lenguaje
    - Análisis de imports
    - Detección de código incompleto
    - Scoring de calidad
    - Sugerencias de mejora
    """
    
    PYTHON_COMMON_MODULES = {
        'os', 'sys', 'json', 're', 'datetime', 'time', 'math', 'random',
        'collections', 'itertools', 'functools', 'typing', 'dataclasses',
        'logging', 'pathlib', 'uuid', 'hashlib', 'base64', 'copy',
        'flask', 'requests', 'sqlalchemy', 'pytest', 'numpy', 'pandas'
    }
    
    JS_COMMON_MODULES = {
        'react', 'react-dom', 'express', 'axios', 'lodash', 'moment',
        'fs', 'path', 'http', 'https', 'url', 'crypto', 'events'
    }
    
    INCOMPLETE_PATTERNS = [
        r'\.{3,}',
        r'#\s*TODO',
        r'//\s*TODO',
        r'pass\s*#.*later',
        r'raise\s+NotImplementedError',
        r'throw\s+new\s+Error\([\'"]not\s+implemented',
        r'\/\*\s*\.\.\.\s*\*\/',
        r'#\s*FIXME',
        r'//\s*FIXME',
    ]
    
    def __init__(self):
        self.language_validators = {
            CodeLanguage.PYTHON: self._validate_python,
            CodeLanguage.JAVASCRIPT: self._validate_javascript,
            CodeLanguage.HTML: self._validate_html,
            CodeLanguage.CSS: self._validate_css,
            CodeLanguage.JSON: self._validate_json,
            CodeLanguage.SQL: self._validate_sql,
        }
    
    def detect_language(self, code: str, filename: str = None) -> CodeLanguage:
        """Detecta el lenguaje del código"""
        if filename:
            ext_map = {
                '.py': CodeLanguage.PYTHON,
                '.js': CodeLanguage.JAVASCRIPT,
                '.jsx': CodeLanguage.JAVASCRIPT,
                '.ts': CodeLanguage.JAVASCRIPT,
                '.tsx': CodeLanguage.JAVASCRIPT,
                '.html': CodeLanguage.HTML,
                '.htm': CodeLanguage.HTML,
                '.css': CodeLanguage.CSS,
                '.scss': CodeLanguage.CSS,
                '.json': CodeLanguage.JSON,
                '.sql': CodeLanguage.SQL,
            }
            for ext, lang in ext_map.items():
                if filename.endswith(ext):
                    return lang
        
        code_lower = code.strip().lower()
        
        if code_lower.startswith('<!doctype html') or code_lower.startswith('<html'):
            return CodeLanguage.HTML
        
        if re.search(r'^\s*\{[\s\S]*\}\s*$', code) or re.search(r'^\s*\[[\s\S]*\]\s*$', code):
            try:
                json.loads(code)
                return CodeLanguage.JSON
            except:
                pass
        
        python_patterns = [
            r'^import\s+\w+', r'^from\s+\w+\s+import', r'def\s+\w+\s*\(',
            r'class\s+\w+\s*[:\(]', r'if\s+__name__\s*==', r'@\w+\s*\n'
        ]
        if any(re.search(p, code, re.MULTILINE) for p in python_patterns):
            return CodeLanguage.PYTHON
        
        js_patterns = [
            r'const\s+\w+\s*=', r'let\s+\w+\s*=', r'var\s+\w+\s*=',
            r'function\s+\w+\s*\(', r'=>\s*\{', r'require\s*\(',
            r'import\s+\{', r'export\s+(default|const|function)'
        ]
        if any(re.search(p, code, re.MULTILINE) for p in js_patterns):
            return CodeLanguage.JAVASCRIPT
        
        css_patterns = [
            r'\{\s*[\w-]+\s*:', r'@media\s+', r'@import\s+',
            r'\.\w+\s*\{', r'#\w+\s*\{', r':\s*(hover|active|focus)'
        ]
        if any(re.search(p, code) for p in css_patterns):
            return CodeLanguage.CSS
        
        sql_patterns = [
            r'SELECT\s+', r'INSERT\s+INTO', r'UPDATE\s+\w+\s+SET',
            r'DELETE\s+FROM', r'CREATE\s+TABLE', r'ALTER\s+TABLE'
        ]
        if any(re.search(p, code, re.IGNORECASE) for p in sql_patterns):
            return CodeLanguage.SQL
        
        return CodeLanguage.UNKNOWN
    
    def verify(self, code: str, filename: str = None, 
               expected_language: CodeLanguage = None) -> VerificationReport:
        """
        Verifica código y genera reporte completo
        
        Args:
            code: Código a verificar
            filename: Nombre del archivo (opcional, ayuda a detectar lenguaje)
            expected_language: Lenguaje esperado (opcional)
        
        Returns:
            VerificationReport con todos los resultados
        """
        language = expected_language or self.detect_language(code, filename)
        
        syntax_issues = []
        syntax_valid = True
        
        validator = self.language_validators.get(language)
        if validator:
            syntax_valid, syntax_issues = validator(code)
        
        import_issues = self._check_imports(code, language)
        
        completeness_score = self._calculate_completeness(code, language)
        
        quality_metrics = self._calculate_quality_metrics(code, language)
        quality_score = self._aggregate_quality_score(quality_metrics)
        
        suggestions = self._generate_suggestions(
            code, language, syntax_issues, import_issues, quality_metrics
        )
        
        warnings = self._extract_warnings(syntax_issues)
        errors = self._extract_errors(syntax_issues)
        
        code_stats = self._calculate_code_stats(code, language)
        
        is_valid = syntax_valid and len(errors) == 0 and completeness_score >= 50
        
        return VerificationReport(
            is_valid=is_valid,
            language=language.value,
            syntax_valid=syntax_valid,
            syntax_issues=syntax_issues,
            import_issues=import_issues,
            completeness_score=completeness_score,
            quality_score=quality_score,
            quality_metrics=quality_metrics,
            suggestions=suggestions,
            warnings=warnings,
            errors=errors,
            code_stats=code_stats
        )
    
    def _validate_python(self, code: str) -> Tuple[bool, List[SyntaxIssue]]:
        """Valida sintaxis Python usando AST"""
        issues = []
        try:
            ast.parse(code)
            return True, issues
        except SyntaxError as e:
            issues.append(SyntaxIssue(
                line=e.lineno or 0,
                column=e.offset or 0,
                message=str(e.msg) if hasattr(e, 'msg') else str(e),
                severity="error",
                code=e.text or ""
            ))
            return False, issues
        except Exception as e:
            issues.append(SyntaxIssue(
                line=0,
                column=0,
                message=f"Error de parseo: {str(e)}",
                severity="error"
            ))
            return False, issues
    
    def _validate_javascript(self, code: str) -> Tuple[bool, List[SyntaxIssue]]:
        """Valida sintaxis JavaScript con heurísticas"""
        issues = []
        
        brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        line_num = 1
        
        in_string = False
        string_char = None
        in_comment = False
        in_multiline_comment = False
        
        i = 0
        while i < len(code):
            char = code[i]
            
            if char == '\n':
                line_num += 1
                in_comment = False
            
            if in_multiline_comment:
                if char == '*' and i + 1 < len(code) and code[i + 1] == '/':
                    in_multiline_comment = False
                    i += 1
                i += 1
                continue
            
            if not in_string and char == '/' and i + 1 < len(code):
                if code[i + 1] == '/':
                    in_comment = True
                elif code[i + 1] == '*':
                    in_multiline_comment = True
                    i += 1
            
            if in_comment:
                i += 1
                continue
            
            if char in ('"', "'", '`'):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    if i == 0 or code[i - 1] != '\\':
                        in_string = False
                        string_char = None
            
            if not in_string:
                if char in brackets:
                    stack.append((char, line_num))
                elif char in brackets.values():
                    if not stack:
                        issues.append(SyntaxIssue(
                            line=line_num,
                            column=0,
                            message=f"Corchete de cierre '{char}' sin apertura",
                            severity="error"
                        ))
                    else:
                        open_bracket, open_line = stack.pop()
                        expected = brackets[open_bracket]
                        if char != expected:
                            issues.append(SyntaxIssue(
                                line=line_num,
                                column=0,
                                message=f"Corchete '{char}' no coincide con '{open_bracket}' de línea {open_line}",
                                severity="error"
                            ))
            
            i += 1
        
        for open_bracket, open_line in stack:
            issues.append(SyntaxIssue(
                line=open_line,
                column=0,
                message=f"Corchete '{open_bracket}' sin cerrar",
                severity="error"
            ))
        
        if in_string:
            issues.append(SyntaxIssue(
                line=line_num,
                column=0,
                message="String sin cerrar",
                severity="error"
            ))
        
        return len(issues) == 0, issues
    
    def _validate_html(self, code: str) -> Tuple[bool, List[SyntaxIssue]]:
        """Valida sintaxis HTML"""
        issues = []
        
        void_elements = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
                        'link', 'meta', 'param', 'source', 'track', 'wbr'}
        
        tag_pattern = r'<(/?)(\w+)[^>]*(/?)>'
        matches = re.finditer(tag_pattern, code, re.IGNORECASE)
        
        stack = []
        for match in matches:
            is_closing = match.group(1) == '/'
            tag_name = match.group(2).lower()
            is_self_closing = match.group(3) == '/'
            
            line_num = code[:match.start()].count('\n') + 1
            
            if tag_name in void_elements or is_self_closing:
                continue
            
            if is_closing:
                if not stack:
                    issues.append(SyntaxIssue(
                        line=line_num,
                        column=0,
                        message=f"Tag de cierre </{tag_name}> sin apertura",
                        severity="warning"
                    ))
                elif stack[-1][0] != tag_name:
                    expected = stack[-1][0]
                    issues.append(SyntaxIssue(
                        line=line_num,
                        column=0,
                        message=f"Tag </{tag_name}> no coincide con <{expected}> abierto en línea {stack[-1][1]}",
                        severity="warning"
                    ))
                    stack.pop()
                else:
                    stack.pop()
            else:
                stack.append((tag_name, line_num))
        
        for tag_name, open_line in stack:
            issues.append(SyntaxIssue(
                line=open_line,
                column=0,
                message=f"Tag <{tag_name}> sin cerrar",
                severity="warning"
            ))
        
        if not re.search(r'<!doctype\s+html', code, re.IGNORECASE):
            issues.append(SyntaxIssue(
                line=1,
                column=0,
                message="Falta declaración DOCTYPE",
                severity="warning"
            ))
        
        return len([i for i in issues if i.severity == "error"]) == 0, issues
    
    def _validate_css(self, code: str) -> Tuple[bool, List[SyntaxIssue]]:
        """Valida sintaxis CSS"""
        issues = []
        
        brace_count = 0
        line_num = 1
        
        for char in code:
            if char == '\n':
                line_num += 1
            elif char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count < 0:
                    issues.append(SyntaxIssue(
                        line=line_num,
                        column=0,
                        message="Llave de cierre sin apertura",
                        severity="error"
                    ))
                    brace_count = 0
        
        if brace_count > 0:
            issues.append(SyntaxIssue(
                line=line_num,
                column=0,
                message=f"{brace_count} llave(s) sin cerrar",
                severity="error"
            ))
        
        rule_pattern = r'([^{]+)\{([^}]*)\}'
        for match in re.finditer(rule_pattern, code):
            declarations = match.group(2).strip()
            if declarations:
                for decl in declarations.split(';'):
                    decl = decl.strip()
                    if decl and ':' not in decl:
                        line_num = code[:match.start()].count('\n') + 1
                        issues.append(SyntaxIssue(
                            line=line_num,
                            column=0,
                            message=f"Declaración CSS inválida: '{decl[:30]}...'",
                            severity="warning"
                        ))
        
        return len([i for i in issues if i.severity == "error"]) == 0, issues
    
    def _validate_json(self, code: str) -> Tuple[bool, List[SyntaxIssue]]:
        """Valida sintaxis JSON"""
        issues = []
        try:
            json.loads(code)
            return True, issues
        except json.JSONDecodeError as e:
            issues.append(SyntaxIssue(
                line=e.lineno,
                column=e.colno,
                message=e.msg,
                severity="error"
            ))
            return False, issues
    
    def _validate_sql(self, code: str) -> Tuple[bool, List[SyntaxIssue]]:
        """Valida sintaxis SQL básica"""
        issues = []
        
        statements = [s.strip() for s in code.split(';') if s.strip()]
        
        valid_starts = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 
                       'DROP', 'TRUNCATE', 'GRANT', 'REVOKE', 'BEGIN', 'COMMIT', 
                       'ROLLBACK', 'WITH', 'SET', '--', '/*']
        
        for i, stmt in enumerate(statements):
            stmt_upper = stmt.upper().lstrip()
            if not any(stmt_upper.startswith(v) for v in valid_starts):
                issues.append(SyntaxIssue(
                    line=i + 1,
                    column=0,
                    message=f"Statement SQL no reconocido: '{stmt[:30]}...'",
                    severity="warning"
                ))
        
        paren_count = 0
        for char in code:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
        
        if paren_count != 0:
            issues.append(SyntaxIssue(
                line=0,
                column=0,
                message="Paréntesis desbalanceados",
                severity="error"
            ))
        
        return len([i for i in issues if i.severity == "error"]) == 0, issues
    
    def _check_imports(self, code: str, language: CodeLanguage) -> List[ImportIssue]:
        """Verifica imports y dependencias"""
        issues = []
        
        if language == CodeLanguage.PYTHON:
            import_pattern = r'^(?:from\s+(\w+)|import\s+(\w+))'
            for match in re.finditer(import_pattern, code, re.MULTILINE):
                module = match.group(1) or match.group(2)
                if module and module not in self.PYTHON_COMMON_MODULES:
                    if not module.startswith('_'):
                        issues.append(ImportIssue(
                            module=module,
                            issue_type="non_standard",
                            suggestion=f"Verificar que '{module}' esté en requirements.txt"
                        ))
        
        elif language == CodeLanguage.JAVASCRIPT:
            import_pattern = r'(?:import\s+.*?from\s+[\'"]([^\'"]+)[\'"]|require\s*\([\'"]([^\'"]+)[\'"]\))'
            for match in re.finditer(import_pattern, code):
                module = match.group(1) or match.group(2)
                if module and not module.startswith('.') and not module.startswith('/'):
                    base_module = module.split('/')[0]
                    if base_module not in self.JS_COMMON_MODULES:
                        issues.append(ImportIssue(
                            module=module,
                            issue_type="non_standard",
                            suggestion=f"Verificar que '{base_module}' esté en package.json"
                        ))
        
        return issues
    
    def _calculate_completeness(self, code: str, language: CodeLanguage) -> int:
        """Calcula score de completitud del código (0-100)"""
        score = 100
        
        for pattern in self.INCOMPLETE_PATTERNS:
            matches = len(re.findall(pattern, code, re.IGNORECASE))
            score -= matches * 10
        
        placeholder_patterns = [
            r'\b(placeholder|lorem|ipsum|example|sample|test)\b',
            r'your[_\s]*(name|email|password|api[_\s]*key)',
            r'xxx+',
        ]
        for pattern in placeholder_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                score -= 5
        
        if language == CodeLanguage.PYTHON:
            if re.search(r'def\s+\w+\s*\([^)]*\)\s*:\s*$', code, re.MULTILINE):
                score -= 15
        
        if language == CodeLanguage.HTML:
            if not re.search(r'</body>', code, re.IGNORECASE):
                score -= 10
            if not re.search(r'</html>', code, re.IGNORECASE):
                score -= 10
        
        return max(0, min(100, score))
    
    def _calculate_quality_metrics(self, code: str, language: CodeLanguage) -> List[QualityMetric]:
        """Calcula métricas de calidad del código"""
        metrics = []
        
        lines = code.split('\n')
        non_empty_lines = [l for l in lines if l.strip()]
        
        comment_pattern = r'#.*$|//.*$|/\*[\s\S]*?\*/|<!--[\s\S]*?-->'
        comments = re.findall(comment_pattern, code)
        comment_ratio = len(comments) / max(len(non_empty_lines), 1)
        
        doc_score = min(25, int(comment_ratio * 100))
        metrics.append(QualityMetric(
            name="Documentación",
            score=doc_score,
            max_score=25,
            details=f"{len(comments)} comentarios en {len(non_empty_lines)} líneas"
        ))
        
        long_lines = sum(1 for l in lines if len(l) > 100)
        format_score = max(0, 25 - long_lines * 2)
        metrics.append(QualityMetric(
            name="Formato",
            score=format_score,
            max_score=25,
            details=f"{long_lines} líneas > 100 caracteres"
        ))
        
        if language == CodeLanguage.PYTHON:
            func_count = len(re.findall(r'^def\s+\w+', code, re.MULTILINE))
            class_count = len(re.findall(r'^class\s+\w+', code, re.MULTILINE))
            structure_score = min(25, (func_count + class_count * 2) * 3)
        elif language == CodeLanguage.JAVASCRIPT:
            func_count = len(re.findall(r'function\s+\w+|const\s+\w+\s*=\s*(?:async\s*)?\(', code))
            structure_score = min(25, func_count * 3)
        else:
            structure_score = 15
        
        metrics.append(QualityMetric(
            name="Estructura",
            score=structure_score,
            max_score=25,
            details=f"Funciones/clases detectadas"
        ))
        
        security_issues = 0
        security_patterns = [
            (r'eval\s*\(', "eval() es inseguro"),
            (r'exec\s*\(', "exec() es inseguro"),
            (r'password\s*=\s*["\'][^"\']+["\']', "Contraseña hardcodeada"),
            (r'api[_\s]*key\s*=\s*["\'][^"\']+["\']', "API key hardcodeada"),
            (r'innerHTML\s*=', "innerHTML puede ser vulnerable a XSS"),
        ]
        for pattern, _ in security_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                security_issues += 1
        
        security_score = max(0, 25 - security_issues * 8)
        metrics.append(QualityMetric(
            name="Seguridad",
            score=security_score,
            max_score=25,
            details=f"{security_issues} posibles problemas de seguridad"
        ))
        
        return metrics
    
    def _aggregate_quality_score(self, metrics: List[QualityMetric]) -> int:
        """Agrega métricas en score total"""
        total = sum(m.score for m in metrics)
        max_total = sum(m.max_score for m in metrics)
        return int((total / max_total) * 100) if max_total > 0 else 0
    
    def _generate_suggestions(self, code: str, language: CodeLanguage,
                             syntax_issues: List[SyntaxIssue],
                             import_issues: List[ImportIssue],
                             quality_metrics: List[QualityMetric]) -> List[str]:
        """Genera sugerencias de mejora"""
        suggestions = []
        
        for issue in syntax_issues[:3]:
            suggestions.append(f"Corregir error de sintaxis en línea {issue.line}: {issue.message}")
        
        for issue in import_issues[:2]:
            suggestions.append(issue.suggestion)
        
        for metric in quality_metrics:
            if metric.score < metric.max_score * 0.5:
                if metric.name == "Documentación":
                    suggestions.append("Agregar más comentarios y docstrings para mejorar documentación")
                elif metric.name == "Formato":
                    suggestions.append("Dividir líneas largas para mejorar legibilidad")
                elif metric.name == "Seguridad":
                    suggestions.append("Revisar posibles vulnerabilidades de seguridad")
        
        if language == CodeLanguage.PYTHON:
            if not re.search(r'^if\s+__name__\s*==\s*[\'"]__main__[\'"]', code, re.MULTILINE):
                if re.search(r'^def\s+main\s*\(', code, re.MULTILINE):
                    suggestions.append("Agregar bloque if __name__ == '__main__'")
        
        if language == CodeLanguage.HTML:
            if not re.search(r'<meta\s+name=["\']viewport', code, re.IGNORECASE):
                suggestions.append("Agregar meta viewport para diseño responsive")
            if not re.search(r'lang\s*=', code):
                suggestions.append("Agregar atributo lang al tag <html>")
        
        return suggestions[:5]
    
    def _extract_warnings(self, issues: List[SyntaxIssue]) -> List[str]:
        """Extrae warnings de los issues"""
        return [f"Línea {i.line}: {i.message}" for i in issues if i.severity == "warning"]
    
    def _extract_errors(self, issues: List[SyntaxIssue]) -> List[str]:
        """Extrae errores de los issues"""
        return [f"Línea {i.line}: {i.message}" for i in issues if i.severity == "error"]
    
    def _calculate_code_stats(self, code: str, language: CodeLanguage) -> Dict[str, Any]:
        """Calcula estadísticas del código"""
        lines = code.split('\n')
        non_empty = [l for l in lines if l.strip()]
        
        stats = {
            "total_lines": len(lines),
            "non_empty_lines": len(non_empty),
            "characters": len(code),
            "language": language.value,
        }
        
        if language == CodeLanguage.PYTHON:
            stats["functions"] = len(re.findall(r'^def\s+\w+', code, re.MULTILINE))
            stats["classes"] = len(re.findall(r'^class\s+\w+', code, re.MULTILINE))
            stats["imports"] = len(re.findall(r'^(?:import|from)\s+\w+', code, re.MULTILINE))
        
        elif language == CodeLanguage.JAVASCRIPT:
            stats["functions"] = len(re.findall(r'function\s+\w+|=>\s*\{', code))
            stats["const_declarations"] = len(re.findall(r'\bconst\s+\w+', code))
            stats["let_declarations"] = len(re.findall(r'\blet\s+\w+', code))
        
        elif language == CodeLanguage.HTML:
            stats["tags"] = len(re.findall(r'<\w+', code))
            stats["has_head"] = bool(re.search(r'<head', code, re.IGNORECASE))
            stats["has_body"] = bool(re.search(r'<body', code, re.IGNORECASE))
        
        return stats
    
    def quick_validate(self, code: str, language: CodeLanguage = None) -> Tuple[bool, str]:
        """
        Validación rápida - retorna (válido, mensaje)
        Útil para verificaciones rápidas sin reporte completo
        """
        lang = language or self.detect_language(code)
        validator = self.language_validators.get(lang)
        
        if not validator:
            return True, "Lenguaje no soportado para validación"
        
        is_valid, issues = validator(code)
        
        if is_valid:
            return True, "Sintaxis válida"
        else:
            error_msgs = [i.message for i in issues if i.severity == "error"]
            return False, "; ".join(error_msgs[:3])


output_verifier = OutputVerifier()


def verify_code(code: str, filename: str = None) -> Dict:
    """Helper function para verificar código"""
    report = output_verifier.verify(code, filename)
    return report.to_dict()


def quick_validate(code: str) -> Tuple[bool, str]:
    """Helper function para validación rápida"""
    return output_verifier.quick_validate(code)
