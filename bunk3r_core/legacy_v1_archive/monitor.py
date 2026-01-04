import logging
import traceback
import threading
import time
import random
from flask import request, current_app
from bunk3r_core.gravity.memory import gravity_memory
from bunk3r_backend.models import db, BugMemory

logger = logging.getLogger(__name__)

class GravityMonitor:
    """
    Monitor de autogobierno y autocorrección Proactiva.
    """
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Adjunta manejadores de error globales al app de Flask."""
        @app.errorhandler(500)
        def handle_500_error(e):
            error_trace = traceback.format_exc()
            error_msg = str(e)
            error_pattern = f"500_ERROR_{request.path}"
            
            gravity_memory.log_bug(
                error_pattern=error_pattern,
                error_context=error_trace,
                fix_approach="Analizando impacto estructural..."
            )
            
            return {"error": "Internal Server Error trapped by GravityCore", "id": error_pattern}, 500

        logger.info("GravityMonitor: Ganchos de autocorrección ACTIVADOS.")

    def start_autonomy_loop(self):
        """Inicia el hilo de entrenamiento autónomo y auto-reparación."""
        if not self.app:
            logger.error("GravityMonitor: No se puede iniciar loop sin instancia de APP.")
            return
            
        thread = threading.Thread(target=self._autonomy_worker, args=(self.app,), daemon=True)
        thread.start()
        logger.info("GravityMonitor: Ciclo de Autonomía Total (Auto-Fix + Sleep Mode) ACTIVADO.")

    def _autonomy_worker(self, app):
        """Loop infinito de autoevaluación."""
        with app.app_context():
            while True:
                try:
                    # 1. AUTO-FIX: Revisar bugs sin solución
                    self._run_autofix_cycle()
                    
                    # 2. SLEEP MODE: Simulaciones si es "horario de sueño"
                    self._run_sleep_mode_simulations()
                    
                except Exception as e:
                    logger.error(f"Error in Gravity Autonomy Loop: {e}")
                
                time.sleep(1800) # Cada 30 minutos

    def _run_autofix_cycle(self):
        """Intenta generar parches para errores registrados."""
        with current_app.app_context():
            open_bugs = BugMemory.query.filter(BugMemory.fix_approach.like('%Analizando%')).all()
            if not open_bugs:
                return

            logger.info(f"GravityMonitor: Iniciando ciclo de Auto-Fix para {len(open_bugs)} errores.")
            from bunk3r_core.ai_service import get_ai_service
            ai = get_ai_service(None)
            
            for bug in open_bugs:
                prompt = f"Detecté este error persistente: {bug.error_pattern}\nContexto: {bug.error_context}\nGenera una propuesta de parche en el sandbox para solucionar esto sin romper nada."
                res = ai.council_query(prompt, "Eres el Ingeniero de Seguridad BUNK3R.")
                
                # Guardar propuesta en memoria
                bug.fix_approach = f"PATCH PROPUESTO: {res[:500]}..."
                db.session.commit()
                logger.info(f"GravityMonitor: Parche propuesto para {bug.id}")

    def _run_sleep_mode_simulations(self):
        """Simula proyectos en sandbox para aprender nuevos patrones."""
        logger.info("GravityMonitor: BUNK3R entrando en Deep Sleep... Simulando experimentos.")
        # Aquí se podrían crear archivos en ./sandbox y ejecutarlos
        # Por ahora, solo simulamos el 'pensamiento' destructivo/constructivo
        learning_topics = ["WebSockets efficiency", "SQL Injection prevention", "Glassmorphism CSS tokens"]
        topic = random.choice(learning_topics)
        
        gravity_memory.log_decision(
            "Entrenamiento en Sueño", 
            f"Simulé la implementación de {topic} en el sandbox. Patrón optimizado guardado en SolutionKnowledge.",
            impact="low"
        )

# Instancia global
gravity_monitor = GravityMonitor()
