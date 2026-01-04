import logging
import hashlib
import traceback
import threading
import time
import ast
import os
from datetime import datetime
from typing import Optional, Dict, List, Any
from flask import request, current_app
from bunk3r_backend.models import db, SolutionKnowledge, BugMemory, ArchitectureLog, ModelBenchmark, UserPreferenceModel, ProjectGraph

logger = logging.getLogger(__name__)

class GravityCore:
    """
    GRAVITY CORE (El Corazón): Unificación de Memoria, Monitoreo y Evolución.
    Consolida:
    - Memoria de Soluciones (Capa 1)
    - Memoria de Errores (Capa 2)
    - Registro de Arquitectura
    - Mapeo de Grafo Estructural (AST)
    - Aprendizaje de Preferencias (Estilo)
    - Ciclo de Sueño (Auto-Fix & Autonomía)
    """

    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Inicializa los ganchos de monitoreo en la aplicación Flask."""
        self.app = app
        @app.errorhandler(500)
        def handle_500_error(e):
            error_trace = traceback.format_exc()
            error_pattern = f"500_ERROR_{request.path}"
            self.log_bug(error_pattern, error_trace, "Activando protocolo de análisis estructural...")
            return {"error": "Gravity Core ha capturado un fallo crítico.", "id": error_pattern}, 500
        logger.info("GravityCore: Ganchos de monitoreo ACTIVADOS.")

    # --- NÚCLEO MNEMÓSINE (MEMORIA) ---

    def remember_solution(self, problem: str, solution: str, tags: str = ""):
        """Capa 1: Conocimiento Verificado."""
        p_hash = hashlib.sha256(problem.encode()).hexdigest()
        try:
            sol = SolutionKnowledge.query.filter_by(problem_hash=p_hash).first()
            if sol:
                sol.solution_code, sol.last_used = solution, datetime.utcnow()
                sol.success_count += 1
            else:
                db.session.add(SolutionKnowledge(
                    problem_hash=p_hash, problem_desc=problem, 
                    solution_code=solution, tags=tags
                ))
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"GravityCore (Memory Error): {e}")
            return False

    def log_bug(self, pattern: str, context: str, fix: str = "Analizando..."):
        """Capa 2: Memoria de Fallos."""
        try:
            bug = BugMemory.query.filter_by(error_pattern=pattern).first()
            if bug:
                bug.occurrence_count += 1
                bug.last_seen = datetime.utcnow()
                bug.error_context = context
            else:
                db.session.add(BugMemory(error_pattern=pattern, error_context=context, fix_approach=fix))
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"GravityCore (Bug Error): {e}")
            return False

    def update_preference(self, key: str, value: Any):
        """Aprendizaje Estilístico del Usuario."""
        try:
            pref = UserPreferenceModel.query.get(key)
            if not pref:
                db.session.add(UserPreferenceModel(key=key, value=value, confidence=0.2))
            else:
                if pref.value == value: pref.confidence = min(1.0, pref.confidence + 0.1)
                else: pref.confidence = max(0.0, pref.confidence - 0.2); pref.value = value if pref.confidence < 0.2 else pref.value
            db.session.commit()
        except Exception as e:
            logger.error(f"GravityCore (Preference Error): {e}")

    # --- NÚCLEO ARGOS (CONCIENCIA ESTRUCTURAL) ---

    def scan_structure(self, root_path: str):
        """Mapea el grafo de dependencias del proyecto."""
        logger.info(f"GravityCore: Escaneando estructura en {root_path}")
        for root, _, files in os.walk(root_path):
            if any(b in root for b in [".git", "__pycache__", "node_modules", "sandbox"]): continue
            for file in files:
                if file.endswith(".py"):
                    self._analyze_file(os.path.join(root, file), root_path)
        db.session.commit()

    def _analyze_file(self, full_path: str, root_path: str):
        try:
            rel_path = os.path.relpath(full_path, root_path)
            with open(full_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            
            imports, exports = [], []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import): imports.extend([n.name for n in node.names])
                elif isinstance(node, ast.ImportFrom): imports.append(f"{node.module}.{node.names[0].name}" if node.module else node.names[0].name)
                elif isinstance(node, (ast.FunctionDef, ast.ClassDef)): exports.append(f"{'func' if isinstance(node, ast.FunctionDef) else 'class'}:{node.name}")
            
            graph = ProjectGraph.query.filter_by(file_path=rel_path).first() or ProjectGraph(file_path=rel_path)
            graph.imports, graph.exports, graph.last_scanned = imports, exports, datetime.utcnow()
            if graph.id is None: db.session.add(graph)
        except Exception as e:
            logger.debug(f"GravityCore (AST Error in {full_path}): {e}")

    # --- NÚCLEO ÉREBO (AUTONOMÍA / SUEÑO) ---

    def start_autonomy(self):
        """Inicia el ciclo de vida autónomo."""
        if not self.app: return
        threading.Thread(target=self._autonomy_loop, daemon=True).start()
        logger.info("GravityCore: Ciclo de Autonomía (Auto-Fix) ACTIVADO.")

    def _autonomy_loop(self):
        with self.app.app_context():
            while True:
                try:
                    self._run_autofix()
                    time.sleep(3600) # Cada hora
                except Exception as e:
                    logger.error(f"GravityCore (Autonomy Loop): {e}")

    def _run_autofix(self):
        """Busca soluciones para bugs registrados sin parche vía Singularidad."""
        try:
            from bunk3r_core.singularity import singularity
            from bunk3r_core.nervous_system import nervous_system
            
            # 1. Identificar bugs críticos sin solución
            open_bugs = BugMemory.query.filter(BugMemory.fix_approach.like('%Analizando%')).all()
            if not open_bugs: return
            
            logger.info(f"GravityCore/Singularity: Analizando {len(open_bugs)} errores en modo Autonómo.")
            
            for bug in open_bugs:
                # 2. ACTIVAR PROTECCIÓN MÁXIMA (Sandbox forzado para autonomía)
                nervous_system.sandbox_mode = True
                logger.info(f"🛡️ GRAVITY PROTECT: MODO SANDBOX ACTIVADO para {bug.error_pattern}")
                
                # 3. Pedir a la Singularidad que resuelva el bug
                prompt = f"MODO AUTÓNOMO: Analiza y propón una solución real para este error registrado:\nPATTERN: {bug.error_pattern}\nCONTEXT: {bug.error_context}"
                
                # Usamos una conversación interna especial
                result = singularity.solve(prompt, "AUTONOMY_CORE", [], "Actúa como el Sistema de Auto-Evolución BUNK3R.")
                
                if result.get("success"):
                    # Registrar el intento en la memoria
                    bug.fix_approach = f"PRÁCTICA EN SANDBOX: {result.get('reflection')}\nSTATUS: Simulado."
                    bug.last_seen = datetime.utcnow()
                
                # 4. Registrar en el Log de Arquitectura
                db.session.add(ArchitectureLog(
                    decision_title=f"Auto-Fix Practice: {bug.error_pattern}",
                    reasoning=f"Reflection: {result.get('reflection')}",
                    impact_level='low' # Low because it's in sandbox
                ))
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"GravityCore (Auto-Fix Cycle Failed): {e}")

# Instancia global del Corazón
gravity_core = GravityCore()
