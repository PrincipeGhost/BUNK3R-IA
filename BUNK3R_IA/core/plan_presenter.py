"""
BUNK3R AI - PlanPresenter (34.4)
Sistema de Presentación Visual de Planes

Funcionalidades:
- Formato visual de planes
- Estimación de tiempo por tarea
- Árbol de dependencias
- Confirmación interactiva
- Modificación de plan por usuario
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


class TaskComplexity(Enum):
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PlanTask:
    id: str
    title: str
    description: str
    complexity: TaskComplexity
    estimated_minutes: int
    dependencies: List[str] = field(default_factory=list)
    files_affected: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    order: int = 0
    optional: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "complexity": self.complexity.value,
            "estimated_minutes": self.estimated_minutes,
            "dependencies": self.dependencies,
            "files_affected": self.files_affected,
            "status": self.status.value,
            "order": self.order,
            "optional": self.optional
        }


@dataclass
class PlanRisk:
    id: str
    description: str
    level: RiskLevel
    mitigation: str
    affected_tasks: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "description": self.description,
            "level": self.level.value,
            "mitigation": self.mitigation,
            "affected_tasks": self.affected_tasks
        }


@dataclass
class ExecutionPlan:
    id: str
    title: str
    description: str
    tasks: List[PlanTask]
    risks: List[PlanRisk]
    total_estimated_minutes: int
    files_to_create: List[str]
    files_to_modify: List[str]
    dependencies_needed: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    confirmed: bool = False
    modifications: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "tasks": [t.to_dict() for t in self.tasks],
            "risks": [r.to_dict() for r in self.risks],
            "total_estimated_minutes": self.total_estimated_minutes,
            "estimated_time_formatted": self._format_time(self.total_estimated_minutes),
            "files_to_create": self.files_to_create,
            "files_to_modify": self.files_to_modify,
            "dependencies_needed": self.dependencies_needed,
            "created_at": self.created_at.isoformat(),
            "confirmed": self.confirmed,
            "modifications": self.modifications,
            "summary": self._generate_summary()
        }
    
    def _format_time(self, minutes: int) -> str:
        if minutes < 60:
            return f"{minutes} minutos"
        hours = minutes // 60
        mins = minutes % 60
        if mins == 0:
            return f"{hours} hora{'s' if hours > 1 else ''}"
        return f"{hours}h {mins}min"
    
    def _generate_summary(self) -> Dict:
        return {
            "total_tasks": len(self.tasks),
            "required_tasks": len([t for t in self.tasks if not t.optional]),
            "optional_tasks": len([t for t in self.tasks if t.optional]),
            "files_count": len(self.files_to_create) + len(self.files_to_modify),
            "high_risks": len([r for r in self.risks if r.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]])
        }


class PlanPresenter:
    """
    Presentador de Planes - Fase 5 del Constructor
    
    Genera planes visuales, estima tiempos, identifica dependencias
    y permite modificaciones interactivas.
    """
    
    COMPLEXITY_TIME_MAP = {
        TaskComplexity.TRIVIAL: 5,
        TaskComplexity.SIMPLE: 15,
        TaskComplexity.MEDIUM: 30,
        TaskComplexity.COMPLEX: 60,
        TaskComplexity.VERY_COMPLEX: 120,
    }
    
    TASK_PATTERNS = {
        "create_file": {
            "patterns": [r"crear\s+archivo", r"nuevo\s+archivo", r"generar\s+\w+\."],
            "complexity": TaskComplexity.SIMPLE,
            "base_time": 10
        },
        "create_component": {
            "patterns": [r"crear\s+componente", r"nuevo\s+componente", r"implementar\s+\w+"],
            "complexity": TaskComplexity.MEDIUM,
            "base_time": 25
        },
        "create_page": {
            "patterns": [r"crear\s+página", r"nueva\s+página", r"añadir\s+vista"],
            "complexity": TaskComplexity.MEDIUM,
            "base_time": 30
        },
        "create_api": {
            "patterns": [r"crear\s+api", r"endpoint", r"ruta\s+\w+"],
            "complexity": TaskComplexity.COMPLEX,
            "base_time": 45
        },
        "add_style": {
            "patterns": [r"estilos?", r"css", r"diseño"],
            "complexity": TaskComplexity.SIMPLE,
            "base_time": 15
        },
        "add_functionality": {
            "patterns": [r"añadir\s+funcionalidad", r"implementar\s+lógica", r"agregar\s+función"],
            "complexity": TaskComplexity.MEDIUM,
            "base_time": 30
        },
        "database": {
            "patterns": [r"base\s+de\s+datos", r"modelo", r"migración", r"tabla"],
            "complexity": TaskComplexity.COMPLEX,
            "base_time": 40
        },
        "integration": {
            "patterns": [r"integrar", r"conectar", r"api\s+externa"],
            "complexity": TaskComplexity.COMPLEX,
            "base_time": 50
        },
        "testing": {
            "patterns": [r"test", r"prueba", r"verificar"],
            "complexity": TaskComplexity.SIMPLE,
            "base_time": 15
        },
        "documentation": {
            "patterns": [r"documentar", r"readme", r"comentarios"],
            "complexity": TaskComplexity.TRIVIAL,
            "base_time": 10
        }
    }
    
    def __init__(self):
        self.plans: Dict[str, ExecutionPlan] = {}
    
    def create_plan(self, plan_id: str, title: str, description: str,
                   task_descriptions: List[str],
                   context: Dict[str, Any] = None) -> ExecutionPlan:
        """
        Crea un plan de ejecución
        
        Args:
            plan_id: ID único del plan
            title: Título del plan
            description: Descripción general
            task_descriptions: Lista de descripciones de tareas
            context: Contexto adicional (tecnología, preferencias, etc.)
        
        Returns:
            ExecutionPlan completo
        """
        context = context or {}
        
        tasks = []
        files_to_create = []
        files_to_modify = []
        dependencies = []
        
        for i, desc in enumerate(task_descriptions):
            task = self._create_task(f"task_{i+1}", desc, i + 1, context)
            tasks.append(task)
            files_to_create.extend(task.files_affected)
        
        self._resolve_dependencies(tasks)
        
        risks = self._identify_risks(tasks, context)
        
        dependencies = self._identify_dependencies(tasks, context)
        
        total_time = sum(t.estimated_minutes for t in tasks)
        
        plan = ExecutionPlan(
            id=plan_id,
            title=title,
            description=description,
            tasks=tasks,
            risks=risks,
            total_estimated_minutes=total_time,
            files_to_create=files_to_create,
            files_to_modify=files_to_modify,
            dependencies_needed=dependencies
        )
        
        self.plans[plan_id] = plan
        return plan
    
    def _create_task(self, task_id: str, description: str, 
                    order: int, context: Dict) -> PlanTask:
        """Crea una tarea individual"""
        complexity = TaskComplexity.MEDIUM
        base_time = 20
        desc_lower = description.lower()
        
        for task_type, config in self.TASK_PATTERNS.items():
            for pattern in config["patterns"]:
                if re.search(pattern, desc_lower):
                    complexity = config["complexity"]
                    base_time = config["base_time"]
                    break
        
        files = self._extract_file_references(description)
        
        estimated_time = base_time
        if context.get("technology") == "React":
            estimated_time = int(estimated_time * 1.2)
        elif context.get("technology") == "HTML/CSS/JS puro":
            estimated_time = int(estimated_time * 0.8)
        
        title = description.split('.')[0][:60]
        if len(title) < len(description.split('.')[0]):
            title += "..."
        
        return PlanTask(
            id=task_id,
            title=title,
            description=description,
            complexity=complexity,
            estimated_minutes=estimated_time,
            files_affected=files,
            order=order
        )
    
    def _extract_file_references(self, text: str) -> List[str]:
        """Extrae referencias a archivos del texto"""
        files = []
        
        patterns = [
            r'(\w+\.(?:py|js|jsx|ts|tsx|html|css|json|sql|md))',
            r'(?:archivo|file)\s+["\']?(\w+\.\w+)["\']?',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            files.extend(matches)
        
        return list(set(files))
    
    def _resolve_dependencies(self, tasks: List[PlanTask]) -> None:
        """Resuelve dependencias entre tareas"""
        dependency_keywords = {
            "database": ["api", "backend", "modelo"],
            "api": ["frontend", "componente", "página"],
            "estilos": ["componente", "página"],
            "testing": ["implementar", "crear", "añadir"],
        }
        
        for i, task in enumerate(tasks):
            task_lower = task.description.lower()
            
            for keyword, dependents in dependency_keywords.items():
                if keyword in task_lower:
                    for j, other_task in enumerate(tasks):
                        if j != i and any(d in other_task.description.lower() for d in dependents):
                            if task.id not in other_task.dependencies:
                                other_task.dependencies.append(task.id)
    
    def _identify_risks(self, tasks: List[PlanTask], 
                       context: Dict) -> List[PlanRisk]:
        """Identifica riesgos del plan"""
        risks = []
        
        complex_tasks = [t for t in tasks if t.complexity in [TaskComplexity.COMPLEX, TaskComplexity.VERY_COMPLEX]]
        if complex_tasks:
            risks.append(PlanRisk(
                id="risk_complexity",
                description=f"Hay {len(complex_tasks)} tarea(s) de alta complejidad",
                level=RiskLevel.MEDIUM,
                mitigation="Dividir en subtareas más pequeñas si es necesario",
                affected_tasks=[t.id for t in complex_tasks]
            ))
        
        db_tasks = [t for t in tasks if "base de datos" in t.description.lower() or "modelo" in t.description.lower()]
        if db_tasks:
            risks.append(PlanRisk(
                id="risk_database",
                description="El proyecto involucra base de datos",
                level=RiskLevel.MEDIUM,
                mitigation="Verificar conexión y permisos antes de ejecutar",
                affected_tasks=[t.id for t in db_tasks]
            ))
        
        total_time = sum(t.estimated_minutes for t in tasks)
        if total_time > 120:
            risks.append(PlanRisk(
                id="risk_time",
                description=f"El plan requiere más de 2 horas ({total_time} min)",
                level=RiskLevel.LOW,
                mitigation="Considerar ejecutar en fases",
                affected_tasks=[]
            ))
        
        return risks
    
    def _identify_dependencies(self, tasks: List[PlanTask], 
                              context: Dict) -> List[str]:
        """Identifica dependencias de paquetes necesarias"""
        dependencies = []
        
        tech = context.get("technology", "").lower()
        
        if "flask" in tech:
            dependencies.extend(["flask", "gunicorn"])
        elif "react" in tech:
            dependencies.extend(["react", "react-dom"])
        elif "express" in tech or "node" in tech:
            dependencies.extend(["express"])
        
        for task in tasks:
            desc_lower = task.description.lower()
            
            if "base de datos" in desc_lower or "postgresql" in desc_lower:
                dependencies.append("psycopg2-binary")
            if "api" in desc_lower and "flask" in tech:
                dependencies.append("flask-cors")
            if "autenticación" in desc_lower or "login" in desc_lower:
                dependencies.append("flask-login" if "flask" in tech else "passport")
        
        return list(set(dependencies))
    
    def format_plan_visual(self, plan: ExecutionPlan) -> str:
        """
        Formatea el plan para visualización en chat
        
        Args:
            plan: Plan a formatear
        
        Returns:
            String formateado para mostrar
        """
        output = f"""
## {plan.title}

{plan.description}

---

### Tareas a Ejecutar ({len(plan.tasks)} tareas)

| # | Tarea | Complejidad | Tiempo Est. |
|---|-------|-------------|-------------|
"""
        
        for task in plan.tasks:
            complexity_emoji = {
                TaskComplexity.TRIVIAL: "🟢",
                TaskComplexity.SIMPLE: "🟢",
                TaskComplexity.MEDIUM: "🟡",
                TaskComplexity.COMPLEX: "🟠",
                TaskComplexity.VERY_COMPLEX: "🔴",
            }.get(task.complexity, "⚪")
            
            opt = " (opcional)" if task.optional else ""
            output += f"| {task.order} | {task.title}{opt} | {complexity_emoji} {task.complexity.value} | {task.estimated_minutes} min |\n"
        
        output += f"""
---

### Resumen

- **Tiempo total estimado:** {plan._format_time(plan.total_estimated_minutes)}
- **Archivos a crear:** {len(plan.files_to_create)}
- **Archivos a modificar:** {len(plan.files_to_modify)}
"""
        
        if plan.dependencies_needed:
            output += f"- **Dependencias necesarias:** {', '.join(plan.dependencies_needed)}\n"
        
        if plan.risks:
            output += "\n### Riesgos Identificados\n\n"
            for risk in plan.risks:
                level_emoji = {
                    RiskLevel.LOW: "🟢",
                    RiskLevel.MEDIUM: "🟡",
                    RiskLevel.HIGH: "🟠",
                    RiskLevel.CRITICAL: "🔴",
                }.get(risk.level, "⚪")
                output += f"- {level_emoji} **{risk.description}**\n"
                output += f"  _Mitigación: {risk.mitigation}_\n"
        
        output += """
---

¿Deseas confirmar este plan para proceder con la ejecución?
Responde **"Sí"** para confirmar o indica qué cambios deseas realizar.
"""
        
        return output
    
    def format_plan_compact(self, plan: ExecutionPlan) -> str:
        """Formato compacto del plan"""
        task_list = "\n".join([
            f"  {i+1}. {t.title} (~{t.estimated_minutes} min)"
            for i, t in enumerate(plan.tasks)
        ])
        
        return f"""**Plan: {plan.title}**

Tareas:
{task_list}

Tiempo total: {plan._format_time(plan.total_estimated_minutes)}

¿Confirmar ejecución?"""
    
    def confirm_plan(self, plan_id: str) -> Tuple[bool, str]:
        """
        Confirma un plan para ejecución
        
        Returns:
            Tupla (éxito, mensaje)
        """
        plan = self.plans.get(plan_id)
        if not plan:
            return False, "Plan no encontrado"
        
        plan.confirmed = True
        return True, "Plan confirmado. Iniciando ejecución..."
    
    def modify_plan(self, plan_id: str, modification: str) -> Tuple[bool, Optional[ExecutionPlan]]:
        """
        Modifica un plan existente
        
        Args:
            plan_id: ID del plan
            modification: Descripción de la modificación
        
        Returns:
            Tupla (éxito, plan_modificado)
        """
        plan = self.plans.get(plan_id)
        if not plan:
            return False, None
        
        plan.modifications.append(modification)
        
        mod_lower = modification.lower()
        
        if "quitar" in mod_lower or "eliminar" in mod_lower or "remover" in mod_lower:
            for task in plan.tasks:
                if any(word in task.title.lower() for word in mod_lower.split() if len(word) > 3):
                    task.status = TaskStatus.SKIPPED
        
        if "agregar" in mod_lower or "añadir" in mod_lower:
            new_task = self._create_task(
                f"task_{len(plan.tasks)+1}",
                modification.replace("agregar", "").replace("añadir", "").strip(),
                len(plan.tasks) + 1,
                {}
            )
            plan.tasks.append(new_task)
        
        plan.total_estimated_minutes = sum(
            t.estimated_minutes for t in plan.tasks 
            if t.status != TaskStatus.SKIPPED
        )
        
        return True, plan
    
    def get_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        """Obtiene un plan por ID"""
        return self.plans.get(plan_id)
    
    def get_next_task(self, plan_id: str) -> Optional[PlanTask]:
        """Obtiene la siguiente tarea pendiente"""
        plan = self.plans.get(plan_id)
        if not plan:
            return None
        
        for task in plan.tasks:
            if task.status == TaskStatus.PENDING:
                deps_completed = all(
                    any(t.id == dep and t.status == TaskStatus.COMPLETED for t in plan.tasks)
                    for dep in task.dependencies
                )
                if deps_completed:
                    return task
        
        return None
    
    def mark_task_complete(self, plan_id: str, task_id: str) -> bool:
        """Marca una tarea como completada"""
        plan = self.plans.get(plan_id)
        if not plan:
            return False
        
        for task in plan.tasks:
            if task.id == task_id:
                task.status = TaskStatus.COMPLETED
                return True
        
        return False
    
    def get_progress(self, plan_id: str) -> Dict[str, Any]:
        """Obtiene el progreso del plan"""
        plan = self.plans.get(plan_id)
        if not plan:
            return {}
        
        completed = len([t for t in plan.tasks if t.status == TaskStatus.COMPLETED])
        total = len([t for t in plan.tasks if t.status != TaskStatus.SKIPPED])
        
        return {
            "completed": completed,
            "total": total,
            "percentage": int((completed / total) * 100) if total > 0 else 0,
            "remaining_time": sum(
                t.estimated_minutes for t in plan.tasks 
                if t.status == TaskStatus.PENDING
            )
        }


plan_presenter = PlanPresenter()


def create_plan(plan_id: str, title: str, description: str,
               tasks: List[str], context: Dict = None) -> Dict:
    """Helper para crear un plan"""
    plan = plan_presenter.create_plan(plan_id, title, description, tasks, context)
    return plan.to_dict()


def format_plan(plan_id: str, compact: bool = False) -> str:
    """Helper para formatear un plan"""
    plan = plan_presenter.get_plan(plan_id)
    if not plan:
        return "Plan no encontrado"
    
    if compact:
        return plan_presenter.format_plan_compact(plan)
    return plan_presenter.format_plan_visual(plan)
