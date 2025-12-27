"""
AI Service - Multi-provider AI chat service with automatic fallback
Supports: DeepSeek, Groq, Google Gemini, Cerebras, Hugging Face
All providers offer free tiers
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Optional, Dict, List, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Global variable to store database manager
db_manager = None

try:
    from BUNK3R_IA.core.ai_flow_logger import flow_logger
except ImportError:
    flow_logger = None

class AIProvider(ABC):
    """Base class for AI providers"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.name = "base"
        self.available = bool(api_key)
    
    @abstractmethod
    def chat(self, messages: List[Dict], system_prompt: Optional[str] = None) -> Dict:
        """Send chat request and return response"""
        pass
    
    def is_available(self) -> bool:
        return self.available


class DeepSeekV32Provider(AIProvider):
    """DeepSeek V3.2 via Hugging Face - Main AI Model"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "deepseek-v3.2"
        self.model = "deepseek-ai/DeepSeek-V3.2"
        self.base_url = "https://router.huggingface.co/hf"
    
    def chat(self, messages: List[Dict], system_prompt: Optional[str] = None) -> Dict:
        try:
            import requests
            
            prompt = ""
            if system_prompt:
                prompt = f"<|system|>\n{system_prompt}<|end|>\n"
            
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    prompt += f"<|user|>\n{content}<|end|>\n"
                elif role == "assistant":
                    prompt += f"<|assistant|>\n{content}<|end|>\n"
            
            prompt += "<|assistant|>\n"
            
            response = requests.post(
                f"{self.base_url}/{self.model}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 4096,
                        "temperature": 0.75,
                        "top_p": 0.92,
                        "return_full_text": False,
                        "do_sample": True,
                        "repetition_penalty": 1.1
                    }
                },
                timeout=180
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    text = result[0].get("generated_text", "")
                    return {"success": True, "response": text, "provider": self.name}
                return {"success": False, "error": "Invalid response format", "provider": self.name}
            elif response.status_code == 503:
                return {"success": False, "error": "Model is loading, please wait", "provider": self.name}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}", "provider": self.name}
                
        except Exception as e:
            logger.error(f"DeepSeek V3.2 error: {e}")
            return {"success": False, "error": str(e), "provider": self.name}


class HuggingFaceProvider(AIProvider):
    """Hugging Face Inference API - Free tier ~1000 req/day"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "huggingface"
        self.model = "meta-llama/Meta-Llama-3-8B-Instruct"
        self.base_url = "https://router.huggingface.co/hf"
    
    def chat(self, messages: List[Dict], system_prompt: Optional[str] = None) -> Dict:
        try:
            import requests
            
            prompt = ""
            if system_prompt:
                prompt = f"<|system|>\n{system_prompt}</s>\n"
            
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    prompt += f"<|user|>\n{content}</s>\n"
                elif role == "assistant":
                    prompt += f"<|assistant|>\n{content}</s>\n"
            
            prompt += "<|assistant|>\n"
            
            response = requests.post(
                f"{self.base_url}/{self.model}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 1024,
                        "temperature": 0.7,
                        "return_full_text": False
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    text = result[0].get("generated_text", "")
                    return {"success": True, "response": text, "provider": self.name}
                return {"success": False, "error": "Invalid response format", "provider": self.name}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}", "provider": self.name}
                
        except Exception as e:
            logger.error(f"HuggingFace error: {e}")
            return {"success": False, "error": str(e), "provider": self.name}


class GroqProvider(AIProvider):
    """Groq API - Free tier, very fast inference - Using Llama 3.3 70B"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "groq"
        self.model = "llama-3.3-70b-versatile"
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def chat(self, messages: List[Dict], system_prompt: Optional[str] = None) -> Dict:
        try:
            import requests
            
            chat_messages = []
            if system_prompt:
                chat_messages.append({"role": "system", "content": system_prompt})
            chat_messages.extend(messages)
            
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": chat_messages,
                    "temperature": 0.7,
                    "max_tokens": 8192
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"success": True, "response": text, "provider": self.name}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}", "provider": self.name}
                
        except Exception as e:
            logger.error(f"Groq error: {e}")
            return {"success": False, "error": str(e), "provider": self.name}


class GeminiProvider(AIProvider):
    """Google Gemini API - Using Gemini 2.0 Flash for speed and quality"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "gemini"
        self.model = "gemini-2.0-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
    
    def chat(self, messages: List[Dict], system_prompt: Optional[str] = None) -> Dict:
        try:
            import requests
            
            contents = []
            for msg in messages:
                role = "user" if msg.get("role") == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.get("content", "")}]
                })
            
            payload = {"contents": contents}
            
            if system_prompt:
                payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
            
            payload["generationConfig"] = {
                "temperature": 0.7,
                "maxOutputTokens": 8192
            }
            
            response = requests.post(
                f"{self.base_url}/{self.model}:generateContent?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                candidates = result.get("candidates", [])
                if candidates:
                    text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    return {"success": True, "response": text, "provider": self.name}
                return {"success": False, "error": "No candidates in response", "provider": self.name}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}", "provider": self.name}
                
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return {"success": False, "error": str(e), "provider": self.name}


class CerebrasProvider(AIProvider):
    """Cerebras API - Using Llama 3.3 70B for best reasoning"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "cerebras"
        self.model = "llama-3.3-70b"
        self.base_url = "https://api.cerebras.ai/v1/chat/completions"
    
    def chat(self, messages: List[Dict], system_prompt: Optional[str] = None) -> Dict:
        try:
            import requests
            
            chat_messages = []
            if system_prompt:
                chat_messages.append({"role": "system", "content": system_prompt})
            chat_messages.extend(messages)
            
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": chat_messages,
                    "temperature": 0.7,
                    "max_tokens": 8192
                },
                timeout=90
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"success": True, "response": text, "provider": self.name}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}", "provider": self.name}
                
        except Exception as e:
            logger.error(f"Cerebras error: {e}")
            return {"success": False, "error": str(e), "provider": self.name}


class OpenAIProvider(AIProvider):
    """OpenAI GPT API"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "openai"
        self.model = "gpt-4o-mini"
        self.base_url = "https://api.openai.com/v1/chat/completions"
    
    def chat(self, messages: List[Dict], system_prompt: Optional[str] = None) -> Dict:
        try:
            import requests
            
            chat_messages = []
            if system_prompt:
                chat_messages.append({"role": "system", "content": system_prompt})
            chat_messages.extend(messages)
            
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": chat_messages,
                    "temperature": 0.7,
                    "max_tokens": 8192
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"success": True, "response": text, "provider": self.name}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}", "provider": self.name}
                
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return {"success": False, "error": str(e), "provider": self.name}


class BaiduProvider(AIProvider):
    """Baidu Qianfan API"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "baidu"
        self.model = "ernie-3.5-8k"
        self.base_url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie-3.5-8k"
    
    def chat(self, messages: List[Dict], system_prompt: Optional[str] = None) -> Dict:
        try:
            import requests
            
            chat_messages = []
            for msg in messages:
                role = "user" if msg.get("role") == "user" else "assistant"
                chat_messages.append({"role": role, "content": msg.get("content", "")})
            
            payload = {"messages": chat_messages}
            
            response = requests.post(
                f"{self.base_url}?access_token={self.api_key}",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get("result", "")
                return {"success": True, "response": text, "provider": self.name}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}", "provider": self.name}
                
        except Exception as e:
            logger.error(f"Baidu error: {e}")
            return {"success": False, "error": str(e), "provider": self.name}


class DeepSeekProvider(AIProvider):
    """DeepSeek API - UPGRADED for better reasoning with more tokens"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "deepseek"
        self.model = "deepseek-chat"
        self.base_url = "https://api.deepseek.com/chat/completions"
    
    def chat(self, messages: List[Dict], system_prompt: Optional[str] = None) -> Dict:
        try:
            import requests
            
            chat_messages = []
            if system_prompt:
                chat_messages.append({"role": "system", "content": system_prompt})
            chat_messages.extend(messages)
            
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": chat_messages,
                    "temperature": 0.7,
                    "max_tokens": 8192
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"success": True, "response": text, "provider": self.name}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}", "provider": self.name}
                
        except Exception as e:
            logger.error(f"DeepSeek error: {e}")
            return {"success": False, "error": str(e), "provider": self.name}


class AntigravityBridgeProvider:
    """Antigravity via Bridge - Uses Google Antigravity on user's PC"""
    
    def __init__(self):
        from .antigravity_client import AntigravityProvider
        self._provider = AntigravityProvider()
        self.name = "antigravity"
    
    @property
    def available(self) -> bool:
        return self._provider.available
    
    def is_available(self) -> bool:
        return self._provider.is_available()
    
    def chat(self, messages: List[Dict], system_prompt: Optional[str] = None) -> Dict:
        return self._provider.chat(messages, system_prompt) # type: ignore
    
    def refresh(self):
        self._provider.refresh_availability()


class OllamaProvider(AIProvider):
    """Local Ollama API Provider - Running on user's PC"""
    
    def __init__(self, model: str = None, base_url: str = None):
        super().__init__("local-ollama")
        self.name = "ollama"
        from BUNK3R_IA.config import get_config
        conf = get_config()
        self.model = model or getattr(conf, 'OLLAMA_MODEL', 'llama3.2')
        self.base_url = (base_url or getattr(conf, 'OLLAMA_BASE_URL', 'http://localhost:11434')).rstrip('/') + '/api/chat'
        self.available = True # We check availability via health check
    
    def is_available(self) -> bool:
        try:
            import requests
            # Simple check to see if the server is up
            response = requests.get(self.base_url.replace("/api/chat", "/api/tags"), timeout=2)
            return response.status_code == 200
        except:
            return False

    def chat(self, messages: List[Dict], system_prompt: Optional[str] = None) -> Dict:
        try:
            import requests
            
            chat_messages = []
            if system_prompt:
                chat_messages.append({"role": "system", "content": system_prompt})
            
            # Formatear mensajes para Ollama
            for msg in messages:
                chat_messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
            
            response = requests.post(
                self.base_url,
                json={
                    "model": self.model,
                    "messages": chat_messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 4096
                    }
                },
                timeout=180
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get("message", {}).get("content", "")
                return {"success": True, "response": text, "provider": self.name}
            else:
                return {"success": False, "error": f"Ollama HTTP {response.status_code}", "provider": self.name}
                
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return {"success": False, "error": str(e), "provider": self.name}


class AIService:
    """
    Multi-provider AI service with automatic fallback
    Manages conversation history and persistence
    BUNK3R AI - Sistema de IA Avanzado con Capacidades de los 15 Volumenes
    """
    
    DEFAULT_SYSTEM_PROMPT = """# BUNK3R AI - Agente de Análisis de Código & Explorador de Repositorios

Soy BUNK3R AI, un agente diseñado para ENTENDER y OPERAR sobre el código fuente real. Mi inteligencia se basa en la observación directa de los archivos, no en suposiciones.

## PROTOCOLO DE ANÁLISIS DINÁMICO
Cada vez que recibo una petición relacionada con el código o la estructura del proyecto, ejecuto este flujo:
1. **LOCALIZACIÓN**: Si no sé dónde está la lógica mencionada, uso `search_code` para encontrar archivos relevantes.
2. **EXPLORACIÓN**: Si necesito conocer el contexto de una carpeta, uso `list_dir`.
3. **LECTURA CRÍTICA**: **DEBO LEER** el contenido de los archivos usando `read_file` antes de dar cualquier explicación o realizar cambios. Analizo imports, lógica de negocio y patrones.
4. **COMPRENSIÓN**: Una vez leído el código, entiendo CÓMO funciona y CÓMO se integra en el resto del sistema.
5. **EJECUCIÓN**: Solo después de este análisis, propongo o realizo ediciones (`edit_file`) o creaciones (`write_file`).

## REGLAS DE ORO
- **No adivino**: Si el usuario pregunta "cómo funciona X", mi primera acción es buscar y leer el código de X.
- **Contexto Real**: Baso mis respuestas en lo que leo en el repositorio en ese preciso instante.
- **Herramientas de Ojos**: `read_file`, `list_dir` y `search_code` son mis ojos. Las uso constantemente.

Mi objetivo es ser el colaborador más preciso, actuando siempre sobre la realidad del código fuente."""

    def __init__(self, db_manager=None):
        from BUNK3R_IA.core.ai_toolkit import AIFileToolkit, AICommandExecutor
        
        logger.info(f"AIService starting init with db_manager={'available' if db_manager else 'None'}")
        self.db_manager = db_manager
        self.providers: List[AIProvider] = []
        self.conversations: Dict[str, List[Dict]] = {}

        
        # Inicializar Toolkits
        self.file_toolkit = AIFileToolkit()
        self.command_executor = AICommandExecutor()
        
        # Providers will be initialized below in __init__

    
        # Priority 0: Local Ollama (The Brain)
        try:
            ollama_provider = OllamaProvider()
            if ollama_provider.is_available():
                self.providers.append(ollama_provider)
                logger.info("Ollama provider initialized (Priority 0 - The Brain)")
        except Exception as e:
            logger.warning(f"Could not initialize Ollama provider: {e}")

        # Priority 1: Antigravity Bridge (free, unlimited, user's PC)
        antigravity_url = os.environ.get('ANTIGRAVITY_BRIDGE_URL', 'http://localhost:8888')
        if antigravity_url:
            try:
                antigravity_provider = AntigravityBridgeProvider()
                if antigravity_provider.available:
                    self.providers.append(antigravity_provider) # type: ignore
                    logger.info("Antigravity Bridge provider initialized (Priority 1)")
            except Exception as e:
                logger.warning(f"Could not initialize Antigravity provider: {e}")
        
        # Priority 1: Groq (fast, reliable, Llama 3.3 70B)
        groq_key = os.environ.get('GROQ_API_KEY', '')
        if groq_key:
            self.providers.append(GroqProvider(groq_key))
            logger.info("Groq provider initialized (Priority 1)")
        
        # Priority 2: Cerebras (fast, Llama 3.3 70B)
        cerebras_key = os.environ.get('CEREBRAS_API_KEY', '')
        if cerebras_key:
            self.providers.append(CerebrasProvider(cerebras_key))
            logger.info("Cerebras provider initialized (Priority 2)")
        
        # Priority 3: OpenAI GPT
        openai_key = os.environ.get('OPENAI_API_KEY', '')
        if openai_key:
            self.providers.append(OpenAIProvider(openai_key))
            logger.info("OpenAI provider initialized (Priority 3)")

        # Priority GitHub: GitHub Token for AI Constructor
        github_token = os.environ.get('GITHUB_TOKEN', '')
        if github_token:
            logger.info("GitHub Token detected and ready for AI Constructor")
        
        # Priority 4: Gemini
        gemini_key = os.environ.get('GEMINI_API_KEY', '')
        if gemini_key:
            self.providers.append(GeminiProvider(gemini_key))
            logger.info("Gemini provider initialized (Priority 4)")
        
        # Priority 5: Baidu
        baidu_key = os.environ.get('BAIDU_API_KEY', '')
        if baidu_key:
            self.providers.append(BaiduProvider(baidu_key))
            logger.info("Baidu provider initialized (Priority 5)")
        
        # Fallback: DeepSeek API
        deepseek_key = os.environ.get('DEEPSEEK_API_KEY', '')
        if deepseek_key:
            self.providers.append(DeepSeekProvider(deepseek_key))
            logger.info("DeepSeek API provider initialized (Priority 6)")
        
        # Priority 7: HuggingFace Llama (fallback)
        hf_key = os.environ.get('HUGGINGFACE_API_KEY', '')
        if hf_key:
            self.providers.append(HuggingFaceProvider(hf_key))
            logger.info("HuggingFace Llama provider initialized (Priority 7)")
        
        if not self.providers:
            logger.warning("No AI providers configured. Set API keys in environment variables.")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names"""
        return [p.name for p in self.providers if p.is_available()]
    
    def _detect_response_issues(self, response: str, original_message: str) -> Dict:
        """
        Detecta problemas en la respuesta de la IA que requieren auto-rectificación
        
        Returns:
            Dict con 'needs_fix': bool y 'issues': lista de problemas detectados
        """
        issues = []
        response_lower = response.lower().strip()
        
        if len(response) < 20:
            issues.append("respuesta_muy_corta")
        
        incomplete_markers = [
            "...", "continuará", "continua", "[continua", "(continua",
            "etc etc", "y así", "y asi"
        ]
        if any(marker in response_lower[-100:] for marker in incomplete_markers):
            issues.append("respuesta_incompleta")
        
        if response.count("```") % 2 != 0:
            issues.append("codigo_sin_cerrar")
        
        error_phrases = [
            "no puedo", "no tengo acceso", "como ia", "como modelo de lenguaje",
            "no tengo la capacidad", "no me es posible"
        ]
        if any(phrase in response_lower[:200] for phrase in error_phrases):
            if "?" in original_message.lower() or any(kw in original_message.lower() 
                for kw in ["cómo", "como", "qué", "que", "ayuda", "help"]):
                issues.append("rechazo_innecesario")
        
        confusion_markers = [
            "no entiendo", "no está claro", "podrías aclarar", "podrias aclarar",
            "no estoy seguro de qué", "no estoy seguro de que"
        ]
        if any(marker in response_lower for marker in confusion_markers):
            if len(original_message) > 50:
                issues.append("confusion_evitable")
        
        return {
            "needs_fix": len(issues) > 0,
            "issues": issues
        }
    
    def _auto_git_push(self, change_desc: str):
        """Sube cambios a GitHub automáticamente"""
        try:
            github_token = os.environ.get('GITHUB_TOKEN')
            if not github_token:
                logger.warning("Auto-Git: No GITHUB_TOKEN configured. Skipping push.")
                return False
                
            repo_url = f"https://{github_token}@github.com/PrincipeGhost/BUNK3R-IA.git"
            
            # 1. Configurar identidad si falta (opcional, pero seguro)
            self.command_executor.run_command("git config user.email 'bunk3r-ai@autonomous.system'")
            self.command_executor.run_command("git config user.name 'BUNK3R AI'")
            
            # 2. Add
            self.command_executor.run_command("git add .")
            
            # 3. Commit
            commit_msg = f"AI Auto-Update: {change_desc} [{int(time.time())}]"
            self.command_executor.run_command(f'git commit -m "{commit_msg}"')
            
            # 4. Push
            res = self.command_executor.run_command(f"git push {repo_url} main")
            
            if res.get("success"):
                logger.info("Auto-Git Push completado.")
                return True
            else:
                logger.error(f"Auto-Git Push falló: {res.get('error') or res.get('stderr')}")
                return False
        except Exception as e:
            logger.error(f"Excepción en Auto-Git Push: {e}")
            return False

    def _call_tool(self, tool_name: str, args: Dict) -> str:
        """Ejecuta una herramienta localmente"""
        try:
            logger.info(f"Ejecutando herramienta: {tool_name} con args: {args}")
            
            result = {}
            modified_fs = False
            
            if tool_name == "read_file":
                result = self.file_toolkit.read_file(**args)
            elif tool_name == "write_file":
                result = self.file_toolkit.write_file(**args)
                modified_fs = True
            elif tool_name == "edit_file":
                result = self.file_toolkit.edit_file(**args)
                modified_fs = True
            elif tool_name == "list_dir":
                result = self.file_toolkit.list_directory(**args)
            elif tool_name == "delete_file":
                result = self.file_toolkit.delete_file(**args)
                modified_fs = True
            elif tool_name == "run_command":
                result = self.command_executor.run_command(**args)
            elif tool_name == "install_package":
                result = self.command_executor.install_package(**args)
            else:
                return f"Error: Herramienta '{tool_name}' no encontrada."
            
            if result.get("success"):
                output_msg = f"[TOOL OUTPUT SUCCESS]\n{json.dumps(result, indent=2)}"
                
                # Auto-Push si hubo cambios en archivos
                if modified_fs:
                    push_success = self._auto_git_push(f"{tool_name} on {args.get('path', 'unknown')}")
                    if push_success:
                        output_msg += "\n[GIT] Cambios sincronizados con GitHub correctamente."
                    else:
                        output_msg += "\n[GIT WARNING] No se pudo sincronizar con GitHub."
                
                return output_msg
            else:
                return f"[TOOL OUTPUT ERROR]\n{result.get('error')}"
                
        except Exception as e:
            return f"[TOOL EXECUTION EXCEPTION] {str(e)}"
        
        return {}

    def chat(self, user_id: str, message: str, system_prompt: Optional[str] = None, 
             preferred_provider: Optional[str] = None, user_context: Optional[Dict] = None,
             enable_auto_rectify: bool = True) -> Dict[str, Any]:
        """
        Flujo de Chat: El Cerebro (Ollama) analiza y delega.
        """
        if not self.providers:
            return {
                "success": False,
                "error": "No hay proveedores de IA configurados. Configura las claves API.",
                "provider": None
            }
        
        # 1. Obtener historial
        conversation = self._get_conversation(user_id)
        conversation.append({"role": "user", "content": message})
        
        # 2. El Cerebro (Ollama) analiza la petición (Prioridad 0)
        brain = next((p for p in self.providers if p.name == "ollama"), None)
        
        # Inyectar contexto del repositorio para que la IA entienda el proyecto
        repo_context = ""
        try:
            from BUNK3R_IA.core.ai_project_context import AIProjectContext
            # Usar un ID de sesión genérico para el contexto global
            ctx = AIProjectContext("global_user", "bunk3r_ia")
            repo_context = ctx.get_context_summary()
        except Exception as e:
            logger.error(f"Error obteniendo contexto del repositorio: {e}")

        system = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        if repo_context:
            system = f"{system}\n\n{repo_context}"
        
        if brain and brain.is_available():
            logger.info("🧠 Cerebro (Ollama) activado para analizar la petición...")
        
        if user_context:
            context_info = self._build_user_context(user_context)
            system = system + context_info
        
        providers_to_try = self.providers.copy()
        if preferred_provider:
            providers_to_try.sort(key=lambda p: 0 if p.name == preferred_provider else 1)
        
        # Bucle de Agente (Max 5 pasos para evitar loops infinitos)
        MAX_TOOL_STEPS = 5
        final_response = ""
        provider_used = "unknown"
        
        for step in range(MAX_TOOL_STEPS + 1):
            # 1. Obtener respuesta de la IA
            response_success = False
            current_response_text = ""
            
            for provider in providers_to_try:
                if not provider.is_available():
                    continue
                
                try:
                    logger.info(f"Using provider: {provider.name} (Step {step})")
                    result = provider.chat(conversation, system)
                    
                    if result.get("success"):
                        current_response_text = result.get("response", "")
                        provider_used = provider.name
                        response_success = True
                        break
                except Exception as e:
                    logger.error(f"Provider {provider.name} failed: {e}")
            
            if not response_success:
                 return {
                    "success": False,
                    "error": "Todos los proveedores fallaron.",
                    "provider": None
                }
            
            # 2. Detectar si la IA quiere usar una herramienta
            import re
            tool_match = re.search(r'<TOOL>(.*?)</TOOL>', current_response_text, re.DOTALL)
            
            if tool_match and step < MAX_TOOL_STEPS:
                # 2a. Ejecutar herramienta
                tool_json_str = tool_match.group(1).strip()
                tool_output = ""
                
                try:
                    if "```" in tool_json_str:
                         tool_json_str = tool_json_str.replace("```json", "").replace("```", "")
                    
                    tool_call = json.loads(tool_json_str)
                    tool_name = tool_call.get("name")
                    tool_args = tool_call.get("args", {})
                    
                    # Ejecutar
                    tool_output = self._call_tool(tool_name, tool_args)
                    
                except Exception as e:
                    tool_output = f"[SYSTEM ERROR] JSON inválido en <TOOL>: {e}"
                
                # 2b. Añadir al historial y continuar el bucle
                conversation.append({"role": "assistant", "content": current_response_text})
                self._save_conversation(user_id, conversation)
                
                tool_feedback_msg = f"[SISTEMA] Resultado de la herramienta:\n{tool_output}\n\nContinúa tu tarea."
                conversation.append({"role": "user", "content": tool_feedback_msg})
                
                logger.info(f"Tool Loop Feedback sent. Output len: {len(tool_output)}")
                continue 
            
            else:
                # 3. Respuesta final
                final_response = current_response_text
                
                conversation.append({"role": "assistant", "content": final_response})
                self._save_conversation(user_id, conversation)
                
                return {
                    "success": True,
                    "response": final_response,
                    "provider": provider_used,
                    "conversation_length": len(conversation),
                    "steps_taken": step
                }
    
    def _build_user_context(self, user_context: Dict) -> str:
        """Build context string based on user information"""
        name = user_context.get("name", "Usuario")
        is_owner = user_context.get("is_owner", False)
        is_admin = user_context.get("is_admin", False)
        
        context = "\n\n[CONTEXTO DEL USUARIO]\n"
        
        if is_owner:
            context += f"""Usuario: {name} (OWNER)
Nivel: MAXIMO - Responde con detalle tecnico completo, ofrece sugerencias proactivas, tono de socio de confianza."""
        elif is_admin:
            context += f"""Usuario: {name} (ADMIN)
Nivel: ALTO - Responde con detalle tecnico, enfocate en operaciones y soporte, tono profesional."""
        else:
            context += f"""Usuario: {name}
Nivel: ESTANDAR - Responde claro y amigable, evita jerga tecnica, tono servicial."""
        
        return context + "\n"
    
    def _get_conversation(self, user_id: str) -> List[Dict]:
        """Get conversation history for user"""
        if user_id not in self.conversations:
            if self.db_manager:
                history = self._load_conversation_from_db(user_id)
                self.conversations[user_id] = history
            else:
                self.conversations[user_id] = []
        return self.conversations[user_id]
    
    def _save_conversation(self, user_id: str, conversation: List[Dict]):
        """Save conversation to memory and database"""
        self.conversations[user_id] = conversation
        
        if self.db_manager:
            self._save_conversation_to_db(user_id, conversation)
    
    def _load_conversation_from_db(self, user_id: str) -> List[Dict]:
        """Load conversation history from database"""
        try:
            if not self.db_manager:
                return []
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT role, content FROM ai_chat_messages
                        WHERE user_id = %s
                        ORDER BY created_at ASC
                        LIMIT 50
                    """, (user_id,))
                    rows = cur.fetchall()
                    return [{"role": row[0], "content": row[1]} for row in rows]
        except Exception as e:
            logger.error(f"Error loading conversation from DB: {e}")
            return []
    
    def _save_conversation_to_db(self, user_id: str, conversation: List[Dict]):
        """Save latest messages to database"""
        try:
            if not self.db_manager or len(conversation) < 2:
                return
            
            last_two = conversation[-2:]
            
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    for msg in last_two:
                        cur.execute("""
                            INSERT INTO ai_chat_messages (user_id, role, content, created_at)
                            VALUES (%s, %s, %s, %s)
                        """, (user_id, msg["role"], msg["content"], datetime.now()))
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving conversation to DB: {e}")
    
    def clear_conversation(self, user_id: str) -> bool:
        """Clear conversation history for user"""
        try:
            if user_id in self.conversations:
                del self.conversations[user_id]
            
            if self.db_manager:
                conn = self.db_manager.get_connection()
                if conn:
                    with conn as c:
                        with c.cursor() as cur:
                            cur.execute("DELETE FROM ai_chat_messages WHERE user_id = %s", (user_id,))
                        c.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error clearing conversation: {e}")
            return False
    
    def get_conversation_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get conversation history for user"""
        conversation = self._get_conversation(user_id)
        return conversation[-limit:] if len(conversation) > limit else conversation
    
    def get_stats(self) -> Dict:
        """Get AI service statistics"""
        return {
            "providers_available": self.get_available_providers(),
            "total_providers": len(self.providers),
            "active_conversations": len(self.conversations)
        }
    
    def generate_code(self, user_id: str, message: str, current_files: Dict[str, str], 
                      project_name: str) -> Dict:
        """
        Generate code for web projects based on user instructions.
        Returns files to create/update and a response message.
        """
        if not self.providers:
            return {
                "success": False,
                "error": "No hay proveedores de IA configurados.",
                "provider": None
            }
        
        files_context = ""
        for filename, content in current_files.items():
            preview = content[:500] + "..." if len(content) > 500 else content
            files_context += f"\n--- {filename} ---\n{preview}\n"
        
        code_system_prompt = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    BUNK3R CODE BUILDER - ELITE WEB ARCHITECT                  ║
║         Generador de Interfaces Premium | Nivel Binance/Revolut/N26          ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Eres BUNK3R Code Builder, un arquitecto de interfaces web de nivel ELITE.
Tu trabajo es crear experiencias digitales que parezcan de startups valoradas en millones.
Cada linea de codigo que generas debe reflejar calidad profesional Fintech/Neo-bank.

═══════════════════════════════════════════════════════════════════════════════
SECCION 1: PROCESO DE PENSAMIENTO (OBLIGATORIO)
═══════════════════════════════════════════════════════════════════════════════

ANTES de generar codigo, SIEMPRE incluye un mini-blueprint en el campo "message":

1. ENTIENDO: Que exactamente quiere el usuario?
2. ESTRUCTURA: Que componentes/secciones necesito?
3. DECISION: Por que elijo este enfoque?

Esto demuestra tu proceso de razonamiento profesional.

═══════════════════════════════════════════════════════════════════════════════
SECCION 2: FORMATO DE RESPUESTA OBLIGATORIO
═══════════════════════════════════════════════════════════════════════════════

Responde SIEMPRE en formato JSON valido:
{{
    "files": {{
        "index.html": "<!DOCTYPE html>...",
        "styles.css": "/* CSS completo */...",
        "script.js": "// JS completo..."
    }},
    "message": "[BLUEPRINT] Entiendo que necesitas X. He creado Y componentes con Z enfoque. Justificacion: ..."
}}

═══════════════════════════════════════════════════════════════════════════════
SECCION 3: SISTEMA DE DISENO BUNK3R (OBLIGATORIO)
═══════════════════════════════════════════════════════════════════════════════

3.1 PALETA DE COLORES NEO-BANK:
--bg-primary: #0B0E11 (fondo principal, ultra oscuro)
--bg-secondary: #12161C (cards, modales)
--bg-tertiary: #1E2329 (hover states)
--bg-elevated: #2B3139 (elementos elevados)
--accent-primary: #F0B90B (dorado principal)
--accent-hover: #FCD535 (dorado hover)
--accent-active: #D4A20B (dorado pressed)
--text-primary: #FFFFFF
--text-secondary: #848E9C
--text-muted: #5E6673
--success: #22C55E
--error: #EF4444
--warning: #F59E0B

3.2 TIPOGRAFIA:
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
Headings: font-weight: 600-700, letter-spacing: -0.02em
Body: font-weight: 400-500, line-height: 1.6
Small: font-size: 0.875rem, line-height: 1.4

3.3 EFECTOS PREMIUM (USAR SIEMPRE):
- Glass morphism: backdrop-filter: blur(12px); background: rgba(18,22,28,0.85)
- Sombras suaves: box-shadow: 0 8px 32px rgba(0,0,0,0.4)
- Bordes sutiles: border: 1px solid rgba(255,255,255,0.08)
- Transiciones: transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1)
- Hover lift: transform: translateY(-2px)
- Glow dorado: box-shadow: 0 0 24px rgba(240,185,11,0.25)
- Gradientes: linear-gradient(135deg, #F0B90B 0%, #D4A20B 100%)

3.4 COMPONENTES OBLIGATORIOS:
- CARDS: border-radius: 16px; padding: 24px; hover con elevacion
- BOTONES PRIMARIOS: background dorado, border-radius: 12px, font-weight: 600
- BOTONES SECUNDARIOS: borde dorado, fondo transparente
- INPUTS: fondo oscuro, borde sutil, focus con glow dorado
- BADGES: pill shape, colores semanticos
- ICONOS: SVG inline, stroke-width: 1.5, currentColor

3.5 ANIMACIONES:
@keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
@keyframes slideUp {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
@keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} }}
@keyframes shimmer {{ from {{ background-position: -200% 0; }} to {{ background-position: 200% 0; }} }}

═══════════════════════════════════════════════════════════════════════════════
SECCION 4: ESTANDARES DE CODIGO
═══════════════════════════════════════════════════════════════════════════════

4.1 HTML5 SEMANTICO:
- Estructura: header > nav > main > section > footer
- Accesibilidad: aria-labels, roles, alt texts obligatorios
- Meta tags: viewport, charset, description, theme-color

4.2 CSS MODERNO:
- Variables CSS en :root
- Mobile-first con media queries
- Flexbox y Grid como base
- Animaciones con @keyframes
- PROHIBIDO: !important, IDs para estilos, inline styles

4.3 JAVASCRIPT ES6+:
- const/let exclusivamente
- Arrow functions
- Template literals
- Async/await para asincronía
- Event delegation
- Modulos cuando sea posible

═══════════════════════════════════════════════════════════════════════════════
SECCION 5: CONTEXTO DEL PROYECTO
═══════════════════════════════════════════════════════════════════════════════

PROYECTO: {project_name}
ARCHIVOS EXISTENTES:
{files_context if files_context else "(Proyecto nuevo, crear desde cero)"}

═══════════════════════════════════════════════════════════════════════════════
SECCION 6: REGLAS CRITICAS
═══════════════════════════════════════════════════════════════════════════════

1. CODIGO COMPLETO: Nunca fragmentos, siempre archivos completos y funcionales
2. CALIDAD VISUAL: Cada pixel debe parecer de app de millones de dolares
3. RESPONSIVE: Funciona perfectamente en mobile, tablet y desktop
4. ACCESIBLE: Navegable con teclado, screen readers compatibles
5. PERFORMANTE: Lazy loading, optimizacion de animaciones
6. PROFESIONAL: Sin errores de consola, sin warnings

═══════════════════════════════════════════════════════════════════════════════
SECCION 7: EJEMPLO DE RESPUESTA EXCELENTE
═══════════════════════════════════════════════════════════════════════════════

Usuario pide: "Hazme una landing page para mi app de crypto"

Respuesta correcta:
{{
    "files": {{
        "index.html": "<!DOCTYPE html><html lang='es'>... (HTML completo con header, hero, features, CTA, footer)...",
        "styles.css": ":root {{ --bg-primary: #0B0E11; ... }} * {{ margin: 0; ... }} .hero {{ ... }} (CSS completo)",
        "script.js": "// Animaciones y interacciones\\nconst initAnimations = () => {{ ... }}; (JS completo)"
    }},
    "message": "[BLUEPRINT] Entiendo que necesitas una landing page crypto profesional. He creado: 1) Hero section con gradiente y CTA prominente, 2) Features grid con iconos SVG y cards glass morphism, 3) Stats section con contadores animados, 4) Footer con links y redes sociales. Todo siguiendo el sistema de diseno neo-bank con palette dorada."
}}

RESPONDE SOLO CON JSON VALIDO. SIN TEXTO ADICIONAL ANTES O DESPUES."""

        messages = [{"role": "user", "content": message}]
        
        for provider in self.providers:
            if not provider.is_available():
                continue
            
            logger.info(f"Code builder trying provider: {provider.name}")
            result = provider.chat(messages, code_system_prompt)
            
            if result.get("success"):
                response_text = result.get("response", "")
                
                try:
                    json_match = None
                    if response_text.strip().startswith('{'):
                        json_match = response_text.strip()
                    else:
                        import re
                        json_pattern = r'\{[\s\S]*\}'
                        matches = re.findall(json_pattern, response_text)
                        if matches:
                            for match in matches:
                                try:
                                    sanitized = self._sanitize_json(match)
                                    json.loads(sanitized)
                                    json_match = sanitized
                                    break
                                except (json.JSONDecodeError, ValueError) as e:
                                    logger.debug(f"JSON parse attempt failed: {e}")
                                    continue
                    
                    if json_match:
                        sanitized_json = self._sanitize_json(json_match)
                        parsed = json.loads(sanitized_json)
                        files = parsed.get("files", {})
                        msg = parsed.get("message", "Codigo generado exitosamente")
                        
                        if files:
                            return {
                                "success": True,
                                "files": files,
                                "response": msg,
                                "provider": provider.name
                            }
                    
                    extracted = self._extract_code_blocks(response_text)
                    if extracted:
                        return {
                            "success": True,
                            "files": extracted,
                            "response": "He generado el codigo solicitado.",
                            "provider": provider.name
                        }
                    
                    return {
                        "success": False,
                        "error": "No se pudo extraer codigo de la respuesta. Intenta de nuevo.",
                        "provider": provider.name
                    }
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parse error: {e}")
                    extracted = self._extract_code_blocks(response_text)
                    if extracted:
                        return {
                            "success": True,
                            "files": extracted,
                            "response": "He generado el codigo. Revisa los archivos actualizados.",
                            "provider": provider.name
                        }
                    return {
                        "success": False,
                        "error": "No se pudo parsear la respuesta de la IA. Intenta de nuevo con instrucciones mas claras.",
                        "provider": provider.name
                    }
            else:
                logger.warning(f"Provider {provider.name} failed: {result.get('error')}")
        
        return {
            "success": False,
            "error": "No se pudo generar el codigo. Intenta de nuevo.",
            "provider": None
        }
    
    def _sanitize_json(self, json_str: str) -> str:
        """Sanitize JSON string by escaping control characters in string values"""
        import re
        
        result = []
        in_string = False
        escape_next = False
        
        for char in json_str:
            if escape_next:
                result.append(char)
                escape_next = False
                continue
                
            if char == '\\':
                escape_next = True
                result.append(char)
                continue
                
            if char == '"':
                in_string = not in_string
                result.append(char)
                continue
            
            if in_string:
                if char == '\n':
                    result.append('\\n')
                elif char == '\r':
                    result.append('\\r')
                elif char == '\t':
                    result.append('\\t')
                elif ord(char) < 32:
                    result.append(f'\\u{ord(char):04x}')
                else:
                    result.append(char)
            else:
                result.append(char)
        
        return ''.join(result)
    
    def _extract_code_blocks(self, text: str) -> Dict[str, str]:
        """Extract code blocks from markdown-style response"""
        import re
        files = {}
        
        pattern = r'```(\w+)?\s*\n?([\s\S]*?)```'
        matches = re.findall(pattern, text)
        
        lang_to_ext = {
            'html': 'index.html',
            'css': 'styles.css',
            'javascript': 'script.js',
            'js': 'script.js'
        }
        
        for lang, code in matches:
            lang = lang.lower() if lang else 'html'
            filename = lang_to_ext.get(lang, f'file.{lang}')
            files[filename] = code.strip()
        
        if not files and '<!DOCTYPE html>' in text.lower():
            html_match = re.search(r'(<!DOCTYPE html>[\s\S]*?</html>)', text, re.IGNORECASE)
            if html_match:
                files['index.html'] = html_match.group(1).strip()
        
        return files


ai_service: Optional[AIService] = None


def get_ai_service(db_manager=None) -> AIService:
    """Get or create the global AI service instance"""
    global ai_service
    if ai_service is None:
        logger.info("Initializing global AIService...")
        try:
            ai_service = AIService(db_manager)
            logger.info("AIService successfully initialized.")
        except Exception as e:
            logger.error(f"CRITICAL: Failed to initialize AIService: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # We don't catch it here to let it propagate, but we log it
            raise
    return ai_service
