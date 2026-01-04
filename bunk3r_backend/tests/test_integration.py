"""
BUNK3R AI - Integration Tests
End-to-end tests for the AI Constructor system
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from bunk3r_core.ai_constructor import (
    IntentParser, TaskType, ProgrammingLanguage, IntentAnalysis,
    ResearchResult, ExecutionPlan, TaskItem, VerificationResult,
    ConstructorSession
)
from bunk3r_core.smart_retry import SmartRetrySystem, RetryConfig
from bunk3r_core.output_verifier import OutputVerifier, CodeLanguage


class TestConstructorSession:
    """Tests for ConstructorSession dataclass"""
    
    def test_session_creation(self):
        """Test session creation with defaults"""
        session = ConstructorSession(
            session_id="test-123",
            user_id="user-1",
            fase_actual=1
        )
        
        assert session.session_id == "test-123"
        assert session.fase_actual == 1
        assert session.archivos_generados == {}
    
    def test_session_to_dict(self):
        """Test session serialization"""
        session = ConstructorSession(
            session_id="test-123",
            user_id="user-1",
            fase_actual=3
        )
        
        session_dict = session.to_dict()
        
        assert session_dict["session_id"] == "test-123"
        assert session_dict["fase_actual"] == 3
        assert session_dict["fase_nombre"] == "Clarificación"
    
    def test_session_with_intent(self):
        """Test session with intent analysis"""
        parser = IntentParser()
        intent = parser.analyze("Crea una landing page")
        
        session = ConstructorSession(
            session_id="test-456",
            user_id="user-1",
            fase_actual=1,
            intent=intent
        )
        
        session_dict = session.to_dict()
        
        assert session_dict["intent"] is not None
        assert "tipo_tarea" in session_dict["intent"]


class TestIntentToResearch:
    """Tests for Intent to Research flow"""
    
    def test_intent_provides_research_direction(self):
        """Test that intent analysis provides direction for research"""
        parser = IntentParser()
        intent = parser.analyze("Crea una landing page para un restaurante mexicano con menú y reservas")
        
        assert intent.tipo_tarea == TaskType.CREAR_LANDING
        assert intent.contexto == "restaurante"
        assert any("restaurante" in kw.lower() or "menú" in kw.lower() 
                  for kw in intent.keywords)


class TestResearchToExecution:
    """Tests for Research to Execution flow"""
    
    def test_research_result_structure(self, sample_research_data):
        """Test research result can be used for execution planning"""
        research = ResearchResult(
            referencias=["https://example.com"],
            elementos_recomendados=sample_research_data["componentes"],
            paleta_sugerida=sample_research_data["paleta_colores"],
            estilo=sample_research_data["estilo_sugerido"],
            insights="Restaurant landing needs images and reservations",
            mejores_practicas=sample_research_data["mejores_practicas"]
        )
        
        result_dict = research.to_dict()
        
        assert len(result_dict["elementos_recomendados"]) > 0
        assert len(result_dict["paleta_sugerida"]) > 0


class TestExecutionPlan:
    """Tests for ExecutionPlan"""
    
    def test_execution_plan_creation(self):
        """Test execution plan creation"""
        tasks = [
            TaskItem(id=1, descripcion="Create HTML", estado="pendiente", archivo_destino="index.html"),
            TaskItem(id=2, descripcion="Create CSS", estado="pendiente", archivo_destino="styles.css"),
        ]
        
        plan = ExecutionPlan(
            tareas=tasks,
            tiempo_estimado="30 minutos",
            riesgos=["Browser compatibility"],
            archivos_a_crear=["index.html", "styles.css"],
            dependencias=[]
        )
        
        plan_dict = plan.to_dict()
        
        assert len(plan_dict["tareas"]) == 2
        assert "index.html" in plan_dict["archivos_a_crear"]
    
    def test_task_item_progression(self):
        """Test task item state progression"""
        task = TaskItem(id=1, descripcion="Test task", estado="pendiente")
        
        assert task.estado == "pendiente"
        
        task.estado = "en_progreso"
        assert task.estado == "en_progreso"
        
        task.estado = "completada"
        task.codigo_generado = "<html></html>"
        assert task.estado == "completada"
        assert task.codigo_generado is not None


class TestVerificationFlow:
    """Tests for code verification flow"""
    
    def test_verification_of_generated_code(self, sample_html_code, sample_css_code):
        """Test verification of generated code files"""
        verifier = OutputVerifier()
        
        html_report = verifier.verify(sample_html_code, "index.html")
        css_report = verifier.verify(sample_css_code, "styles.css")
        
        assert html_report.language == "html"
        assert css_report.language == "css"
        
        assert html_report.syntax_valid == True
        assert css_report.syntax_valid == True
    
    def test_verification_result_to_session(self, sample_python_code):
        """Test verification result can be stored in session"""
        verifier = OutputVerifier()
        report = verifier.verify(sample_python_code, "app.py")
        
        verification = VerificationResult(
            sintaxis_valida=report.syntax_valid,
            completitud=report.completeness_score >= 80,
            funcionalidad=True,
            responsive=True,
            coincide_requisitos=True,
            errores=report.errors,
            advertencias=report.warnings,
            puntuacion=report.quality_score
        )
        
        session = ConstructorSession(
            session_id="test-verify",
            user_id="user-1",
            fase_actual=7,
            verification=verification
        )
        
        session_dict = session.to_dict()
        
        assert session_dict["verification"]["sintaxis_valida"] == True


class TestRetryWithVerification:
    """Tests for retry system with verification"""
    
    def test_retry_on_verification_failure(self):
        """Test that verification failures can trigger retries"""
        verifier = OutputVerifier()
        retry_system = SmartRetrySystem(RetryConfig(
            max_attempts=3,
            base_delay_seconds=0.01
        ))
        
        attempt_count = {"count": 0}
        
        def generate_code(provider=None):
            attempt_count["count"] += 1
            if attempt_count["count"] < 2:
                return {
                    "success": True,
                    "code": "def broken_func("
                }
            return {
                "success": True,
                "code": "def working_func(): pass"
            }
        
        def verify_and_check(provider=None):
            result = generate_code(provider)
            report = verifier.verify(result["code"], "test.py")
            if not report.syntax_valid:
                return {"success": False, "error": "Syntax error"}
            return {"success": True, "code": result["code"]}
        
        result = retry_system.execute_with_retry(
            verify_and_check,
            providers=["default"]
        )
        
        assert result.success == True
        assert attempt_count["count"] == 2


class TestFullConstructorFlow:
    """Tests for complete constructor flow"""
    
    def test_complete_session_flow(self):
        """Test complete session from intent to delivery"""
        parser = IntentParser()
        verifier = OutputVerifier()
        
        session = ConstructorSession(
            session_id="full-test",
            user_id="user-1",
            fase_actual=1
        )
        
        session.intent = parser.analyze("Crea una landing page para restaurante")
        session.fase_actual = 2
        
        session.research = ResearchResult(
            referencias=["https://example.com"],
            elementos_recomendados=["header", "menu", "footer"],
            paleta_sugerida=["#D4A574", "#2C1810"],
            estilo="Mexican restaurant",
            insights="Focus on food imagery",
            mejores_practicas=["Mobile first"]
        )
        session.fase_actual = 3
        
        tasks = [
            TaskItem(id=1, descripcion="Create HTML", estado="pendiente", archivo_destino="index.html"),
            TaskItem(id=2, descripcion="Create CSS", estado="pendiente", archivo_destino="styles.css")
        ]
        session.plan = ExecutionPlan(
            tareas=tasks,
            tiempo_estimado="30 min",
            riesgos=[],
            archivos_a_crear=["index.html", "styles.css"],
            dependencias=[]
        )
        session.fase_actual = 5
        
        html_code = """<!DOCTYPE html>
<html lang="es">
<head><title>Restaurante</title></head>
<body><h1>Bienvenidos</h1></body>
</html>"""
        
        session.archivos_generados["index.html"] = html_code
        session.plan.tareas[0].estado = "completada"
        session.plan.tareas[0].codigo_generado = html_code
        session.fase_actual = 6
        
        report = verifier.verify(html_code, "index.html")
        session.verification = VerificationResult(
            sintaxis_valida=report.syntax_valid,
            completitud=True,
            funcionalidad=True,
            responsive=False,
            coincide_requisitos=True,
            errores=[],
            advertencias=report.warnings,
            puntuacion=report.quality_score
        )
        session.fase_actual = 7
        
        session.fase_actual = 8
        
        session_dict = session.to_dict()
        
        assert session_dict["fase_actual"] == 8
        assert session_dict["fase_nombre"] == "Entrega"
        assert len(session_dict["archivos_generados"]) > 0
        assert session_dict["verification"]["sintaxis_valida"] == True


class TestMultiLanguageSupport:
    """Tests for multi-language code generation"""
    
    def test_python_flask_generation_verification(self, sample_python_code):
        """Test Python Flask code verification"""
        verifier = OutputVerifier()
        report = verifier.verify(sample_python_code, "app.py")
        
        assert report.language == "python"
        assert report.syntax_valid == True
    
    def test_html_generation_verification(self, sample_html_code):
        """Test HTML code verification"""
        verifier = OutputVerifier()
        report = verifier.verify(sample_html_code, "index.html")
        
        assert report.language == "html"
        assert report.is_valid == True
    
    def test_css_generation_verification(self, sample_css_code):
        """Test CSS code verification"""
        verifier = OutputVerifier()
        report = verifier.verify(sample_css_code, "styles.css")
        
        assert report.language == "css"
        assert report.syntax_valid == True
    
    def test_javascript_generation_verification(self, sample_javascript_code):
        """Test JavaScript code verification"""
        verifier = OutputVerifier()
        report = verifier.verify(sample_javascript_code, "script.js")
        
        assert report.language == "javascript"
        assert report.syntax_valid == True


class TestEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_empty_user_request(self):
        """Test handling of empty user request"""
        parser = IntentParser()
        result = parser.analyze("")
        
        assert result.tipo_tarea == TaskType.CONSULTA_GENERAL
        assert result.nivel_detalle in ["bajo", "vago"]
    
    def test_very_long_request(self):
        """Test handling of very long user request"""
        parser = IntentParser()
        long_request = "Crea una landing page " * 100
        
        result = parser.analyze(long_request)
        
        assert result is not None
        assert isinstance(result.tipo_tarea, TaskType)
    
    def test_special_characters_in_request(self):
        """Test handling of special characters"""
        parser = IntentParser()
        request = "Crea una web con €, £, ¥ y símbolos especiales: @#$%^&*()"
        
        result = parser.analyze(request)
        
        assert result is not None
    
    def test_empty_code_verification(self):
        """Test verification of empty code"""
        verifier = OutputVerifier()
        report = verifier.verify("", "empty.py")
        
        assert report is not None
        assert report.completeness_score <= 100
    
    def test_very_large_code_verification(self):
        """Test verification of large code file"""
        verifier = OutputVerifier()
        large_code = "x = 1\n" * 10000
        
        report = verifier.verify(large_code, "large.py")
        
        assert report is not None
        assert report.syntax_valid == True
