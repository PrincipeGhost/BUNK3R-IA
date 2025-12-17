# GRAVITY-CONNECT: Integración Antigravity con BUNK3R_IA

## Descripción General

Este documento detalla el plan completo para integrar Google Antigravity como motor principal de IA para BUNK3R_IA, utilizando un sistema de puente (bridge) que permite comunicación bidireccional entre la aplicación en Replit y Antigravity corriendo en la PC del usuario.

**Versión:** 2.1 - Cloudflare Tunnel + Clipboard Mode
**Fecha:** 17 Diciembre 2025
**Estado:** EN PROGRESO

---

## Estado Actual de Implementación

| Componente | Estado | Notas |
|------------|--------|-------|
| Documentación | ✅ Completo | Este archivo |
| antigravity_client.py (Replit) | ✅ Completo | `BUNK3R_IA/core/antigravity_client.py` |
| ai_service.py integración | ✅ Completo | Provider agregado como prioridad 0 |
| config.py | ✅ Completo | Variables de configuración añadidas |
| Bridge script (PC Usuario) | ✅ Completo | Clipboard mode (sin OCR) |
| Dependencias Python (PC) | ✅ Instaladas | flask, pyautogui, etc. |
| Cloudflared (PC) | ⏳ Instalando | Usuario descargando |
| Túnel activo | ⏳ Pendiente | Siguiente paso |
| Variable ANTIGRAVITY_BRIDGE_URL | ⏳ Pendiente | Configurar en Replit |

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
│  │  │  ai-chat.js │    │ (multi-provider)│    │                   │     │    │
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
│  │  │  │ HTTP Server  │───►│  Automator   │───►│  Clipboard   │  │    │    │
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

## Configuración del Usuario

**Ruta del proyecto en PC:**
```
C:\Users\Asus\Documents\Proyectos\AntigravityBridge\
```

**Archivo principal:**
```
C:\Users\Asus\Documents\Proyectos\AntigravityBridge\antigravity_bridge.py
```

**Python instalado:** 3.14 (pythoncore-3.14-64)

---

## Dependencias Instaladas (PC Usuario)

```
flask==3.1.2
flask-cors==6.0.2
pyautogui==0.9.54
pyperclip==1.11.0
pillow==12.0.0
keyboard==0.13.5
mss==10.1.0
pygetwindow==0.0.9
```

**Nota:** opencv-python y pytesseract no instalados (incompatibles con Python 3.14). Se usa modo Clipboard en lugar de OCR.

---

## Script del Bridge (antigravity_bridge.py)

```python
"""
ANTIGRAVITY BRIDGE v2.0 (Clipboard Mode)
=========================================
Conecta BUNK3R_IA con Google Antigravity via Cloudflare Tunnel

Uso:
1. Abre Google Antigravity en tu navegador
2. Ejecuta: python antigravity_bridge.py
3. En otra terminal: cloudflared tunnel --url http://localhost:8888
4. Copia la URL de Cloudflare a BUNK3R_IA
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pyautogui
import pyperclip
import time
import os
import re

app = Flask(__name__)
CORS(app)

ANTIGRAVITY_WINDOW_TITLE = "Antigravity"
RESPONSE_TIMEOUT = 120
CHECK_INTERVAL = 1.0
STABLE_CHECKS = 3


class AntigravityAutomator:
    def __init__(self):
        self.is_processing = False
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
    
    def activate_window(self):
        try:
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle(ANTIGRAVITY_WINDOW_TITLE)
            if windows:
                win = windows[0]
                if win.isMinimized:
                    win.restore()
                win.activate()
                time.sleep(0.5)
                return True
        except Exception as e:
            print(f"Error activando ventana: {e}")
        
        pyautogui.hotkey('alt', 'tab')
        time.sleep(0.5)
        return True
    
    def open_agent_panel(self):
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.8)
    
    def send_query(self, text: str):
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.3)
        
        pyautogui.press('enter')
    
    def wait_and_extract_response(self, timeout: int = RESPONSE_TIMEOUT) -> str:
        start_time = time.time()
        time.sleep(3)
        
        last_text = ""
        stable_count = 0
        
        while time.time() - start_time < timeout:
            time.sleep(CHECK_INTERVAL)
            
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.15)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.15)
            
            pyautogui.press('escape')
            
            current_text = pyperclip.paste()
            
            if current_text == last_text and len(current_text) > 10:
                stable_count += 1
                if stable_count >= STABLE_CHECKS:
                    return current_text
            else:
                stable_count = 0
                last_text = current_text
        
        return last_text
    
    def extract_code_blocks(self, text: str) -> list:
        code_blocks = []
        pattern = r"```(\w*)\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        
        for lang, code in matches:
            code_blocks.append({
                "language": lang or "text",
                "code": code.strip()
            })
        
        return code_blocks
    
    def process_query(self, prompt: str) -> dict:
        if self.is_processing:
            return {"error": "Ya hay una consulta en proceso", "status": "busy"}
        
        try:
            self.is_processing = True
            
            self.activate_window()
            self.open_agent_panel()
            self.send_query(prompt)
            
            response = self.wait_and_extract_response()
            code_blocks = self.extract_code_blocks(response)
            
            return {
                "response": response,
                "code_blocks": code_blocks,
                "status": "success",
                "method": "clipboard",
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {"error": str(e), "status": "error"}
        finally:
            self.is_processing = False


automator = AntigravityAutomator()


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "service": "Antigravity Bridge v2.0",
        "method": "clipboard",
        "is_processing": automator.is_processing
    })


@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "bridge_running": True,
        "version": "2.0",
        "method": "clipboard",
        "is_processing": automator.is_processing,
        "antigravity_window": ANTIGRAVITY_WINDOW_TITLE,
        "timeout": RESPONSE_TIMEOUT,
        "tunnel": "cloudflare"
    })


@app.route('/query', methods=['POST'])
def query():
    data = request.get_json()
    
    if not data or 'prompt' not in data:
        return jsonify({"error": "Se requiere 'prompt' en el body"}), 400
    
    prompt = data['prompt']
    result = automator.process_query(prompt)
    
    return jsonify(result)


@app.route('/calibrate', methods=['POST'])
def calibrate():
    try:
        automator.activate_window()
        return jsonify({"status": "ok", "message": "Ventana activada"})
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("ANTIGRAVITY BRIDGE v2.0 - Clipboard Mode")
    print("=" * 60)
    print("Servidor en http://localhost:8888")
    print("")
    print("PASOS:")
    print("1. Abre Google Antigravity")
    print("2. En otra terminal ejecuta:")
    print("   cloudflared tunnel --url http://localhost:8888")
    print("3. Copia la URL de Cloudflare a BUNK3R_IA")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8888, debug=False, threaded=True)
```

---

## Próximos Pasos

### Paso 1: Instalar Cloudflared (EN PROGRESO)
```powershell
winget install Cloudflare.cloudflared
```

O descargar desde:
https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe

### Paso 2: Ejecutar el Bridge
```powershell
cd C:\Users\Asus\Documents\Proyectos\AntigravityBridge
python antigravity_bridge.py
```

### Paso 3: Iniciar Cloudflare Tunnel (en otra terminal)
```powershell
cloudflared tunnel --url http://localhost:8888
```

### Paso 4: Copiar la URL
Cloudflare mostrará algo como:
```
Your quick tunnel is ready!
https://random-name.trycloudflare.com
```

### Paso 5: Configurar en Replit
Agregar variable de entorno:
```
ANTIGRAVITY_BRIDGE_URL=https://random-name.trycloudflare.com
```

---

## Archivos en Replit

| Archivo | Ruta | Descripción |
|---------|------|-------------|
| antigravity_client.py | `BUNK3R_IA/core/` | Cliente HTTP para el bridge |
| ai_service.py | `BUNK3R_IA/core/` | Modificado para incluir Antigravity como provider |
| config.py | `BUNK3R_IA/` | Variables de configuración añadidas |

---

## Comandos Rápidos

```powershell
# Terminal 1 - Bridge
cd C:\Users\Asus\Documents\Proyectos\AntigravityBridge
python antigravity_bridge.py

# Terminal 2 - Túnel
cloudflared tunnel --url http://localhost:8888

# Verificar (desde cualquier lugar)
curl https://URL.trycloudflare.com/health
```

---

## Troubleshooting

### El bridge no encuentra la ventana de Antigravity
- Asegúrate de que el título de la ventana contenga "Antigravity"
- Modifica `ANTIGRAVITY_WINDOW_TITLE` en el script si es diferente

### Error de permisos con pyautogui
- Ejecuta PowerShell como Administrador

### Cloudflared no se encuentra
- Agrega la carpeta donde está cloudflared.exe al PATH
- O ejecuta con ruta completa: `C:\ruta\cloudflared.exe tunnel --url http://localhost:8888`

---

## Resumen

| Aspecto | Detalle |
|---------|---------|
| **Objetivo** | Usar Antigravity como motor principal de IA |
| **Método** | Automatización GUI + Clipboard + Cloudflare Tunnel |
| **Costo** | 100% Gratis |
| **Requisito Principal** | PC encendida con Antigravity abierto |
| **Modo actual** | Clipboard (sin OCR por compatibilidad Python 3.14) |
| **Fallback** | Proveedores actuales (Groq, DeepSeek, Gemini, etc.) |

---

**Última actualización:** 17 Diciembre 2025
**Versión:** 2.1 (Clipboard Mode)
**Estado:** Configuración en progreso - esperando Cloudflared
