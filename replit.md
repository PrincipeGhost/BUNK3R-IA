# BUNK3R_IA - AI System

## Overview
BUNK3R_IA is an advanced AI system for code generation and development assistance. It provides a Flask-based API server with multiple AI provider support.

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
├── docs/                # Documentation
├── frontend/            # Frontend assets
└── prompts/             # AI prompts
```

## Running the Project
The server runs on port 5000 via the BUNK3R_IA Server workflow.

## API Endpoints
- GET `/` - Service info
- GET `/status` - AI service status
- POST `/api/ai/chat` - Chat with AI
- GET `/api/ai/history` - Chat history
- POST `/api/ai-constructor/process` - 8-phase constructor
- POST `/api/ai-toolkit/*` - File operations

## Environment Variables
- `DATABASE_URL` - PostgreSQL connection (optional, uses Replit DB)
- `DEEPSEEK_API_KEY` - DeepSeek API key
- `GROQ_API_KEY` - Groq API key
- `GEMINI_API_KEY` - Google Gemini API key

## Recent Changes
- 2025-12-15: Initial Replit setup, configured port 5000
