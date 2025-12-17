"""
BUNK3R AI - Test Configuration
Fixtures and mocks for testing the AI Constructor system
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@pytest.fixture
def mock_ai_response():
    """Mock response from AI provider"""
    return {
        "success": True,
        "response": "Test response from AI",
        "provider": "mock_provider",
        "tokens_used": 100
    }


@pytest.fixture
def mock_ai_service(mock_ai_response):
    """Mock AIService for testing without API calls"""
    service = Mock()
    service.chat.return_value = mock_ai_response
    service.get_available_providers.return_value = ["deepseek", "groq", "gemini"]
    return service


@pytest.fixture
def sample_user_request():
    """Sample user request for testing"""
    return "Crea una landing page para un restaurante mexicano con menú, reservas y fotos"


@pytest.fixture
def sample_intent_data():
    """Sample intent analysis data"""
    return {
        "tipo_tarea": "crear_landing",
        "contexto": "restaurante",
        "lenguaje": "html_css_js",
        "nivel_detalle": "alto",
        "requiere_clarificacion": False,
        "keywords": ["landing", "restaurante", "mexicano", "menú", "reservas"],
        "urgencia": "media",
        "resumen": "Crear landing page para restaurante mexicano"
    }


@pytest.fixture
def sample_research_data():
    """Sample research result data"""
    return {
        "mejores_practicas": ["Diseño responsive", "Imágenes de alta calidad"],
        "estructura_archivos": ["index.html", "styles.css", "script.js"],
        "componentes": ["Header", "Menu", "Reservas", "Footer"],
        "paleta_colores": ["#D4A574", "#2C1810", "#F5E6D3"],
        "estilo_sugerido": "Cálido y mexicano tradicional",
        "dependencias": [],
        "patrones": ["Single Page App", "Mobile First"],
        "seguridad": ["HTTPS", "Form validation"],
        "tiempo_estimado_minutos": 60,
        "complejidad": "media"
    }


@pytest.fixture
def sample_plan_data():
    """Sample execution plan data"""
    return {
        "titulo_plan": "Landing Page Restaurante Mexicano",
        "descripcion": "Crear landing page completa",
        "tareas": [
            {
                "id": "task_1",
                "titulo": "Crear estructura HTML",
                "descripcion": "Crear archivo index.html con estructura base",
                "tiempo_minutos": 15,
                "archivos": ["index.html"],
                "dependencias": [],
                "complejidad": "simple"
            },
            {
                "id": "task_2",
                "titulo": "Añadir estilos CSS",
                "descripcion": "Crear styles.css con diseño mexicano",
                "tiempo_minutos": 20,
                "archivos": ["styles.css"],
                "dependencias": ["task_1"],
                "complejidad": "media"
            }
        ],
        "tiempo_total_minutos": 35,
        "riesgos": [],
        "dependencias_npm_pip": []
    }


@pytest.fixture
def sample_python_code():
    """Sample Python code for verification"""
    return '''
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/reservas', methods=['POST'])
def crear_reserva():
    data = request.json
    return {"success": True, "reserva_id": 123}

if __name__ == '__main__':
    app.run(debug=True)
'''


@pytest.fixture
def sample_html_code():
    """Sample HTML code for verification"""
    return '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Restaurante Mexicano</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <h1>Bienvenidos a La Casa Mexicana</h1>
        <nav>
            <a href="#menu">Menú</a>
            <a href="#reservas">Reservas</a>
        </nav>
    </header>
    <main>
        <section id="menu">
            <h2>Nuestro Menú</h2>
        </section>
        <section id="reservas">
            <h2>Reservaciones</h2>
        </section>
    </main>
    <footer>
        <p>© 2024 La Casa Mexicana</p>
    </footer>
</body>
</html>'''


@pytest.fixture
def sample_css_code():
    """Sample CSS code for verification"""
    return '''
body {
    font-family: 'Georgia', serif;
    margin: 0;
    padding: 0;
    background-color: #F5E6D3;
    color: #2C1810;
}

header {
    background-color: #D4A574;
    padding: 20px;
    text-align: center;
}

nav a {
    color: #2C1810;
    text-decoration: none;
    margin: 0 15px;
}

main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 40px 20px;
}

section {
    margin-bottom: 40px;
}

footer {
    background-color: #2C1810;
    color: #F5E6D3;
    text-align: center;
    padding: 20px;
}
'''


@pytest.fixture
def sample_javascript_code():
    """Sample JavaScript code for verification"""
    return '''
const form = document.getElementById('reserva-form');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    try {
        const response = await fetch('/api/reservas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Reserva confirmada!');
        }
    } catch (error) {
        console.error('Error:', error);
    }
});
'''


@pytest.fixture
def sample_invalid_python():
    """Sample invalid Python code"""
    return '''
def broken_function(
    return "missing closing paren"
'''


@pytest.fixture
def sample_incomplete_code():
    """Sample incomplete code with TODOs"""
    return '''
def process_data(data):
    # TODO: Implement this function
    ...
    
def another_function():
    raise NotImplementedError("not implemented yet")
'''


@pytest.fixture
def sample_json_code():
    """Sample JSON for verification"""
    return '{"name": "Test", "version": "1.0.0", "dependencies": {}}'


@pytest.fixture
def sample_invalid_json():
    """Sample invalid JSON"""
    return '{"name": "Test", version: "1.0.0"}'


@pytest.fixture
def mock_retry_result():
    """Mock retry result"""
    from BUNK3R_IA.core.smart_retry import RetryResult, RetryAttempt
    from datetime import datetime
    
    return RetryResult(
        success=True,
        result={"response": "test"},
        total_attempts=1,
        attempts=[
            RetryAttempt(
                attempt_number=1,
                timestamp=datetime.now(),
                provider="mock",
                success=True,
                error=None,
                duration_ms=100,
                retry_reason=None
            )
        ],
        final_provider="mock",
        total_duration_ms=100
    )
