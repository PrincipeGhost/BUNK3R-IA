import logging
import hashlib
from datetime import datetime
from backend.models import db, SolutionKnowledge, BugMemory, ArchitectureLog

logger = logging.getLogger(__name__)

class GravityMemory:
    """
    Gestiona la memoria persistente de BUNK3R_IA usando SQLAlchemy.
    Implementa las capas de Verdad Verificada, Conocimiento Tentativo y Rechazado.
    """
    
    @staticmethod
    def _get_hash(text):
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def remember_solution(self, problem_desc, solution_code, tags="", status="verified"):
        """Almacena una solución validada en la capa 1."""
        p_hash = self._get_hash(problem_desc)
        try:
            solution = SolutionKnowledge.query.filter_by(problem_hash=p_hash).first()
            if solution:
                solution.solution_code = solution_code
                solution.tags = tags
                solution.status = status
                solution.last_used = datetime.utcnow()
                solution.success_count += 1
            else:
                solution = SolutionKnowledge(
                    problem_hash=p_hash,
                    problem_desc=problem_desc,
                    solution_code=solution_code,
                    tags=tags,
                    status=status
                )
                db.session.add(solution)
            
            db.session.commit()
            logger.info(f"GravityMemory: Solución recordada [{p_hash[:8]}]")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"GravityMemory Error (remember_solution): {e}")
            return False

    def log_bug(self, error_pattern, error_context, fix_approach="Buscando solución..."):
        """Registra un patrón de error para evitar repetirlo."""
        try:
            bug = BugMemory.query.filter_by(error_pattern=error_pattern).first()
            if bug:
                bug.occurrence_count += 1
                bug.last_seen = datetime.utcnow()
                bug.error_context = error_context
                if fix_approach != "Buscando solución...":
                    bug.fix_approach = fix_approach
            else:
                bug = BugMemory(
                    error_pattern=error_pattern,
                    error_context=error_context,
                    fix_approach=fix_approach
                )
                db.session.add(bug)
            
            db.session.commit()
            logger.info(f"GravityMemory: Error registrado [{error_pattern[:30]}...]")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"GravityMemory Error (log_bug): {e}")
            return False

    def log_decision(self, title, reasoning, alternatives="", impact="medium"):
        """Registra una decisión de arquitectura."""
        try:
            log = ArchitectureLog(
                decision_title=title,
                reasoning=reasoning,
                alternatives=alternatives,
                impact_level=impact
            )
            db.session.add(log)
            db.session.commit()
            logger.info(f"GravityMemory: Decisión registrada [{title}]")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"GravityMemory Error (log_decision): {e}")
            return False

# Instancia global
gravity_memory = GravityMemory()
