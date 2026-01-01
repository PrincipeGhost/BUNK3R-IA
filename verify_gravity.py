import os
import sys
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from BUNK3R_IA.main import create_app
from BUNK3R_IA.models import db, SolutionKnowledge, BugMemory, ArchitectureLog
from BUNK3R_IA.core.gravity.memory import gravity_memory

def verify_gravity():
    app = create_app()
    with app.app_context():
        print("--- Verificando BUNK3R_IA Gravity Core ---")
        
        # 1. Verificar creación de tablas
        try:
            db.create_all()
            print("✅ Tablas de Gravity Core verificadas/creadas.")
        except Exception as e:
            print(f"❌ Error al crear tablas: {e}")
            return

        # 2. Probar SolutionKnowledge
        print("\nProbando Capa 1 (SolutionKnowledge)...")
        success = gravity_memory.remember_solution(
            problem_desc="Cómo centrar un div",
            solution_code="display: flex; justify-content: center; align-items: center;",
            tags="css,layout",
            status="verified"
        )
        if success:
            sol = SolutionKnowledge.query.filter_by(problem_desc="Cómo centrar un div").first()
            if sol:
                print(f"✅ Solución guardada: {sol.problem_hash[:8]} | Status: {sol.status}")
            else:
                print("❌ Solución no encontrada en DB.")
        else:
            print("❌ Error al guardar solución.")

        # 3. Probar BugMemory
        print("\nProbando BugMemory...")
        gravity_memory.log_bug(
            error_pattern="DivisionByZero",
            error_context="Traceback: line 10, in main: 1/0",
            fix_approach="Validar que el denominador no sea cero."
        )
        bug = BugMemory.query.filter_by(error_pattern="DivisionByZero").first()
        if bug:
            print(f"✅ Bug registrado. Occurrences: {bug.occurrence_count}")
        else:
            print("❌ Bug no encontrado en DB.")

        # 4. Probar ArchitectureLog
        print("\nProbando ArchitectureLog...")
        gravity_memory.log_decision(
            title="Integración de Gravity Core",
            reasoning="Se integra memoria persistente para mejorar la autonomía de la IA.",
            impact="critical"
        )
        log = ArchitectureLog.query.filter_by(decision_title="Integración de Gravity Core").first()
        if log:
            print(f"✅ Decisión registrada. Impacto: {log.impact_level}")
        else:
            print("❌ Log no encontrado en DB.")

        print("\n--- Verificación Completada ---")

if __name__ == "__main__":
    verify_gravity()
