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
        pyautogui.hotkey('ctrl', 'shift', 'l')
        time.sleep(1.0)
    
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
    
    def _clean_response(self, full_text: str, prompt: str) -> str:
        """Filtra el texto copiado para devolver solo la respuesta nueva"""
        try:
            if not full_text:
                return ""
                
            # 1. Quitar el prompt y todo lo anterior
            # Intentamos encontrar la última ocurrencia del prompt (o parte de él)
            prompt_clean = prompt.strip()
            last_index = -1
            
            # Buscamos por el prompt completo primero
            if prompt_clean:
                last_index = full_text.rfind(prompt_clean)
            
            # Si no lo encontramos, intentamos con las últimas líneas del prompt por si Antigravity lo recortó
            if last_index == -1 and prompt_clean:
                lines = [l for l in prompt_clean.split('\n') if l.strip()]
                if lines:
                    last_line = lines[-1]
                    last_index = full_text.rfind(last_line)
            
            if last_index != -1:
                # El texto real empieza después del prompt
                # Pero a veces Antigravity repite el prompt en el área de respuesta
                # Saltamos esa parte
                raw_response = full_text[last_index:].split(prompt_clean, 1)[-1] if prompt_clean in full_text[last_index:] else full_text[last_index + len(prompt_clean):]
            else:
                raw_response = full_text

            # 2. Eliminar el bloque de razonamiento ("Thought for X s")
            # Usamos regex para atrapar "Thought for 4s", "Thought for 10s", etc.
            raw_response = re.sub(r'Thought for \d+s\s+', '', raw_response, flags=re.IGNORECASE)
            # También variaciones comunes
            raw_response = re.sub(r'Pensado durante \d+s\s+', '', raw_response, flags=re.IGNORECASE)
            
            # 3. Eliminar basura de la interfaz (botones de abajo)
            # Antigravity suele poner "Good Bad Add context Images Mentions..." al final
            ui_markers = [
                "Good\nBad", "Good Bad", 
                "Add context", "Images", "Mentions", "Workflows",
                "Conversation mode", "Planning", "Fast",
                "Gemini 3 Pro", "Model", "View plans"
            ]
            
            clean_lines = []
            for line in raw_response.split('\n'):
                line_strip = line.strip()
                # Si encontramos un marcador de UI, dejamos de procesar líneas
                if any(marker in line_strip for marker in ui_markers) and len(line_strip) < 50:
                    break
                clean_lines.append(line)
            
            final_response = "\n".join(clean_lines).strip()
            
            # 4. Limpieza final de etiquetas de sistema/usuario si quedaron
            final_response = re.sub(r'^\[Asistente\]\s*', '', final_response, flags=re.IGNORECASE)
            final_response = re.sub(r'^\[Assistant\]\s*', '', final_response, flags=re.IGNORECASE)
            
            return final_response
            
        except Exception as e:
            print(f"Error limpiando respuesta: {e}")
            return full_text

    def process_query(self, prompt: str) -> dict:
        if self.is_processing:
            return {"error": "Ya hay una consulta en proceso", "status": "busy"}
        
        try:
            self.is_processing = True
            
            self.activate_window()
            self.open_agent_panel()
            self.send_query(prompt)
            
            full_response = self.wait_and_extract_response()
            
            # Limpiamos la respuesta para quitar historial y prompt
            clean_response = self._clean_response(full_response, prompt)
            
            code_blocks = self.extract_code_blocks(clean_response)
            
            return {
                "response": clean_response,
                "full_clipboard": full_response, # Guardamos el original por si acaso
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
