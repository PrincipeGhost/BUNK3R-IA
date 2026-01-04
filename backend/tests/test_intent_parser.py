"""
BUNK3R AI - Tests for IntentParser (ai_constructor.py)
Tests for Phase 1: Intent Analysis
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.ai_constructor import (
    IntentParser, TaskType, ProgrammingLanguage, IntentAnalysis
)


class TestIntentParser:
    """Tests for IntentParser class"""
    
    @pytest.fixture
    def parser(self):
        return IntentParser()
    
    def test_detect_landing_page_task(self, parser):
        """Test detection of landing page creation task"""
        result = parser.analyze("Quiero una landing page para mi empresa")
        assert result.tipo_tarea == TaskType.CREAR_LANDING
    
    def test_detect_web_task(self, parser):
        """Test detection of website creation task"""
        result = parser.analyze("Necesito un sitio web para vender productos")
        assert result.tipo_tarea in [TaskType.CREAR_WEB, TaskType.CREAR_LANDING]
    
    def test_detect_dashboard_task(self, parser):
        """Test detection of dashboard creation task"""
        result = parser.analyze("Crea un dashboard de administración")
        assert result.tipo_tarea == TaskType.CREAR_DASHBOARD
    
    def test_detect_api_task(self, parser):
        """Test detection of API creation task"""
        result = parser.analyze("Necesito una API REST para usuarios")
        assert result.tipo_tarea == TaskType.CREAR_API
    
    def test_detect_form_task(self, parser):
        """Test detection of form creation task"""
        result = parser.analyze("Crea un formulario de contacto")
        assert result.tipo_tarea == TaskType.CREAR_FORMULARIO
    
    def test_detect_fix_error_task(self, parser):
        """Test detection of error correction task"""
        result = parser.analyze("Hay un error en mi código, no funciona")
        assert result.tipo_tarea == TaskType.CORREGIR_ERROR
    
    def test_detect_install_dependency_task(self, parser):
        """Test detection of dependency installation task"""
        result = parser.analyze("Instala flask y requests")
        assert result.tipo_tarea == TaskType.INSTALAR_DEPENDENCIA
    
    def test_detect_restaurant_context(self, parser):
        """Test detection of restaurant context"""
        result = parser.analyze("Landing page para un restaurante con menú")
        assert result.contexto == "restaurante"
    
    def test_detect_ecommerce_context(self, parser):
        """Test detection of ecommerce context"""
        result = parser.analyze("Tienda online para vender ropa con carrito")
        assert result.contexto == "ecommerce"
    
    def test_detect_portfolio_context(self, parser):
        """Test detection of portfolio context"""
        result = parser.analyze("Portfolio para mostrar mis proyectos de diseño")
        assert result.contexto == "portfolio"
    
    def test_detect_python_flask_language(self, parser):
        """Test detection of Python Flask"""
        result = parser.analyze("Crea una app con Flask y SQLAlchemy")
        assert result.lenguaje_programacion == ProgrammingLanguage.PYTHON_FLASK
    
    def test_detect_react_language(self, parser):
        """Test detection of React"""
        result = parser.analyze("Quiero un componente React con hooks")
        assert result.lenguaje_programacion == ProgrammingLanguage.REACT
    
    def test_detect_html_css_default(self, parser):
        """Test default to HTML/CSS/JS for web requests"""
        result = parser.analyze("Crea una landing page simple")
        assert result.lenguaje_programacion == ProgrammingLanguage.HTML_CSS_JS
    
    def test_extract_keywords(self, parser):
        """Test keyword extraction"""
        result = parser.analyze("Landing page restaurante mexicano con reservas")
        assert len(result.keywords) > 0
        assert any("restaurante" in kw.lower() for kw in result.keywords)
    
    def test_high_detail_level(self, parser):
        """Test high detail level detection"""
        detailed_request = """
        Crea una landing page para restaurante mexicano con:
        - Sección hero con imagen de fondo
        - Menú con precios y fotos
        - Sistema de reservas online
        - Galería de fotos del local
        - Mapa de ubicación
        - Colores: naranja, marrón y beige
        - Tipografía Georgia
        """
        result = parser.analyze(detailed_request)
        assert result.nivel_detalle in ["alto", "medio"]
    
    def test_low_detail_level(self, parser):
        """Test low detail level detection"""
        result = parser.analyze("hazme una web")
        assert result.nivel_detalle in ["bajo", "vago"]
    
    def test_vague_request_low_detail(self, parser):
        """Test that vague requests are detected as low detail"""
        result = parser.analyze("hazme algo bonito")
        assert result.nivel_detalle in ["bajo", "vago"]
    
    def test_detailed_request_has_specs(self, parser):
        """Test that detailed requests extract specifications"""
        result = parser.analyze("Crea una landing page HTML para restaurante italiano con menú y reservas")
        assert len(result.keywords) > 0
        assert "menú" in result.especificaciones_usuario.get("secciones", [])
    
    def test_detect_spanish_language(self, parser):
        """Test Spanish language detection"""
        result = parser.analyze("Quiero una página web para mi negocio")
        assert result.idioma == "es"
    
    def test_intent_analysis_to_dict(self, parser):
        """Test IntentAnalysis serialization"""
        result = parser.analyze("Crea una landing page")
        result_dict = result.to_dict()
        
        assert "tipo_tarea" in result_dict
        assert "contexto" in result_dict
        assert "keywords" in result_dict
        assert "lenguaje_programacion" in result_dict
    
    def test_modification_task(self, parser):
        """Test modification task detection"""
        result = parser.analyze("Modifica el archivo app.py y agrega una ruta")
        assert result.tipo_tarea in [TaskType.MODIFICAR_CODIGO, TaskType.MODIFICAR_ARCHIVO, TaskType.AGREGAR_FUNCIONALIDAD]
    
    def test_read_task(self, parser):
        """Test read/list task detection"""
        result = parser.analyze("lee el archivo main.py")
        assert result.tipo_tarea in [TaskType.LEER_ARCHIVO, TaskType.BUSCAR_CODIGO, TaskType.CONSULTA_GENERAL]
    
    def test_explain_task(self, parser):
        """Test explanation task detection"""
        result = parser.analyze("Explícame cómo funciona este código")
        assert result.tipo_tarea in [TaskType.EXPLICAR, TaskType.EXPLICAR_CODIGO]


class TestTaskType:
    """Tests for TaskType enum"""
    
    def test_creation_tasks_exist(self):
        """Test creation task types exist"""
        assert TaskType.CREAR_WEB
        assert TaskType.CREAR_LANDING
        assert TaskType.CREAR_API
        assert TaskType.CREAR_COMPONENTE
    
    def test_modification_tasks_exist(self):
        """Test modification task types exist"""
        assert TaskType.MODIFICAR_CODIGO
        assert TaskType.AGREGAR_FUNCIONALIDAD
        assert TaskType.QUITAR_ELEMENTO
    
    def test_correction_tasks_exist(self):
        """Test correction task types exist"""
        assert TaskType.CORREGIR_ERROR
        assert TaskType.CORREGIR_SINTAXIS
    
    def test_task_type_values(self):
        """Test TaskType values are strings"""
        assert isinstance(TaskType.CREAR_WEB.value, str)
        assert TaskType.CREAR_WEB.value == "crear_web"


class TestProgrammingLanguage:
    """Tests for ProgrammingLanguage enum"""
    
    def test_languages_exist(self):
        """Test programming languages exist"""
        assert ProgrammingLanguage.HTML_CSS_JS
        assert ProgrammingLanguage.PYTHON_FLASK
        assert ProgrammingLanguage.PYTHON_FASTAPI
        assert ProgrammingLanguage.REACT
        assert ProgrammingLanguage.NODEJS_EXPRESS
    
    def test_language_values(self):
        """Test language values are strings"""
        assert isinstance(ProgrammingLanguage.PYTHON_FLASK.value, str)
        assert ProgrammingLanguage.PYTHON_FLASK.value == "python_flask"
