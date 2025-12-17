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
│   ├── ai_service.py    # Multi-provider AI service
│   ├── ai_constructor.py# 8-phase constructor
│   ├── ai_core_engine.py# Decision engine
│   ├── ai_toolkit.py    # File and command tools
│   └── ai_flow_logger.py# Logging system
├── templates/
│   └── workspace.html   # Main workspace UI (3 panels)
├── static/
│   ├── ai-chat.js       # Frontend JavaScript
│   └── ai-chat.css      # Frontend styles
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

## Environment Variables
- `DATABASE_URL` - PostgreSQL connection (uses Replit DB)
- `DEEPSEEK_API_KEY` - DeepSeek API key
- `GROQ_API_KEY` - Groq API key
- `GEMINI_API_KEY` - Google Gemini API key

## Recent Changes
- 2025-12-17: Implemented Live Preview System (Section 35)
  - Created `/api/ai-constructor/generate` endpoint for OpenAI HTML generation
  - Added `/preview/<session_id>` route to serve generated previews
  - Implemented `live_preview.py` with fallback system and project management
  - Updated frontend with `generateLivePreview()` and `showLivePreview()` methods
  - Added automatic detection of generation requests in chat
- 2025-12-15: Created workspace.html with 3-panel layout
- 2025-12-15: Cleaned up duplicate files
- 2025-12-15: Initial Replit setup, configured port 5000
