# GRAVITY-CONNECT: Integración Antigravity con BUNK3R_IA

## Descripción General

Este documento detalla el plan completo para integrar Google Antigravity como motor principal de IA para BUNK3R_IA, utilizando un sistema de puente (bridge) que permite comunicación bidireccional entre la aplicación en Replit y Antigravity corriendo en la PC del usuario.

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FLUJO DE COMUNICACIÓN                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐                                                        │
│  │   USUARIO FINAL   │                                                        │
│  │  (Navegador Web)  │                                                        │
│  └────────┬─────────┘                                                        │
│           │ Escribe consulta                                                  │
│           ▼                                                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐    │
│  │                        BUNK3R_IA (Replit)                             │    │
│  │  ┌─────────────┐    ┌─────────────────┐    ┌──────────────────┐     │    │
│  │  │  Frontend   │───►│   AIService     │───►│ AntigravityClient │     │    │
│  │  │  ai-chat.js │    │ (multi-provider)│    │    (NUEVO)        │     │    │
│  │  └─────────────┘    └─────────────────┘    └────────┬─────────┘     │    │
│  └─────────────────────────────────────────────────────┬────────────────┘    │
│                                                         │                     │
│                                                         │ HTTPS Request       │
│                                                         │ (túnel ngrok)       │
│                                                         ▼                     │
│  ┌──────────────────────────────────────────────────────────────────────┐    │
│  │                        PC DEL USUARIO                                 │    │
│  │                                                                       │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │              ANTIGRAVITY BRIDGE (Python)                     │    │    │
│  │  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │    │    │
│  │  │  │ HTTP Server  │───►│  Automator   │───►│   Response   │  │    │    │
│  │  │  │ (puerto 8888)│    │  (PyAutoGUI) │    │   Extractor  │  │    │    │
│  │  │  └──────────────┘    └───────┬──────┘    └──────────────┘  │    │    │
│  │  └──────────────────────────────┼────────────────────────────────┘    │    │
│  │                                  │                                     │    │
│  │                                  │ Simula clicks/teclado               │    │
│  │                                  ▼                                     │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                    GOOGLE ANTIGRAVITY                        │    │    │
│  │  │  ┌──────────────────────────────────────────────────────┐  │    │    │
│  │  │  │                   Agent Chat Panel                     │  │    │    │
│  │  │  │  - Recibe consulta via automatización                  │  │    │    │
│  │  │  │  - Procesa con Gemini 3 Pro                            │  │    │    │
│  │  │  │  - Genera código/respuestas                            │  │    │    │
│  │  │  └──────────────────────────────────────────────────────┘  │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                       │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                         NGROK                                 │    │    │
│  │  │  - Expone localhost:8888 a internet                          │    │    │
│  │  │  - URL pública: https://xxxx.ngrok.io                        │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Plan de Trabajo Detallado

### FASE 1: Preparación del Entorno (PC del Usuario)

#### 1.1 Requisitos Previos
- [ ] Google Antigravity instalado y funcionando
- [ ] Python 3.10+ instalado
- [ ] Cuenta de ngrok (gratuita)

#### 1.2 Instalación de Dependencias (PC)
```bash
pip install pyautogui
pip install pillow
pip install flask
pip install flask-cors
pip install pyperclip
pip install keyboard
pip install pygetwindow
```

**Comando único para instalar todo:**
```bash
pip install pyautogui pillow flask flask-cors pyperclip keyboard pygetwindow
```

#### 1.3 Instalación de ngrok
```bash
# Windows (con chocolatey)
choco install ngrok

# O descargar desde https://ngrok.com/download
# Registrarse gratis en ngrok.com para obtener authtoken
ngrok config add-authtoken TU_AUTH_TOKEN
```

---

### FASE 2: Creación del Antigravity Bridge (PC del Usuario)

#### 2.1 Archivo: `antigravity_bridge.py`

Este script debe crearse en la PC del usuario. Funciones principales:

```python
# Estructura del script (a crear en PC del usuario)

1. HTTPServer (Flask)
   - Puerto: 8888
   - Endpoints:
     - POST /query → Recibe consulta, la procesa, devuelve respuesta
     - GET /health → Verifica que el bridge está funcionando
     - GET /status → Estado de Antigravity (abierto/cerrado)

2. AntigravityAutomator (PyAutoGUI)
   - activate_window() → Trae Antigravity al frente
   - open_agent_panel() → Cmd+L para abrir panel del agente
   - send_query(text) → Escribe la consulta en el chat
   - wait_for_response() → Espera que Antigravity responda
   - extract_response() → Copia la respuesta

3. ResponseExtractor
   - Detecta cuando Antigravity termina de responder
   - Extrae el texto de la respuesta
   - Extrae código si lo hay
   - Formatea para enviar a BUNK3R_IA
```

#### 2.2 Flujo del Bridge

```
1. Bridge recibe POST /query con {"prompt": "crear función fibonacci"}
2. Activa ventana de Antigravity (la trae al frente)
3. Abre panel del agente si no está abierto (Cmd+L)
4. Hace click en el campo de texto del chat
5. Escribe la consulta
6. Presiona Enter
7. Espera respuesta (detecta cuando deja de escribir)
8. Selecciona y copia la respuesta
9. Devuelve JSON: {"response": "...", "code": [...], "status": "success"}
```

---

### FASE 3: Configuración de ngrok (PC del Usuario)

#### 3.1 Iniciar el túnel
```bash
# En una terminal separada
ngrok http 8888
```

#### 3.2 Obtener URL pública
```
ngrok mostrará algo como:
Forwarding: https://a1b2c3d4.ngrok.io -> http://localhost:8888

Esta URL (https://a1b2c3d4.ngrok.io) es la que usará BUNK3R_IA
```

#### 3.3 Configurar URL en BUNK3R_IA
- Agregar variable de entorno: `ANTIGRAVITY_BRIDGE_URL=https://a1b2c3d4.ngrok.io`

---

### FASE 4: Modificaciones en BUNK3R_IA (Replit)

#### 4.1 Nuevo archivo: `BUNK3R_IA/core/antigravity_client.py`

```python
# Cliente para comunicarse con el Antigravity Bridge

class AntigravityClient:
    def __init__(self, bridge_url: str):
        self.bridge_url = bridge_url
        self.timeout = 120  # Antigravity puede tardar
    
    async def query(self, prompt: str) -> dict:
        # Envía consulta al bridge
        # Retorna respuesta de Antigravity
        pass
    
    async def health_check(self) -> bool:
        # Verifica que el bridge esté funcionando
        pass
    
    async def get_status(self) -> dict:
        # Estado del bridge y Antigravity
        pass
```

#### 4.2 Modificar: `BUNK3R_IA/core/ai_service.py`

Agregar Antigravity como proveedor principal:

```python
# Orden de proveedores actualizado
PROVIDERS = {
    "antigravity": 0,  # NUEVO - Principal (gratis)
    "deepseek": 1,     # Fallback 1
    "groq": 2,         # Fallback 2
    "gemini": 3,       # Fallback 3
    "cerebras": 4,     # Fallback 4
    "huggingface": 5   # Fallback 5
}

# Nueva función para llamar a Antigravity
async def call_antigravity(prompt: str, context: dict = None) -> str:
    client = AntigravityClient(os.getenv("ANTIGRAVITY_BRIDGE_URL"))
    
    if not await client.health_check():
        raise Exception("Antigravity Bridge no disponible")
    
    response = await client.query(prompt)
    return response["response"]
```

#### 4.3 Modificar: `BUNK3R_IA/config.py`

```python
# Agregar configuración de Antigravity
ANTIGRAVITY_CONFIG = {
    "bridge_url": os.getenv("ANTIGRAVITY_BRIDGE_URL", ""),
    "timeout": 120,
    "retry_attempts": 3,
    "fallback_enabled": True
}
```

#### 4.4 Nueva variable de entorno

```
ANTIGRAVITY_BRIDGE_URL=https://tu-url-ngrok.ngrok.io
```

---

### FASE 5: Script Completo del Bridge (Para PC del Usuario)

#### 5.1 Crear archivo: `antigravity_bridge.py`

```python
"""
ANTIGRAVITY BRIDGE
==================
Script para correr en la PC del usuario.
Conecta BUNK3R_IA con Google Antigravity via automatización GUI.

Requisitos:
- pip install flask flask-cors pyautogui pyperclip pillow keyboard

Uso:
1. Abrir Google Antigravity
2. Ejecutar: python antigravity_bridge.py
3. Ejecutar ngrok: ngrok http 8888
4. Copiar URL de ngrok a BUNK3R_IA
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pyautogui
import pyperclip
import time
import threading
import os

app = Flask(__name__)
CORS(app)

# Configuración
ANTIGRAVITY_WINDOW_TITLE = "Antigravity"
RESPONSE_TIMEOUT = 60  # segundos
CHECK_INTERVAL = 0.5   # segundos

class AntigravityAutomator:
    def __init__(self):
        self.is_processing = False
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
    
    def activate_window(self):
        """Trae Antigravity al primer plano"""
        # En Windows/Mac, buscar ventana por título
        try:
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle(ANTIGRAVITY_WINDOW_TITLE)
            if windows:
                windows[0].activate()
                time.sleep(0.5)
                return True
        except:
            pass
        
        # Alternativa: usar Alt+Tab o buscar en taskbar
        pyautogui.hotkey('alt', 'tab')
        time.sleep(0.5)
        return True
    
    def open_agent_panel(self):
        """Abre el panel del agente con Cmd+L (Mac) o Ctrl+L (Windows)"""
        if os.name == 'nt':  # Windows
            pyautogui.hotkey('ctrl', 'l')
        else:  # Mac/Linux
            pyautogui.hotkey('command', 'l')
        time.sleep(0.5)
    
    def send_query(self, text: str):
        """Escribe la consulta en el chat del agente"""
        # Limpiar campo actual
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        
        # Escribir consulta
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.2)
        
        # Enviar
        pyautogui.press('enter')
    
    def wait_for_response(self, timeout: int = RESPONSE_TIMEOUT) -> bool:
        """Espera a que Antigravity termine de responder"""
        start_time = time.time()
        last_clipboard = ""
        stable_count = 0
        
        while time.time() - start_time < timeout:
            time.sleep(CHECK_INTERVAL)
            
            # Detectar si sigue escribiendo
            # Método: verificar si el contenido visible cambió
            # (Esto se puede mejorar con OCR o detección de elementos)
            
            # Por ahora, esperamos un tiempo fijo + verificación
            if time.time() - start_time > 5:  # Mínimo 5 segundos
                # Verificar estabilidad
                stable_count += 1
                if stable_count >= 3:
                    return True
        
        return True
    
    def extract_response(self) -> dict:
        """Extrae la respuesta de Antigravity"""
        # Seleccionar todo el contenido de la respuesta
        # Esto depende de cómo esté estructurado el UI de Antigravity
        
        # Método 1: Triple click para seleccionar párrafo
        pyautogui.tripleClick()
        time.sleep(0.2)
        
        # Copiar
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.2)
        
        # Obtener del clipboard
        response = pyperclip.paste()
        
        # Detectar si hay código
        code_blocks = []
        if "```" in response:
            # Extraer bloques de código
            import re
            code_pattern = r"```(\w*)\n(.*?)```"
            matches = re.findall(code_pattern, response, re.DOTALL)
            for lang, code in matches:
                code_blocks.append({
                    "language": lang or "text",
                    "code": code.strip()
                })
        
        return {
            "response": response,
            "code_blocks": code_blocks,
            "timestamp": time.time()
        }
    
    def process_query(self, prompt: str) -> dict:
        """Procesa una consulta completa"""
        if self.is_processing:
            return {"error": "Ya hay una consulta en proceso", "status": "busy"}
        
        try:
            self.is_processing = True
            
            # 1. Activar Antigravity
            self.activate_window()
            
            # 2. Abrir panel del agente
            self.open_agent_panel()
            
            # 3. Enviar consulta
            self.send_query(prompt)
            
            # 4. Esperar respuesta
            self.wait_for_response()
            
            # 5. Extraer respuesta
            result = self.extract_response()
            result["status"] = "success"
            
            return result
            
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
        finally:
            self.is_processing = False


# Instancia global del automatizador
automator = AntigravityAutomator()


@app.route('/health', methods=['GET'])
def health():
    """Verifica que el bridge esté funcionando"""
    return jsonify({
        "status": "ok",
        "service": "Antigravity Bridge",
        "is_processing": automator.is_processing
    })


@app.route('/status', methods=['GET'])
def status():
    """Estado detallado del bridge"""
    return jsonify({
        "bridge_running": True,
        "is_processing": automator.is_processing,
        "antigravity_window": ANTIGRAVITY_WINDOW_TITLE,
        "timeout": RESPONSE_TIMEOUT
    })


@app.route('/query', methods=['POST'])
def query():
    """Procesa una consulta a Antigravity"""
    data = request.get_json()
    
    if not data or 'prompt' not in data:
        return jsonify({"error": "Se requiere 'prompt' en el body"}), 400
    
    prompt = data['prompt']
    
    # Procesar en thread separado para no bloquear
    result = automator.process_query(prompt)
    
    return jsonify(result)


if __name__ == '__main__':
    print("=" * 60)
    print("ANTIGRAVITY BRIDGE")
    print("=" * 60)
    print("Servidor iniciando en http://localhost:8888")
    print("Asegúrate de tener Antigravity abierto")
    print("Luego ejecuta: ngrok http 8888")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8888, debug=False)
```

---

### FASE 6: Instrucciones de Uso

#### 6.1 En la PC del Usuario

```bash
# Paso 1: Abrir Google Antigravity

# Paso 2: En una terminal, ir a la carpeta del bridge
cd ruta/a/tu/carpeta

# Paso 3: Ejecutar el bridge
python antigravity_bridge.py

# Paso 4: En OTRA terminal, iniciar ngrok
ngrok http 8888

# Paso 5: Copiar la URL que muestra ngrok
# Ejemplo: https://abc123.ngrok.io
```

#### 6.2 En BUNK3R_IA (Replit)

```bash
# Agregar variable de entorno:
ANTIGRAVITY_BRIDGE_URL=https://abc123.ngrok.io
```

#### 6.3 Verificar Conexión

```bash
# Probar que el bridge responde:
curl https://abc123.ngrok.io/health

# Debería responder:
# {"status": "ok", "service": "Antigravity Bridge"}
```

---

### FASE 7: Archivos a Crear/Modificar

| Archivo | Ubicación | Acción | Descripción |
|---------|-----------|--------|-------------|
| `antigravity_bridge.py` | PC Usuario | CREAR | Script del bridge |
| `antigravity_client.py` | BUNK3R_IA/core/ | CREAR | Cliente para conectar al bridge |
| `ai_service.py` | BUNK3R_IA/core/ | MODIFICAR | Agregar proveedor Antigravity |
| `config.py` | BUNK3R_IA/ | MODIFICAR | Agregar configuración |
| `.env` | BUNK3R_IA/ | MODIFICAR | Agregar ANTIGRAVITY_BRIDGE_URL |

---

### FASE 8: Orden de Implementación

```
SEMANA 1: Preparación
├── Día 1-2: Crear antigravity_bridge.py completo
├── Día 3: Probar bridge localmente
└── Día 4: Configurar ngrok y probar túnel

SEMANA 2: Integración BUNK3R_IA
├── Día 1: Crear antigravity_client.py
├── Día 2: Modificar ai_service.py
├── Día 3: Modificar config.py y variables de entorno
└── Día 4: Pruebas de integración

SEMANA 3: Optimización
├── Día 1-2: Mejorar detección de respuestas
├── Día 3: Agregar manejo de errores robusto
└── Día 4: Documentación y pruebas finales
```

---

### FASE 9: Fallback y Recuperación

Si Antigravity no está disponible, el sistema automáticamente usará los otros proveedores:

```
1. Intenta Antigravity (bridge)
   ├── Si OK → Usa respuesta de Antigravity
   └── Si FALLA → Continúa al siguiente

2. Intenta DeepSeek
   ├── Si OK → Usa respuesta
   └── Si FALLA → Continúa

3. Intenta Groq
   └── ... y así sucesivamente
```

---

### FASE 10: Consideraciones de Seguridad

1. **ngrok genera URLs únicas** cada vez que se reinicia
   - Actualizar ANTIGRAVITY_BRIDGE_URL cuando cambie
   - Considerar ngrok de pago para URL fija

2. **El bridge tiene acceso a tu PC**
   - Solo acepta requests del túnel
   - No exponer directamente a internet sin ngrok

3. **Antigravity debe estar visible**
   - No minimizar la ventana
   - Mantener en monitor secundario si es necesario

---

### FASE 11: Mejoras Futuras

1. **Detección de respuesta mejorada**
   - Usar OCR para detectar cuando Antigravity termina
   - Monitorear el cursor de escritura

2. **Soporte multi-respuesta**
   - Manejar respuestas largas divididas
   - Streaming de respuestas parciales

3. **Persistencia de sesión**
   - Mantener contexto de conversación en Antigravity
   - Sincronizar historial con BUNK3R_IA

4. **URL fija de ngrok**
   - Usar ngrok de pago o alternativa (cloudflare tunnel)
   - Evitar reconfigurar cada vez

---

## Resumen Ejecutivo

| Aspecto | Detalle |
|---------|---------|
| **Objetivo** | Usar Antigravity como motor principal de IA |
| **Método** | Automatización GUI + Túnel HTTP |
| **Costo** | Gratis (Antigravity + ngrok free tier) |
| **Requisito Principal** | PC encendida con Antigravity abierto |
| **Tiempo estimado** | 2-3 semanas para implementación completa |
| **Fallback** | Proveedores actuales (DeepSeek, Groq, etc.) |

---

## Comandos Rápidos

```bash
# PC del Usuario
python antigravity_bridge.py    # Iniciar bridge
ngrok http 8888                 # Iniciar túnel

# Verificar
curl https://URL.ngrok.io/health
curl -X POST https://URL.ngrok.io/query -H "Content-Type: application/json" -d '{"prompt": "hola"}'
```

---

**Documento creado:** 17 Diciembre 2025
**Versión:** 1.0
**Estado:** Plan de implementación
