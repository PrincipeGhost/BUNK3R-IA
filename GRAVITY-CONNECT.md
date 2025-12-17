# GRAVITY-CONNECT: Integración Antigravity con BUNK3R_IA

## Descripción General

Este documento detalla el plan completo para integrar Google Antigravity como motor principal de IA para BUNK3R_IA, utilizando un sistema de puente (bridge) que permite comunicación bidireccional entre la aplicación en Replit y Antigravity corriendo en la PC del usuario.

**Versión:** 2.0 - Cloudflare Tunnel + OCR
**Fecha:** 17 Diciembre 2025

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
│                                                         │ (Cloudflare Tunnel) │
│                                                         ▼                     │
│  ┌──────────────────────────────────────────────────────────────────────┐    │
│  │                        PC DEL USUARIO                                 │    │
│  │                                                                       │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │              ANTIGRAVITY BRIDGE (Python)                     │    │    │
│  │  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │    │    │
│  │  │  │ HTTP Server  │───►│  Automator   │───►│ OCR Response │  │    │    │
│  │  │  │ (puerto 8888)│    │  (PyAutoGUI) │    │  Extractor   │  │    │    │
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
│  │  │                   CLOUDFLARE TUNNEL                          │    │    │
│  │  │  - Expone localhost:8888 a internet (GRATIS)                │    │    │
│  │  │  - URL: https://random-name.trycloudflare.com               │    │    │
│  │  │  - NO requiere cuenta ni registro                           │    │    │
│  │  │  - Auto HTTPS + Protección DDoS                             │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Ventajas de Cloudflare Tunnel vs ngrok

| Característica | Cloudflare Tunnel | ngrok |
|----------------|-------------------|-------|
| **Cuenta requerida** | NO (Quick Tunnel) | SI |
| **Costo** | Gratis | Gratis (limitado) |
| **HTTPS automático** | ✅ | ✅ |
| **Protección DDoS** | ✅ | ❌ |
| **Límite de conexiones** | 200 concurrentes | Varía |
| **Facilidad de uso** | 1 comando | Requiere config |

---

## Plan de Trabajo Detallado

### FASE 1: Preparación del Entorno (PC del Usuario)

#### 1.1 Requisitos Previos
- [ ] Google Antigravity instalado y funcionando
- [ ] Python 3.10+ instalado
- [ ] Cloudflared instalado (ver abajo)

#### 1.2 Instalación de Dependencias Python (PC)

```bash
pip install pyautogui pillow flask flask-cors pyperclip keyboard pygetwindow pytesseract opencv-python mss
```

**Dependencias adicionales para OCR:**
- **Windows:** Instalar Tesseract OCR desde https://github.com/UB-Mannheim/tesseract/wiki
- **Mac:** `brew install tesseract`
- **Linux:** `sudo apt install tesseract-ocr tesseract-ocr-spa`

#### 1.3 Instalación de Cloudflare Tunnel

**Windows (con Chocolatey):**
```bash
choco install cloudflared
```

**Windows (descarga directa):**
```bash
# Descargar desde:
# https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
# Renombrar a cloudflared.exe y agregar al PATH
```

**Mac (con Homebrew):**
```bash
brew install cloudflare/cloudflare/cloudflared
```

**Linux (Debian/Ubuntu):**
```bash
curl -fsSL https://pkg.cloudflare.com/cloudflare-public-v2.gpg | sudo tee /usr/share/keyrings/cloudflare-public-v2.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/cloudflare-public-v2.gpg] https://pkg.cloudflare.com/cloudflared any main" | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt update
sudo apt install cloudflared
```

**Verificar instalación:**
```bash
cloudflared --version
```

---

### FASE 2: Creación del Antigravity Bridge con OCR (PC del Usuario)

#### 2.1 Archivo: `antigravity_bridge.py`

Este script debe crearse en la PC del usuario. Funciones principales:

```
1. HTTPServer (Flask)
   - Puerto: 8888
   - Endpoints:
     - POST /query → Recibe consulta, la procesa, devuelve respuesta
     - GET /health → Verifica que el bridge está funcionando
     - GET /status → Estado de Antigravity (abierto/cerrado)
     - POST /calibrate → Calibrar coordenadas de la ventana

2. AntigravityAutomator (PyAutoGUI)
   - activate_window() → Trae Antigravity al frente
   - open_agent_panel() → Cmd+L para abrir panel del agente
   - send_query(text) → Escribe la consulta en el chat
   - wait_for_response() → Usa OCR para detectar cuando termina
   - extract_response() → Extrae respuesta con OCR

3. OCREngine (Tesseract + OpenCV)
   - capture_region() → Captura área del chat
   - extract_text() → Extrae texto de la imagen
   - detect_response_complete() → Detecta si terminó de escribir
   - extract_code_blocks() → Detecta y extrae bloques de código
```

#### 2.2 Flujo del Bridge con OCR

```
1. Bridge recibe POST /query con {"prompt": "crear función fibonacci"}
2. Activa ventana de Antigravity (la trae al frente)
3. Abre panel del agente si no está abierto (Cmd+L)
4. Hace click en el campo de texto del chat
5. Escribe la consulta
6. Presiona Enter
7. [OCR] Captura pantalla cada 0.5s
8. [OCR] Detecta cuando el texto deja de cambiar (respuesta completa)
9. [OCR] Extrae todo el texto de la respuesta
10. [OCR] Identifica bloques de código por formato
11. Devuelve JSON: {"response": "...", "code_blocks": [...], "status": "success"}
```

---

### FASE 3: Configuración de Cloudflare Tunnel (PC del Usuario)

#### 3.1 Iniciar el túnel (Quick Tunnel - Sin cuenta)

```bash
# En una terminal separada (después de iniciar el bridge)
cloudflared tunnel --url http://localhost:8888
```

#### 3.2 Obtener URL pública

```
Cloudflare mostrará algo como:
+----------------------------+
| Your quick tunnel is ready!|
| https://random-name.trycloudflare.com
+----------------------------+

Esta URL es la que usará BUNK3R_IA
```

#### 3.3 Configurar URL en BUNK3R_IA
- Agregar variable de entorno: `ANTIGRAVITY_BRIDGE_URL=https://random-name.trycloudflare.com`

---

### FASE 4: Modificaciones en BUNK3R_IA (Replit)

#### 4.1 Nuevo archivo: `BUNK3R_IA/core/antigravity_client.py`

```python
"""
Cliente para comunicarse con el Antigravity Bridge
"""
import httpx
import asyncio
from typing import Optional, Dict, Any
import os

class AntigravityClient:
    def __init__(self, bridge_url: str = None):
        self.bridge_url = bridge_url or os.getenv("ANTIGRAVITY_BRIDGE_URL", "")
        self.timeout = 180  # Antigravity puede tardar con respuestas largas
        self.client = httpx.AsyncClient(timeout=self.timeout)
    
    async def query(self, prompt: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Envía consulta al bridge y retorna respuesta de Antigravity"""
        if not self.bridge_url:
            raise Exception("ANTIGRAVITY_BRIDGE_URL no configurado")
        
        payload = {
            "prompt": prompt,
            "context": context or {}
        }
        
        try:
            response = await self.client.post(
                f"{self.bridge_url}/query",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"error": "Timeout esperando respuesta de Antigravity", "status": "timeout"}
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    async def health_check(self) -> bool:
        """Verifica que el bridge esté funcionando"""
        if not self.bridge_url:
            return False
        
        try:
            response = await self.client.get(
                f"{self.bridge_url}/health",
                timeout=10
            )
            data = response.json()
            return data.get("status") == "ok"
        except:
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Estado detallado del bridge y Antigravity"""
        if not self.bridge_url:
            return {"error": "URL no configurada", "available": False}
        
        try:
            response = await self.client.get(
                f"{self.bridge_url}/status",
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"error": str(e), "available": False}
    
    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose()
```

#### 4.2 Modificar: `BUNK3R_IA/core/ai_service.py`

Agregar Antigravity como proveedor principal:

```python
# Orden de proveedores actualizado
PROVIDERS = {
    "antigravity": 0,  # PRINCIPAL (gratis, ilimitado)
    "deepseek": 1,     # Fallback 1
    "groq": 2,         # Fallback 2
    "gemini": 3,       # Fallback 3
    "cerebras": 4,     # Fallback 4
    "huggingface": 5   # Fallback 5
}

# Nueva función para llamar a Antigravity
async def call_antigravity(prompt: str, context: dict = None) -> str:
    from .antigravity_client import AntigravityClient
    
    client = AntigravityClient()
    
    try:
        if not await client.health_check():
            raise Exception("Antigravity Bridge no disponible")
        
        result = await client.query(prompt, context)
        
        if result.get("status") == "success":
            return result.get("response", "")
        else:
            raise Exception(result.get("error", "Error desconocido"))
    finally:
        await client.close()
```

#### 4.3 Modificar: `BUNK3R_IA/config.py`

```python
# Agregar configuración de Antigravity
ANTIGRAVITY_CONFIG = {
    "bridge_url": os.getenv("ANTIGRAVITY_BRIDGE_URL", ""),
    "timeout": 180,
    "retry_attempts": 2,
    "fallback_enabled": True,
    "ocr_enabled": True
}
```

---

### FASE 5: Script Completo del Bridge con OCR (Para PC del Usuario)

#### 5.1 Crear archivo: `antigravity_bridge.py`

```python
"""
ANTIGRAVITY BRIDGE v2.0 - Con OCR
=================================
Script para correr en la PC del usuario.
Conecta BUNK3R_IA con Google Antigravity via automatización GUI + OCR.

Requisitos:
- pip install flask flask-cors pyautogui pyperclip pillow keyboard pytesseract opencv-python mss pygetwindow

Para OCR (Tesseract):
- Windows: https://github.com/UB-Mannheim/tesseract/wiki
- Mac: brew install tesseract
- Linux: sudo apt install tesseract-ocr

Uso:
1. Abrir Google Antigravity
2. Ejecutar: python antigravity_bridge.py
3. Ejecutar: cloudflared tunnel --url http://localhost:8888
4. Copiar URL de Cloudflare a BUNK3R_IA
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pyautogui
import pyperclip
import time
import threading
import os
import re
import mss
import cv2
import numpy as np

# Configurar pytesseract
try:
    import pytesseract
    # Ajustar path de Tesseract según sistema
    if os.name == 'nt':  # Windows
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️ pytesseract no disponible. Usando método alternativo.")

app = Flask(__name__)
CORS(app)

# Configuración
ANTIGRAVITY_WINDOW_TITLE = "Antigravity"
RESPONSE_TIMEOUT = 120  # segundos
CHECK_INTERVAL = 0.5    # segundos
STABLE_CHECKS = 5       # cuantas veces debe estar estable para considerar terminado


class OCREngine:
    """Motor de OCR para extraer texto de Antigravity"""
    
    def __init__(self):
        self.sct = mss.mss()
        self.chat_region = None  # Se calibra automáticamente
        self.last_text = ""
        self.stable_count = 0
    
    def capture_screen(self, region=None):
        """Captura una región de la pantalla"""
        if region:
            monitor = {"top": region[1], "left": region[0], 
                      "width": region[2], "height": region[3]}
        else:
            monitor = self.sct.monitors[0]
        
        screenshot = self.sct.grab(monitor)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img
    
    def preprocess_image(self, img):
        """Preprocesa imagen para mejor OCR"""
        # Convertir a escala de grises
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Aumentar contraste
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
        
        # Binarización adaptativa
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        return binary
    
    def extract_text(self, img):
        """Extrae texto de una imagen usando OCR"""
        if not OCR_AVAILABLE:
            return ""
        
        processed = self.preprocess_image(img)
        
        # Configuración para mejor detección de código
        config = '--oem 3 --psm 6'
        text = pytesseract.image_to_string(processed, config=config)
        
        return text.strip()
    
    def is_response_complete(self, current_text):
        """Detecta si la respuesta ha terminado (texto estable)"""
        if current_text == self.last_text and current_text:
            self.stable_count += 1
        else:
            self.stable_count = 0
            self.last_text = current_text
        
        return self.stable_count >= STABLE_CHECKS
    
    def extract_code_blocks(self, text):
        """Extrae bloques de código del texto"""
        code_blocks = []
        
        # Patrón para bloques de código con lenguaje
        pattern = r"```(\w*)\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        
        for lang, code in matches:
            code_blocks.append({
                "language": lang or "text",
                "code": code.strip()
            })
        
        # Si no hay bloques markdown, buscar por indentación
        if not code_blocks:
            lines = text.split('\n')
            in_code = False
            current_code = []
            
            for line in lines:
                if line.startswith('    ') or line.startswith('\t'):
                    in_code = True
                    current_code.append(line.strip())
                elif in_code and current_code:
                    code_blocks.append({
                        "language": "text",
                        "code": '\n'.join(current_code)
                    })
                    current_code = []
                    in_code = False
        
        return code_blocks
    
    def reset(self):
        """Resetea el estado del OCR"""
        self.last_text = ""
        self.stable_count = 0


class AntigravityAutomator:
    """Automatiza la interacción con Antigravity"""
    
    def __init__(self):
        self.is_processing = False
        self.ocr = OCREngine()
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        # Coordenadas del chat (se calibran automáticamente)
        self.chat_input_coords = None
        self.chat_output_region = None
    
    def activate_window(self):
        """Trae Antigravity al primer plano"""
        try:
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle(ANTIGRAVITY_WINDOW_TITLE)
            if windows:
                win = windows[0]
                if win.isMinimized:
                    win.restore()
                win.activate()
                time.sleep(0.5)
                
                # Guardar región de la ventana para OCR
                self.chat_output_region = (
                    win.left + 50, 
                    win.top + 100,
                    win.width - 100,
                    win.height - 200
                )
                return True
        except Exception as e:
            print(f"Error activando ventana: {e}")
        
        # Fallback: Alt+Tab
        pyautogui.hotkey('alt', 'tab')
        time.sleep(0.5)
        return True
    
    def open_agent_panel(self):
        """Abre el panel del agente con Cmd+L (Mac) o Ctrl+L (Windows)"""
        if os.name == 'nt':  # Windows
            pyautogui.hotkey('ctrl', 'l')
        else:  # Mac/Linux
            pyautogui.hotkey('command', 'l')
        time.sleep(0.8)
    
    def send_query(self, text: str):
        """Escribe la consulta en el chat del agente"""
        # Limpiar campo actual
        if os.name == 'nt':
            pyautogui.hotkey('ctrl', 'a')
        else:
            pyautogui.hotkey('command', 'a')
        time.sleep(0.1)
        
        # Escribir consulta usando clipboard (más confiable para texto largo)
        pyperclip.copy(text)
        if os.name == 'nt':
            pyautogui.hotkey('ctrl', 'v')
        else:
            pyautogui.hotkey('command', 'v')
        time.sleep(0.3)
        
        # Enviar
        pyautogui.press('enter')
    
    def wait_for_response_ocr(self, timeout: int = RESPONSE_TIMEOUT) -> str:
        """Espera y captura la respuesta usando OCR"""
        start_time = time.time()
        self.ocr.reset()
        
        # Esperar un poco para que empiece a escribir
        time.sleep(2)
        
        last_response = ""
        
        while time.time() - start_time < timeout:
            time.sleep(CHECK_INTERVAL)
            
            # Capturar pantalla del área del chat
            if self.chat_output_region:
                img = self.ocr.capture_screen(self.chat_output_region)
            else:
                img = self.ocr.capture_screen()
            
            # Extraer texto
            current_text = self.ocr.extract_text(img)
            
            # Verificar si la respuesta está completa
            if self.ocr.is_response_complete(current_text):
                last_response = current_text
                break
            
            last_response = current_text
        
        return last_response
    
    def wait_for_response_clipboard(self, timeout: int = RESPONSE_TIMEOUT) -> str:
        """Método alternativo: espera y copia usando clipboard"""
        start_time = time.time()
        
        # Esperar tiempo mínimo
        time.sleep(5)
        
        last_clipboard = ""
        stable_count = 0
        
        while time.time() - start_time < timeout:
            time.sleep(CHECK_INTERVAL * 2)
            
            # Seleccionar todo y copiar
            if os.name == 'nt':
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.1)
                pyautogui.hotkey('ctrl', 'c')
            else:
                pyautogui.hotkey('command', 'a')
                time.sleep(0.1)
                pyautogui.hotkey('command', 'c')
            
            time.sleep(0.2)
            current = pyperclip.paste()
            
            if current == last_clipboard and current:
                stable_count += 1
                if stable_count >= 3:
                    return current
            else:
                stable_count = 0
                last_clipboard = current
        
        return last_clipboard
    
    def extract_response(self, raw_text: str) -> dict:
        """Procesa el texto extraído y extrae código"""
        # Limpiar texto
        response = raw_text.strip()
        
        # Extraer bloques de código
        code_blocks = self.ocr.extract_code_blocks(response)
        
        return {
            "response": response,
            "code_blocks": code_blocks,
            "timestamp": time.time()
        }
    
    def process_query(self, prompt: str, use_ocr: bool = True) -> dict:
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
            
            # 4. Esperar y capturar respuesta
            if use_ocr and OCR_AVAILABLE:
                raw_response = self.wait_for_response_ocr()
            else:
                raw_response = self.wait_for_response_clipboard()
            
            # 5. Procesar respuesta
            result = self.extract_response(raw_response)
            result["status"] = "success"
            result["method"] = "ocr" if (use_ocr and OCR_AVAILABLE) else "clipboard"
            
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
        "service": "Antigravity Bridge v2.0",
        "ocr_available": OCR_AVAILABLE,
        "is_processing": automator.is_processing
    })


@app.route('/status', methods=['GET'])
def status():
    """Estado detallado del bridge"""
    return jsonify({
        "bridge_running": True,
        "version": "2.0",
        "is_processing": automator.is_processing,
        "ocr_available": OCR_AVAILABLE,
        "antigravity_window": ANTIGRAVITY_WINDOW_TITLE,
        "timeout": RESPONSE_TIMEOUT,
        "tunnel": "cloudflare"
    })


@app.route('/query', methods=['POST'])
def query():
    """Procesa una consulta a Antigravity"""
    data = request.get_json()
    
    if not data or 'prompt' not in data:
        return jsonify({"error": "Se requiere 'prompt' en el body"}), 400
    
    prompt = data['prompt']
    use_ocr = data.get('use_ocr', True)
    
    result = automator.process_query(prompt, use_ocr)
    
    return jsonify(result)


@app.route('/calibrate', methods=['POST'])
def calibrate():
    """Calibra las coordenadas de la ventana de Antigravity"""
    try:
        automator.activate_window()
        return jsonify({
            "status": "ok",
            "message": "Ventana calibrada",
            "region": automator.chat_output_region
        })
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("ANTIGRAVITY BRIDGE v2.0 - Con OCR")
    print("=" * 60)
    print(f"OCR disponible: {'SI' if OCR_AVAILABLE else 'NO'}")
    print("Servidor iniciando en http://localhost:8888")
    print("")
    print("PASOS:")
    print("1. Asegúrate de tener Antigravity abierto")
    print("2. En otra terminal ejecuta:")
    print("   cloudflared tunnel --url http://localhost:8888")
    print("3. Copia la URL que te da Cloudflare a BUNK3R_IA")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8888, debug=False, threaded=True)
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

# Paso 4: En OTRA terminal, iniciar Cloudflare Tunnel
cloudflared tunnel --url http://localhost:8888

# Paso 5: Copiar la URL que muestra Cloudflare
# Ejemplo: https://random-name.trycloudflare.com
```

#### 6.2 En BUNK3R_IA (Replit)

```bash
# Agregar variable de entorno:
ANTIGRAVITY_BRIDGE_URL=https://random-name.trycloudflare.com
```

#### 6.3 Verificar Conexión

```bash
# Probar que el bridge responde:
curl https://random-name.trycloudflare.com/health

# Debería responder:
# {"status": "ok", "service": "Antigravity Bridge v2.0", "ocr_available": true}

# Probar una consulta:
curl -X POST https://random-name.trycloudflare.com/query \
  -H "Content-Type: application/json" \
  -d '{"prompt": "hola, dime la hora"}'
```

---

### FASE 7: Archivos a Crear/Modificar

| Archivo | Ubicación | Acción | Descripción |
|---------|-----------|--------|-------------|
| `antigravity_bridge.py` | PC Usuario | CREAR | Script del bridge con OCR |
| `antigravity_client.py` | BUNK3R_IA/core/ | CREAR | Cliente para conectar al bridge |
| `ai_service.py` | BUNK3R_IA/core/ | MODIFICAR | Agregar proveedor Antigravity |
| `config.py` | BUNK3R_IA/ | MODIFICAR | Agregar configuración |
| Variables de entorno | Replit | AGREGAR | ANTIGRAVITY_BRIDGE_URL |

---

### FASE 8: Orden de Implementación

```
DÍA 1: Preparación
├── Instalar Tesseract OCR en PC
├── Instalar dependencias Python
├── Instalar cloudflared
└── Crear antigravity_bridge.py

DÍA 2: Pruebas Locales
├── Probar bridge localmente
├── Calibrar región de captura OCR
├── Probar túnel Cloudflare
└── Verificar health endpoint

DÍA 3: Integración BUNK3R_IA
├── Crear antigravity_client.py
├── Modificar ai_service.py
├── Configurar variable de entorno
└── Pruebas end-to-end

DÍA 4: Optimización
├── Ajustar tiempos de espera
├── Mejorar detección OCR
├── Agregar manejo de errores
└── Documentar
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

1. **Cloudflare Quick Tunnel**
   - Genera URLs aleatorias cada vez (más seguro)
   - Actualizar ANTIGRAVITY_BRIDGE_URL cuando cambie
   - Para URL fija, crear Named Tunnel (requiere cuenta gratuita)

2. **El bridge tiene acceso a tu PC**
   - Solo acepta requests del túnel
   - No exponer directamente a internet

3. **Antigravity debe estar visible**
   - No minimizar la ventana
   - Mantener en monitor secundario si es necesario

---

### FASE 11: Mejoras Implementadas (v2.0)

1. **OCR con Tesseract + OpenCV**
   - Captura de pantalla con mss (multiplataforma)
   - Preprocesamiento de imagen para mejor detección
   - Detección automática de fin de respuesta
   - Extracción de bloques de código

2. **Cloudflare Tunnel**
   - Sin necesidad de cuenta
   - HTTPS automático
   - Protección DDoS incluida
   - Un solo comando para activar

3. **Método de respaldo**
   - Si OCR falla, usa método clipboard
   - Detección automática de disponibilidad

4. **Calibración automática**
   - Detecta ventana de Antigravity
   - Ajusta región de captura automáticamente

---

## Resumen Ejecutivo

| Aspecto | Detalle |
|---------|---------|
| **Objetivo** | Usar Antigravity como motor principal de IA |
| **Método** | Automatización GUI + OCR + Cloudflare Tunnel |
| **Costo** | 100% Gratis |
| **Requisito Principal** | PC encendida con Antigravity abierto |
| **Tiempo estimado** | 3-4 días para implementación completa |
| **Fallback** | Proveedores actuales (DeepSeek, Groq, etc.) |
| **Mejoras v2.0** | OCR, Cloudflare, calibración automática |

---

## Comandos Rápidos

```bash
# PC del Usuario
python antigravity_bridge.py              # Iniciar bridge
cloudflared tunnel --url http://localhost:8888  # Iniciar túnel

# Verificar
curl https://URL.trycloudflare.com/health
curl -X POST https://URL.trycloudflare.com/query \
  -H "Content-Type: application/json" \
  -d '{"prompt": "hola"}'

# Calibrar
curl -X POST https://URL.trycloudflare.com/calibrate
```

---

## Comparación: ngrok vs Cloudflare Tunnel

| Aspecto | ngrok | Cloudflare Tunnel |
|---------|-------|-------------------|
| Cuenta | Requerida | NO requerida |
| Instalación | Más pasos | 1 comando |
| URL | Cambia cada reinicio | Cambia cada reinicio |
| HTTPS | Sí | Sí |
| DDoS | No | Sí |
| Límites | Estrictos | 200 concurrentes |
| Precio | Gratis limitado | 100% gratis |

---

**Documento actualizado:** 17 Diciembre 2025
**Versión:** 2.0 (Cloudflare Tunnel + OCR)
**Estado:** Listo para implementación
