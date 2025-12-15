# PROMPT MAESTRO - BUNK3R_IA
## Sistema de Inteligencia Artificial

╔══════════════════════════════════════════════════════════════════╗
║                    BUNK3R_IA - ESTADO ACTUAL                     ║
╠══════════════════════════════════════════════════════════════════╣
║ Ultima actualizacion: 8 Diciembre 2025                           ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║ COMPLETADAS:                                                     ║
║    34.1 Frontend IA conectado con 8 fases                        ║
║    34.2 AIService multi-proveedor con fallback                   ║
║    34.6 AIToolkit (archivos, comandos, errores)                  ║
║    34.9 Sistema de 8 fases del Constructor                       ║
║    34.10 IntentParser - Analisis de solicitudes                  ║
║    34.11 ResearchEngine - Investigacion de contexto              ║
║    34.12 PromptBuilder - Construccion de prompts                 ║
║    34.13 TaskOrchestrator - Orquestacion de tareas               ║
║    34.14 DeliveryManager - Entrega de resultados                 ║
║    34.16 Motor de Decisiones Automatico (AIDecisionEngine)       ║
║    34.18 Contexto de Proyecto Persistente (AIProjectContext)     ║
║    34.20 Sistema de Rollback (RollbackManager)                   ║
║    34.21 Analizador de Impacto (ChangeImpactAnalyzer)            ║
║    34.22 Gestor de Workflows (WorkflowManager)                   ║
║    34.23 Gestor de Tareas (TaskManager)                          ║
║                                                                  ║
║ PENDIENTES CRITICOS:                                             ║
║    34.3 ClarificationManager - Preguntas inteligentes            ║
║    34.4 PlanPresenter - Presentacion de planes                   ║
║    34.5 OutputVerifier - Verificacion de codigo                  ║
║    34.7 Integracion real con LLM en todas las fases              ║
║    34.8 Tests automatizados del Constructor                      ║
║    34.15 Sistema de streaming de respuestas                      ║
║    34.17 Sistema de Reintentos Inteligente                       ║
║    34.19 Validador Pre-Ejecucion completo                        ║
║                                                                  ║
║ COMPONENTES AVANZADOS (34.A - 34.H): ~169 horas                  ║
║    34.A Busqueda en Vivo (Serper + Playwright)                   ║
║    34.B Memoria Vectorial (ChromaDB + Embeddings)                ║
║    34.C Analisis AST + Grafos de Dependencias                    ║
║    34.D Validacion, Testing y Seguridad                          ║
║    34.E Ejecucion Inteligente + Process Manager                  ║
║    34.F Progress Streaming + Diff Previewer                      ║
║    34.G Self-Healing Loop + Agentes Encadenados                  ║
║    34.H Git Avanzado + Template Manager                          ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║                        COMANDOS DISPONIBLES                      ║
╠══════════════════════════════════════════════════════════════════╣
║  1  STATUS       -> Ver este tablero actualizado                 ║
║  2  CONTINUAR    -> Retomar siguiente tarea pendiente            ║
║  3  CORE         -> Trabajar en modulos core de IA               ║
║  4  API          -> Trabajar en rutas y endpoints                ║
║  5  TOOLKIT      -> Trabajar en herramientas de IA               ║
║  6  AVANZADO     -> Trabajar en componentes avanzados            ║
║  7  TESTS        -> Crear/ejecutar tests                         ║
║  8  DOCS         -> Actualizar documentacion                     ║
╚══════════════════════════════════════════════════════════════════╝

---

## ESTRUCTURA DEL PROYECTO

```
BUNK3R_IA/
├── __init__.py              # Exports principales
├── main.py                  # Servidor independiente (puerto 5001)
├── config.py                # Configuraciones
├── requirements.txt         # Dependencias
├── api/
│   └── routes.py            # Todas las rutas API
├── core/
│   ├── ai_service.py        # Servicio multi-proveedor
│   ├── ai_constructor.py    # Constructor de 8 fases
│   ├── ai_core_engine.py    # Motor de decisiones
│   ├── ai_toolkit.py        # Herramientas
│   ├── ai_flow_logger.py    # Sistema de logging
│   └── ai_project_context.py
├── docs/                    # Documentacion
├── frontend/                # ai-chat.js, ai-chat.css
└── prompts/                 # Prompts del sistema
```

---

## SECCION 34: FASES BASE DEL CONSTRUCTOR

### 34.1 - Frontend IA Conectado [COMPLETADO]
- [x] Chat de IA en frontend con 8 fases
- [x] Visualizacion de progreso por fase
- [x] Preview de archivos generados
- [x] Descarga de proyectos como ZIP

### 34.2 - AIService Multi-Proveedor [COMPLETADO]
- [x] Soporte DeepSeek V3.2 (principal)
- [x] Soporte Groq (Llama 3)
- [x] Soporte Google Gemini
- [x] Soporte Cerebras
- [x] Soporte Hugging Face
- [x] Fallback automatico entre proveedores
- [x] Historial de conversacion por usuario

### 34.3 - ClarificationManager [PENDIENTE] [3h]
- [ ] Deteccion de solicitudes ambiguas
- [ ] Generacion de preguntas clarificadoras
- [ ] Priorizacion de preguntas (max 3)
- [ ] Integracion con flujo de 8 fases
- [ ] Persistencia de respuestas

### 34.4 - PlanPresenter [PENDIENTE] [2h]
- [ ] Formato visual de planes
- [ ] Estimacion de tiempo por tarea
- [ ] Arbol de dependencias
- [ ] Confirmacion interactiva
- [ ] Modificacion de plan por usuario

### 34.5 - OutputVerifier [PENDIENTE] [4h]
- [ ] Validacion de sintaxis por lenguaje
- [ ] Verificacion de imports
- [ ] Deteccion de codigo incompleto
- [ ] Score de calidad 0-100
- [ ] Sugerencias de mejora automaticas

### 34.6 - AIToolkit [COMPLETADO]
- [x] AIFileToolkit - Operaciones de archivos
- [x] AICommandExecutor - Ejecucion de comandos
- [x] AIErrorDetector - Deteccion de errores
- [x] AIProjectAnalyzer - Analisis de proyecto
- [x] Whitelist de paquetes
- [x] Proteccion de rutas sensibles

### 34.7 - Integracion LLM en Todas las Fases [PENDIENTE] [8h]
- [ ] Fase 1: LLM para analisis de intent
- [ ] Fase 2: LLM para investigacion
- [ ] Fase 3: LLM para clarificacion
- [ ] Fase 4: LLM para construccion de prompt
- [ ] Fase 5: LLM para presentacion de plan
- [ ] Fase 6: LLM para generacion de codigo
- [ ] Fase 7: LLM para verificacion
- [ ] Fase 8: LLM para entrega final

### 34.8 - Tests del Constructor [PENDIENTE] [4h]
- [ ] Tests unitarios de cada fase
- [ ] Tests de integracion end-to-end
- [ ] Mocking de proveedores de IA
- [ ] Cobertura minima 80%
- [ ] CI/CD integration

---

## SECCION 34.16-34.23: FASES NUCLEO IA

### 34.16 - Motor de Decisiones Automatico [COMPLETADO]
- [x] AIDecisionEngine con patrones de intent
- [x] Clasificacion: CREATE, MODIFY, DEBUG, EXPLAIN, DEPLOY
- [x] Workflows predefinidos por tipo de intent
- [x] Confianza de clasificacion

### 34.17 - Sistema de Reintentos Inteligente [PENDIENTE] [3h]
- [ ] Retry con backoff exponencial
- [ ] Cambio automatico de proveedor en fallo
- [ ] Limite de reintentos configurable
- [ ] Logging de fallos
- [ ] Notificacion al usuario

### 34.18 - Contexto de Proyecto Persistente [COMPLETADO]
- [x] AIProjectContext por usuario
- [x] Tracking de archivos creados/modificados
- [x] Historial de comandos ejecutados
- [x] Errores encontrados y solucionados
- [x] Serializacion para persistencia

### 34.19 - Validador Pre-Ejecucion [PARCIAL] [3h]
- [x] PreExecutionValidator base
- [ ] Verificacion de sintaxis antes de escribir
- [ ] Verificacion de dependencias
- [ ] Verificacion de permisos
- [ ] Alerta de cambios destructivos

### 34.20 - Sistema de Rollback Automatico [COMPLETADO]
- [x] RollbackManager con checkpoints
- [x] Guardado de archivos antes de cambios
- [x] Restauracion a cualquier checkpoint
- [x] Limpieza de checkpoints antiguos

### 34.21 - Analizador de Impacto de Cambios [COMPLETADO]
- [x] ChangeImpactAnalyzer
- [x] Deteccion de importadores
- [x] Analisis de usages
- [x] Nivel de riesgo (low/medium/high)
- [x] Deteccion de breaking changes

### 34.22 - Gestor de Workflows [COMPLETADO]
- [x] WorkflowManager
- [x] Estado de workflows
- [x] Health check de servidores
- [x] Integracion con Process Manager

### 34.23 - Gestor de Tareas con Tracking [COMPLETADO]
- [x] TaskManager con session_id
- [x] Estados: pending, in_progress, completed, failed
- [x] Progreso visible para usuario
- [x] Estimacion de tiempo restante

---

## SECCION 34.A-H: COMPONENTES AVANZADOS

### 34.A - Busqueda en Vivo [PENDIENTE] [10h]

#### 34.A.1 - Web Search (Serper API) [4h]
- [ ] Integracion Serper API
- [ ] Cache de resultados 24h
- [ ] Filtros por tipo (docs, tutorials, stackoverflow)
- [ ] Extraccion de snippets relevantes
- [ ] Rate limiting

#### 34.A.2 - Web Scraping (Playwright) [6h]
- [ ] Instalacion Playwright
- [ ] Scraper de documentacion
- [ ] Extractor de ejemplos de codigo
- [ ] Manejo de SPAs
- [ ] Sandbox de seguridad

---

### 34.B - Memoria y Contexto [PENDIENTE] [21h]

#### 34.B.1 - Memoria Vectorial (ChromaDB) [8h]
- [ ] Instalacion ChromaDB
- [ ] Modelo de embeddings
- [ ] Indexacion del codebase
- [ ] Busqueda semantica
- [ ] Actualizacion incremental

#### 34.B.2 - Conversation Memory Manager [4h]
- [ ] Almacenamiento de historial
- [ ] Resumen automatico de conversaciones
- [ ] Extraccion de decisiones
- [ ] Contexto persistente entre sesiones

#### 34.B.3 - Project State Snapshots [4h]
- [ ] Checkpoints automaticos
- [ ] Comparacion entre snapshots
- [ ] Rollback a cualquier punto
- [ ] Limpieza automatica

#### 34.B.4 - User Preference Learning [5h]
- [ ] Deteccion de estilo de codigo
- [ ] Aprendizaje de naming conventions
- [ ] Preferencias de frameworks
- [ ] Idioma preferido

---

### 34.C - Analisis Profundo de Codigo [PENDIENTE] [22h]

#### 34.C.1 - AST Parser [6h]
- [ ] Parser Python (ast module)
- [ ] Parser JavaScript (acorn/babel)
- [ ] Extraccion de funciones/clases
- [ ] Modificacion quirurgica

#### 34.C.2 - Dependency Graph Analyzer [5h]
- [ ] Mapeo de imports
- [ ] Grafo de dependencias
- [ ] Deteccion de ciclos
- [ ] Impacto de cambios

#### 34.C.3 - Type Inference Engine [6h]
- [ ] Inferencia de tipos Python
- [ ] Inferencia de tipos JavaScript
- [ ] Deteccion de type mismatches

#### 34.C.4 - LSP Integration [5h]
- [ ] Conexion con Language Server
- [ ] Autocompletado inteligente
- [ ] Go to definition
- [ ] Find references

---

### 34.D - Validacion y Testing [PENDIENTE] [25h]

#### 34.D.1 - Screenshot Testing [4h]
- [ ] Captura automatica de screenshots
- [ ] Comparacion visual
- [ ] Deteccion de regresiones UI

#### 34.D.2 - Test Runner Integration [4h]
- [ ] Deteccion de framework de tests
- [ ] Ejecucion (pytest, jest)
- [ ] Parsing de resultados
- [ ] Generacion de tests basicos

#### 34.D.3 - Code Quality Scorer [4h]
- [ ] Complejidad ciclomatica
- [ ] Score de legibilidad
- [ ] Deteccion de code smells
- [ ] Puntuacion 0-100

#### 34.D.4 - Security Scanner [5h]
- [ ] Deteccion SQL injection
- [ ] Deteccion XSS
- [ ] Secrets expuestos
- [ ] Dependencias vulnerables

#### 34.D.5 - Breaking Change Detector [5h]
- [ ] Analisis de cambios de API
- [ ] Funciones eliminadas/renombradas
- [ ] Alertas pre-aplicacion

#### 34.D.6 - Accessibility Checker [3h]
- [ ] Validacion WCAG basica
- [ ] Alt text, contraste, headings

---

### 34.E - Ejecucion Inteligente [PENDIENTE] [17h]

#### 34.E.1 - Environment Validator [3h]
- [ ] Verificacion de env vars
- [ ] Chequeo de puertos
- [ ] Validacion de dependencias

#### 34.E.2 - Function Calling Nativo [4h]
- [ ] Definicion de funciones para IA
- [ ] Ejecucion segura
- [ ] Manejo de errores

#### 34.E.3 - Hot Reload Detector [2h]
- [ ] Deteccion de soporte hot reload
- [ ] Trigger automatico

#### 34.E.4 - Process Manager [5h]
- [ ] Control de multiples procesos
- [ ] Health checks periodicos
- [ ] Restart automatico

#### 34.E.5 - Timeout & Recovery Handler [3h]
- [ ] Timeouts configurables
- [ ] Reintentos con backoff
- [ ] Cancelacion graceful

---

### 34.F - Progress Streaming [PENDIENTE] [16h]

#### 34.F.1 - Real-time Progress Streaming [4h]
- [ ] WebSocket connection
- [ ] Eventos por fase
- [ ] Barra de progreso

#### 34.F.2 - Diff Previewer [4h]
- [ ] Visualizacion de cambios
- [ ] Syntax highlighting
- [ ] Aplicar/rechazar por archivo

#### 34.F.3 - Terminal Emulator [5h]
- [ ] PTY virtual
- [ ] Output en tiempo real
- [ ] Input interactivo

#### 34.F.4 - Notification System [3h]
- [ ] Eventos importantes
- [ ] Sonidos opcionales
- [ ] Historial de notificaciones

---

### 34.G - Self-Healing Loop [PENDIENTE] [23h]

#### 34.G.1 - Auto-Fix Loop [6h]
- [ ] Deteccion automatica de errores
- [ ] Generacion de fix
- [ ] Aplicacion y verificacion
- [ ] Limite de intentos

#### 34.G.2 - Chained Agents [6h]
- [ ] Agente Planificador
- [ ] Agente Implementador
- [ ] Agente Verificador
- [ ] Comunicacion entre agentes

#### 34.G.3 - Learning from Mistakes [5h]
- [ ] Registro de errores y soluciones
- [ ] Patrones de errores comunes
- [ ] Evitar repetir errores

#### 34.G.4 - Confidence Scoring [3h]
- [ ] Score por respuesta
- [ ] Umbral minimo para aplicar
- [ ] Solicitar confirmacion si bajo

#### 34.G.5 - Explanation Generator [3h]
- [ ] Explicacion de cada cambio
- [ ] Nivel de detalle configurable
- [ ] Formato markdown

---

### 34.H - Git Avanzado [PENDIENTE] [17h]

#### 34.H.1 - Git Integration [5h]
- [ ] Commits automaticos
- [ ] Mensajes descriptivos
- [ ] Branch management
- [ ] Stash/unstash

#### 34.H.2 - Merge Conflict Resolver [4h]
- [ ] Deteccion de conflictos
- [ ] Sugerencias de resolucion
- [ ] Aplicacion de fix

#### 34.H.3 - Template Manager [4h]
- [ ] Biblioteca de templates
- [ ] Templates por categoria
- [ ] Personalizacion

#### 34.H.4 - Project Initializer [4h]
- [ ] Deteccion de tipo de proyecto
- [ ] Estructura inicial
- [ ] Archivos de configuracion
- [ ] README automatico

---

## PROVEEDORES DE IA SOPORTADOS

| Proveedor | Modelo | Estado | Prioridad |
|-----------|--------|--------|-----------|
| DeepSeek | V3.2 | ACTIVO | 1 (Principal) |
| Groq | Llama 3 70B | ACTIVO | 2 |
| Google | Gemini Pro | ACTIVO | 3 |
| Cerebras | Llama 3.1 | ACTIVO | 4 |
| Hugging Face | Varios | ACTIVO | 5 |

---

## API ENDPOINTS

| Endpoint | Metodo | Descripcion |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/ai/chat` | POST | Chat con IA |
| `/api/ai/history` | GET | Historial de chat |
| `/api/ai/clear` | POST | Limpiar historial |
| `/api/ai/code-builder` | POST | Generador de codigo |
| `/api/ai-constructor/process` | POST | Constructor 8 fases |
| `/api/ai-constructor/session` | GET | Estado de sesion |
| `/api/ai-constructor/files` | GET | Archivos generados |
| `/api/ai-constructor/confirm` | POST | Confirmar plan |
| `/api/ai-constructor/flow` | GET | Flow log debug |
| `/api/ai-constructor/download-zip` | GET | Descargar ZIP |
| `/api/ai-toolkit/files/*` | POST | Operaciones archivos |
| `/api/ai-toolkit/command/*` | POST | Ejecutar comandos |
| `/api/ai-toolkit/errors/*` | POST | Deteccion errores |
| `/api/ai-toolkit/project/analyze` | GET | Analizar proyecto |
| `/api/ai-core/process` | POST | Procesar mensaje |
| `/api/ai-core/intent/classify` | POST | Clasificar intent |
| `/api/ai-core/workflow/decide` | POST | Decidir workflow |
| `/api/ai-core/validate` | POST | Validar accion |
| `/api/ai-core/checkpoint/*` | POST/GET | Checkpoints |
| `/api/ai-core/impact/analyze` | POST | Analizar impacto |
| `/api/ai-core/tasks/*` | POST/GET | Gestion de tareas |

---

## VARIABLES DE ENTORNO

| Variable | Descripcion | Requerida |
|----------|-------------|-----------|
| `DATABASE_URL` | URL de PostgreSQL | No |
| `DEEPSEEK_API_KEY` | API Key DeepSeek | Si (principal) |
| `GROQ_API_KEY` | API Key Groq | No |
| `GEMINI_API_KEY` | API Key Gemini | No |
| `HF_TOKEN` | Token Hugging Face | No |
| `CEREBRAS_API_KEY` | API Key Cerebras | No |
| `BUNK3R_IA_PORT` | Puerto servidor | No (default: 5001) |
| `BUNK3R_IA_HOST` | Host servidor | No (default: 0.0.0.0) |

---

## RESUMEN DE HORAS

| Seccion | Completado | Pendiente | Total |
|---------|------------|-----------|-------|
| 34.1-34.8 Base | ~16h | ~21h | 37h |
| 34.16-34.23 Nucleo | ~15h | ~6h | 21h |
| 34.A Busqueda | 0h | 10h | 10h |
| 34.B Memoria | 0h | 21h | 21h |
| 34.C Analisis | 0h | 22h | 22h |
| 34.D Testing | 0h | 25h | 25h |
| 34.E Ejecucion | 0h | 17h | 17h |
| 34.F Streaming | 0h | 16h | 16h |
| 34.G Self-Healing | 0h | 23h | 23h |
| 34.H Git | 0h | 17h | 17h |
| **TOTAL** | **~31h** | **~178h** | **~209h** |

---

## PROXIMOS PASOS RECOMENDADOS

1. **Prioridad Alta**: 34.5 OutputVerifier (verificacion de codigo)
2. **Prioridad Alta**: 34.7 Integracion LLM en todas las fases
3. **Prioridad Media**: 34.B.1 Memoria Vectorial (ChromaDB)
4. **Prioridad Media**: 34.D.4 Security Scanner
5. **Prioridad Baja**: 34.F Progress Streaming

---

## SECCION 35: PREVIEW EN VIVO (ESTILO REPLIT)

### Objetivo Principal
Hacer que cuando el usuario escriba un prompt, la IA genere codigo HTML/CSS/JS y se muestre en vivo en el iframe del preview, exactamente como funciona Replit Agent.

---

### 35.1 - Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FLUJO COMPLETO                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Usuario escribe prompt                                              │
│         │                                                            │
│         ▼                                                            │
│  Frontend (ai-chat.js) ──POST──► /api/ai-constructor/generate       │
│         │                              │                             │
│         │                              ▼                             │
│         │                    OpenAI genera codigo                    │
│         │                              │                             │
│         │                              ▼                             │
│         │                    Backend guarda HTML en                  │
│         │                    generated_projects/{session_id}/        │
│         │                              │                             │
│         │                              ▼                             │
│         │◄─────────── Retorna { preview_url, files }                │
│         │                                                            │
│         ▼                                                            │
│  Frontend actualiza:                                                 │
│    - iframe.src = /preview/{session_id}                             │
│    - URL bar = preview.bunk3r.dev/{session_id}                      │
│    - Chat = "Proyecto generado!"                                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 35.2 - Backend: Generacion de Codigo [4h]

#### Endpoint: POST `/api/ai-constructor/generate`

**Archivo**: `BUNK3R_IA/api/ai_constructor.py`

```python
@bp.route('/generate', methods=['POST'])
def generate_project():
    data = request.json
    prompt = data.get('prompt')
    session_id = data.get('session_id') or str(uuid.uuid4())[:8]
    
    # 1. Llamar a OpenAI para generar codigo
    html_code = generate_with_openai(prompt)
    
    # 2. Guardar en carpeta de sesion
    save_project(session_id, html_code)
    
    # 3. Retornar URL del preview
    return jsonify({
        'success': True,
        'session_id': session_id,
        'preview_url': f'/preview/{session_id}',
        'files': ['index.html']
    })
```

**Prompt del Sistema para OpenAI**:
```
Eres BUNK3R IA, un experto desarrollador web. 
Genera codigo HTML completo basado en la descripcion del usuario.

REGLAS ESTRICTAS:
1. Genera UN SOLO archivo HTML completo y funcional
2. Incluye TODO el CSS dentro de <style> tags en el <head>
3. Incluye TODO el JavaScript dentro de <script> tags antes de </body>
4. El diseno debe ser moderno, profesional y responsive
5. Usa colores oscuros (tema dark) por defecto
6. NO uses librerias externas (no CDN, no imports externos)
7. El codigo debe funcionar SIN conexion a internet

Responde UNICAMENTE con el codigo HTML. Sin explicaciones, sin markdown, sin comentarios fuera del codigo.
```

---

### 35.3 - Backend: Servir Preview [2h]

#### Endpoint: GET `/preview/<session_id>`

**Archivo**: `BUNK3R_IA/api/preview.py`

```python
from flask import Blueprint, Response
import os

bp = Blueprint('preview', __name__)

PROJECTS_DIR = 'BUNK3R_IA/generated_projects'

@bp.route('/preview/<session_id>')
def serve_preview(session_id):
    # Sanitizar session_id para evitar path traversal
    safe_session = ''.join(c for c in session_id if c.isalnum())
    
    file_path = os.path.join(PROJECTS_DIR, safe_session, 'index.html')
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            html_content = f.read()
        
        # Inyectar script para capturar logs
        html_with_console = inject_console_capture(html_content)
        
        return Response(html_with_console, mimetype='text/html')
    else:
        return Response('<h1>Proyecto no encontrado</h1>', status=404)
```

**Estructura de Archivos**:
```
BUNK3R_IA/
├── generated_projects/
│   ├── abc123/
│   │   └── index.html
│   ├── def456/
│   │   └── index.html
│   └── ...
```

---

### 35.4 - Frontend: Conexion Chat → Preview [3h]

**Archivo**: `BUNK3R_IA/static/ai-chat.js`

```javascript
class AIChat {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.previewHistory = [];
        this.historyIndex = -1;
    }
    
    generateSessionId() {
        return Math.random().toString(36).substring(2, 10);
    }
    
    async sendMessage(prompt) {
        // 1. Mostrar mensaje del usuario
        this.addUserMessage(prompt);
        
        // 2. Mostrar indicador de carga
        this.showTypingIndicator();
        
        // 3. Enviar al backend
        const response = await fetch('/api/ai-constructor/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                prompt: prompt,
                session_id: this.sessionId
            })
        });
        
        const data = await response.json();
        
        // 4. Ocultar indicador de carga
        this.hideTypingIndicator();
        
        if (data.success) {
            // 5. Actualizar preview
            this.updatePreview(data.preview_url);
            
            // 6. Actualizar URL bar
            this.updateBrowserUrl(data.preview_url);
            
            // 7. Agregar al historial
            this.previewHistory.push(data.preview_url);
            this.historyIndex = this.previewHistory.length - 1;
            
            // 8. Mostrar mensaje de exito
            this.addAIMessage('He generado tu proyecto. Puedes verlo en el preview.');
        } else {
            this.addAIMessage('Hubo un error generando el proyecto. Intenta de nuevo.');
        }
    }
    
    updatePreview(url) {
        const iframe = document.getElementById('ai-preview-iframe');
        const previewEmpty = document.getElementById('ai-preview-empty');
        
        previewEmpty.classList.add('hidden');
        iframe.classList.remove('hidden');
        iframe.src = url;
    }
    
    updateBrowserUrl(url) {
        const urlInput = document.getElementById('browser-url');
        urlInput.value = 'preview.bunk3r.dev' + url;
    }
}
```

---

### 35.5 - Consola: Captura de Logs [2h]

**Script inyectado en cada preview**:
```javascript
<script>
(function() {
    // Capturar errores globales
    window.onerror = function(msg, url, line, col, error) {
        parent.postMessage({
            type: 'bunk3r-console',
            level: 'error',
            message: msg + ' (linea ' + line + ')'
        }, '*');
        return false;
    };
    
    // Capturar console.log
    const originalLog = console.log;
    console.log = function(...args) {
        parent.postMessage({
            type: 'bunk3r-console',
            level: 'log',
            message: args.map(a => String(a)).join(' ')
        }, '*');
        originalLog.apply(console, args);
    };
    
    // Capturar console.error
    const originalError = console.error;
    console.error = function(...args) {
        parent.postMessage({
            type: 'bunk3r-console',
            level: 'error',
            message: args.map(a => String(a)).join(' ')
        }, '*');
        originalError.apply(console, args);
    };
    
    // Capturar console.warn
    const originalWarn = console.warn;
    console.warn = function(...args) {
        parent.postMessage({
            type: 'bunk3r-console',
            level: 'warn',
            message: args.map(a => String(a)).join(' ')
        }, '*');
        originalWarn.apply(console, args);
    };
})();
</script>
```

**En el frontend principal** (workspace.html):
```javascript
// Escuchar mensajes del iframe
window.addEventListener('message', function(event) {
    if (event.data.type === 'bunk3r-console') {
        addConsoleLog(event.data.level, event.data.message);
    }
});

function addConsoleLog(level, message) {
    const consoleOutput = document.getElementById('ai-console-output');
    const line = document.createElement('div');
    line.className = 'console-line ' + level;
    line.textContent = message;
    consoleOutput.appendChild(line);
    consoleOutput.scrollTop = consoleOutput.scrollHeight;
}
```

---

### 35.6 - Barra de Navegador [1h]

**Funcionalidades**:
```javascript
// Boton Atras
document.getElementById('browser-back').addEventListener('click', function() {
    if (historyIndex > 0) {
        historyIndex--;
        updatePreview(previewHistory[historyIndex]);
    }
});

// Boton Adelante
document.getElementById('browser-forward').addEventListener('click', function() {
    if (historyIndex < previewHistory.length - 1) {
        historyIndex++;
        updatePreview(previewHistory[historyIndex]);
    }
});

// Boton Refresh
document.getElementById('browser-refresh').addEventListener('click', function() {
    const iframe = document.getElementById('ai-preview-iframe');
    iframe.src = iframe.src; // Recargar
});

// Abrir en nueva ventana
document.getElementById('browser-open-external').addEventListener('click', function() {
    const iframe = document.getElementById('ai-preview-iframe');
    if (iframe.src) {
        window.open(iframe.src, '_blank');
    }
});
```

---

### 35.7 - Archivos a Crear/Modificar

| Archivo | Accion | Descripcion |
|---------|--------|-------------|
| `BUNK3R_IA/api/preview.py` | CREAR | Endpoint para servir previews |
| `BUNK3R_IA/api/ai_constructor.py` | MODIFICAR | Agregar endpoint /generate |
| `BUNK3R_IA/main.py` | MODIFICAR | Registrar blueprint preview |
| `BUNK3R_IA/static/ai-chat.js` | MODIFICAR | Conectar chat con preview |
| `BUNK3R_IA/templates/workspace.html` | YA HECHO | UI ya actualizada |
| `BUNK3R_IA/generated_projects/` | CREAR | Carpeta para proyectos |

---

### 35.8 - Dependencias

```python
# requirements.txt - agregar
openai>=1.0.0
```

**Variables de entorno**:
```
OPENAI_API_KEY=sk-...  # Ya configurada
```

---

### 35.9 - Estimacion de Tiempo

| Tarea | Tiempo |
|-------|--------|
| 35.2 Backend generacion | 4h |
| 35.3 Backend servir preview | 2h |
| 35.4 Frontend conexion | 3h |
| 35.5 Consola logs | 2h |
| 35.6 Barra navegador | 1h |
| Testing e integracion | 2h |
| **TOTAL** | **14h** |

---

### 35.10 - Orden de Implementacion

1. Crear `generated_projects/` carpeta
2. Crear `api/preview.py` con endpoint basico
3. Modificar `api/ai_constructor.py` con generacion OpenAI
4. Registrar rutas en `main.py`
5. Actualizar `ai-chat.js` para conectar todo
6. Agregar captura de logs para consola
7. Implementar historial de navegacion
8. Testing completo
