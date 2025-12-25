# BUNK3R_IA - AI System

## Overview
BUNK3R_IA is an advanced AI system for code generation and development assistance. It provides a Flask-based API server with a 3-panel workspace interface and multiple AI provider support.

## Project Structure
```
BUNK3R_IA/
├── main.py              # Main Flask server
├── config.py            # Configuration settings
├── requirements.txt     # Python dependencies
├── api/
│   └── routes.py        # All API routes
├── core/
│   ├── ai_service.py        # Multi-provider AI service
│   ├── ai_constructor.py    # 8-phase constructor
│   ├── ai_core_engine.py    # Decision engine
│   ├── ai_toolkit.py        # File and command tools
│   ├── ai_flow_logger.py    # Logging system
│   ├── llm_phase_integrator.py  # LLM integration for 8 phases
│   ├── smart_retry.py       # Intelligent retry system
│   ├── output_verifier.py   # Code verification
│   ├── clarification_manager.py # Clarification questions
│   ├── plan_presenter.py    # Plan presentation
│   └── pre_execution_validator.py # Pre-execution validation
├── templates/
│   └── workspace.html   # Main workspace UI (3 panels)
├── static/
│   ├── ai-chat.js       # Frontend JavaScript
│   └── ai-chat.css      # Frontend styles
├── tests/               # Automated tests (140 tests)
│   ├── conftest.py      # Test fixtures and mocks
│   ├── test_intent_parser.py
│   ├── test_smart_retry.py
│   ├── test_output_verifier.py
│   ├── test_llm_phase_integrator.py
│   └── test_integration.py
├── frontend/            # Source frontend assets
├── docs/                # Documentation
└── prompts/             # AI prompts
```

## Workspace Design (3 Panels)
- **Panel Izquierdo (35%)**: Chat con IA - conversación y fases de construcción
- **Panel Centro**: Vista previa en tiempo real + Editor de código + Consola
- **Panel Derecho (160px)**: Lista de archivos creados por la IA

## Running the Project
The server runs on port 5000 via the BUNK3R_IA Server workflow.

## API Endpoints
- GET `/` - Workspace UI
- GET `/api/info` - Service info
- GET `/status` - AI service status
- POST `/api/ai/chat` - Chat with AI
- GET `/api/ai/history` - Chat history
- POST `/api/ai-constructor/process` - 8-phase constructor
- POST `/api/ai-toolkit/*` - File operations
- POST `/api/ai-llm/phase` - Execute specific LLM phase
- POST `/api/ai-llm/pipeline` - Run full 8-phase pipeline
- POST `/api/ai-llm/execute-plan` - Execute approved plan
- GET `/api/ai-llm/phases` - List available phases

## Environment Variables & AI Providers
Proveedores de IA disponibles (por orden de prioridad):
1. **OpenAI** - `OPENAI_API_KEY` (GPT-4o-mini) ✅ CONFIGURADO
2. **Google Gemini** - `GEMINI_API_KEY` (Gemini 2.0 Flash) ✅ CONFIGURADO  
3. **Baidu** - `BAIDU_API_KEY` (ERNIE 3.5) ✅ CONFIGURADO
4. **Groq** - `GROQ_API_KEY` (Llama 3.3 70B)
5. **Cerebras** - `CEREBRAS_API_KEY` (Llama 3.3 70B)
6. **DeepSeek** - `DEEPSEEK_API_KEY` (DeepSeek Chat)

Otros:
- `DATABASE_URL` - PostgreSQL connection (uses Replit DB)
- `ANTIGRAVITY_BRIDGE_URL` - URL del bridge de Antigravity (Cloudflare Tunnel)

## Antigravity Integration (GRAVITY-CONNECT)
Sistema para usar Google Antigravity como motor principal de IA:
- **Bridge**: Script Python en PC del usuario con OCR (Tesseract + OpenCV)
- **Túnel**: Cloudflare Quick Tunnel (gratis, sin cuenta requerida)
- **Documentación**: Ver `GRAVITY-CONNECT.md` para setup completo
- **Fallback**: Si Antigravity no disponible, usa DeepSeek/Groq/Gemini

## Render Deployment
Files configured for Render deployment:
- `requirements.txt` - Python dependencies (root level)
- `render.yaml` - Render configuration
- `Procfile` - Gunicorn start command
- `runtime.txt` - Python version (3.11.4)

Start command: `gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 "BUNK3R_IA.main:create_app()"`

## Replit Environment
- **Port**: 5000 (frontend and API)
- **Host**: 0.0.0.0 (all interfaces)
- **Workflow**: BUNK3R IA Server (`python -m BUNK3R_IA.main`)
- **Deployment**: Autoscale with Gunicorn

## Recent Changes
- 2025-12-25: Imported to Replit environment
  - Configured workflow for port 5000
  - Set up autoscale deployment with Gunicorn
  - All dependencies installed via pip
- 2025-12-17: Added mobile responsive design
  - Hamburger menu for mobile navigation
  - Chat panel is default view on mobile
  - Switch between Chat, Preview, Files, and Console panels
  - Optimized touch targets and font sizes
- 2025-12-17: Added Render deployment configuration
  - Created requirements.txt, render.yaml, Procfile, runtime.txt
  - Updated README with deployment instructions
- 2025-12-17: Updated GRAVITY-CONNECT v2.0
  - Cambiado ngrok por Cloudflare Tunnel (gratis, sin cuenta)
  - Implementado OCR con Tesseract + OpenCV para extracción de respuestas
  - Calibración automática de ventana
  - Método fallback clipboard si OCR no disponible
- 2025-12-17: Implemented Web Search Service (Section 34.A.1)
  - Created WebSearchService with Serper API integration
  - Added SearchCache with 24h TTL for result caching
  - Added RateLimiter for API call control
  - Implemented ContentFilter (documentation, tutorial, stackoverflow, github)
  - Created 6 API endpoints: /api/ai-search/*
  - Added 43 automated tests for web search functionality
- 2025-12-17: Implemented comprehensive test suite (Section 34.8)
  - 140 automated tests with pytest, pytest-cov, pytest-mock
  - Tests for IntentParser, SmartRetrySystem (96%), OutputVerifier (84%), LLMPhaseIntegrator
  - Integration tests for full 8-phase Constructor flow
  - Multi-language code verification tests (Python, JS, HTML, CSS, JSON)
- 2025-12-17: Implemented LLMPhaseIntegrator (Section 34.7)
  - Created `/api/ai-llm/phase` endpoint for individual phase execution
  - Created `/api/ai-llm/pipeline` endpoint for full 8-phase pipeline
  - Created `/api/ai-llm/execute-plan` endpoint for plan execution
  - Integrated SmartRetry for robust LLM calls with fallback
  - Phase-specific prompts for Intent, Research, Clarification, etc.
  - Updated documentation with corrected component status
- 2025-12-17: Implemented Live Preview System (Section 35)
  - Created `/api/ai-constructor/generate` endpoint for OpenAI HTML generation
  - Added `/preview/<session_id>` route to serve generated previews
  - Implemented `live_preview.py` with fallback system and project management
- 2025-12-15: Created workspace.html with 3-panel layout
- 2025-12-15: Initial Replit setup, configured port 5000
