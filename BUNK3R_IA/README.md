# BUNK3R_IA - Sistema de Inteligencia Artificial

Sistema de IA avanzado para generación de código y asistencia en desarrollo.

## Estructura del Proyecto

```
BUNK3R_IA/
├── __init__.py          # Módulo principal con exports
├── main.py              # Servidor Flask independiente
├── config.py            # Configuraciones
├── requirements.txt     # Dependencias Python
├── api/
│   ├── __init__.py
│   └── routes.py        # Todas las rutas de la API
├── core/
│   ├── __init__.py
│   ├── ai_service.py        # Servicio multi-proveedor de IA
│   ├── ai_constructor.py    # Constructor de 8 fases
│   ├── ai_core_engine.py    # Motor de decisiones y workflows
│   ├── ai_toolkit.py        # Herramientas de archivos y comandos
│   ├── ai_flow_logger.py    # Sistema de logging
│   └── ai_project_context.py # Contexto de proyecto
├── docs/                # Documentación y análisis
├── frontend/            # Archivos frontend (ai-chat.js, ai-chat.css)
└── prompts/             # Prompts del sistema
```

## Instalación

```bash
cd BUNK3R_IA
pip install -r requirements.txt
```

## Uso

### Como servidor independiente

```bash
python -m BUNK3R_IA.main
```

El servidor se iniciará en `http://0.0.0.0:5001`

### Como módulo en otro proyecto

```python
from BUNK3R_IA import AIService, get_ai_service
from BUNK3R_IA import AIConstructorService
from BUNK3R_IA import AICoreOrchestrator

# Usar el servicio de IA
ai_service = get_ai_service(db_manager)
response = ai_service.chat("user_123", "Hola, crea una página web")
```

## Endpoints API

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/ai/chat` | POST | Chat con la IA |
| `/api/ai/history` | GET | Historial de chat |
| `/api/ai/code-builder` | POST | Generador de código |
| `/api/ai-constructor/process` | POST | Constructor de 8 fases |
| `/api/ai-constructor/session` | GET | Estado de sesión |
| `/api/ai-constructor/files` | GET | Archivos generados |
| `/api/ai-toolkit/files/*` | POST | Operaciones de archivos |
| `/api/ai-toolkit/command/*` | POST | Ejecución de comandos |
| `/api/ai-core/process` | POST | Procesamiento de mensajes |
| `/api/ai-core/intent/classify` | POST | Clasificación de intención |

## Variables de Entorno

| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `DATABASE_URL` | URL de PostgreSQL | No |
| `DEEPSEEK_API_KEY` | API Key de DeepSeek | No |
| `GROQ_API_KEY` | API Key de Groq | No |
| `GEMINI_API_KEY` | API Key de Google Gemini | No |
| `HF_TOKEN` | Token de Hugging Face | No |
| `BUNK3R_IA_PORT` | Puerto del servidor (default: 5001) | No |

## Arquitectura de 8 Fases

1. **IntentParser** - Análisis de la solicitud del usuario
2. **ResearchEngine** - Investigación de contexto y mejores prácticas
3. **ClarificationManager** - Preguntas de clarificación si es necesario
4. **PromptBuilder** - Construcción del prompt maestro
5. **PlanPresenter** - Presentación del plan al usuario
6. **TaskOrchestrator** - Orquestación de tareas
7. **OutputVerifier** - Verificación del código generado
8. **DeliveryManager** - Entrega final

## Proveedores de IA Soportados

- DeepSeek V3.2 (principal)
- Groq (Llama 3)
- Google Gemini
- Cerebras
- Hugging Face

El sistema incluye fallback automático entre proveedores.
