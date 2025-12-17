"""
Antigravity Client - Cliente para comunicarse con el Antigravity Bridge
Conecta BUNK3R_IA con Google Antigravity corriendo en la PC del usuario via Cloudflare Tunnel
"""
import os
import logging
import time
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

HTTPX_AVAILABLE = False
REQUESTS_AVAILABLE = False

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    pass

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    pass

if not HTTPX_AVAILABLE and not REQUESTS_AVAILABLE:
    logger.error("Neither httpx nor requests is available. AntigravityClient will not work.")


class AntigravityClient:
    """
    Cliente para comunicarse con el Antigravity Bridge
    Usa httpx si está disponible, requests como fallback
    """
    
    HEALTH_CACHE_TTL = 30
    
    def __init__(self, bridge_url: str = None):
        self.bridge_url = bridge_url or os.getenv("ANTIGRAVITY_BRIDGE_URL", "")
        self.timeout = int(os.getenv("ANTIGRAVITY_TIMEOUT", "180"))
        self._last_health_check = 0
        self._last_health_result = False
    
    @property
    def is_configured(self) -> bool:
        return bool(self.bridge_url) and (HTTPX_AVAILABLE or REQUESTS_AVAILABLE)
    
    def _get_url(self, endpoint: str) -> str:
        base = self.bridge_url.rstrip('/')
        return f"{base}/{endpoint.lstrip('/')}"
    
    def _http_get(self, url: str, timeout: int = 10) -> Optional[Dict]:
        try:
            if HTTPX_AVAILABLE:
                with httpx.Client(timeout=timeout) as client:
                    response = client.get(url)
                    response.raise_for_status()
                    return response.json()
            elif REQUESTS_AVAILABLE:
                response = requests.get(url, timeout=timeout)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.debug(f"HTTP GET failed: {e}")
            return None
        return None
    
    def _http_post(self, url: str, json_data: Dict, timeout: int = None) -> Optional[Dict]:
        timeout = timeout or self.timeout
        try:
            if HTTPX_AVAILABLE:
                with httpx.Client(timeout=timeout) as client:
                    response = client.post(url, json=json_data)
                    response.raise_for_status()
                    return response.json()
            elif REQUESTS_AVAILABLE:
                response = requests.post(url, json=json_data, timeout=timeout)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.debug(f"HTTP POST failed: {e}")
            return None
        return None
    
    def health_check(self, force: bool = False) -> bool:
        if not self.is_configured:
            return False
        
        now = time.time()
        if not force and (now - self._last_health_check) < self.HEALTH_CACHE_TTL:
            return self._last_health_result
        
        try:
            data = self._http_get(self._get_url("/health"), timeout=10)
            if data and data.get("status") == "ok":
                self._last_health_check = now
                self._last_health_result = True
                return True
        except Exception as e:
            logger.warning(f"Antigravity health check failed: {e}")
        
        self._last_health_check = now
        self._last_health_result = False
        return False
    
    def query(self, prompt: str, context: Optional[Dict] = None, use_ocr: bool = True) -> Dict[str, Any]:
        if not self.is_configured:
            return {"success": False, "error": "Bridge not configured", "provider": "antigravity"}
        
        payload = {
            "prompt": prompt,
            "use_ocr": use_ocr,
            "context": context or {}
        }
        
        try:
            result = self._http_post(self._get_url("/query"), payload)
            
            if result is None:
                self._last_health_result = False
                return {
                    "success": False, 
                    "error": "Could not connect to Antigravity Bridge",
                    "provider": "antigravity"
                }
            
            if result.get("status") == "success":
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "code_blocks": result.get("code_blocks", []),
                    "method": result.get("method", "unknown"),
                    "provider": "antigravity"
                }
            elif result.get("status") == "busy":
                return {
                    "success": False,
                    "error": "Antigravity is busy processing another request",
                    "provider": "antigravity"
                }
            elif result.get("status") == "timeout":
                return {
                    "success": False,
                    "error": "Antigravity took too long to respond",
                    "provider": "antigravity"
                }
            else:
                error_msg = result.get("error", "Unknown error")
                return {
                    "success": False,
                    "error": f"Bridge error: {error_msg}",
                    "provider": "antigravity"
                }
                
        except Exception as e:
            logger.error(f"Antigravity query error: {e}")
            self._last_health_result = False
            return {
                "success": False,
                "error": "Connection to Antigravity Bridge failed",
                "provider": "antigravity"
            }
    
    def get_status(self) -> Dict[str, Any]:
        if not self.is_configured:
            return {"available": False, "reason": "Not configured"}
        
        data = self._http_get(self._get_url("/status"), timeout=10)
        if data:
            data["available"] = True
            return data
        return {"available": False, "reason": "Could not connect"}
    
    def invalidate_health_cache(self):
        self._last_health_check = 0
        self._last_health_result = False


class AntigravityProvider:
    """
    Proveedor de IA compatible con AIService que usa Antigravity via Bridge
    Sigue el mismo patrón que los otros providers de AIService
    """
    
    MAX_CONVERSATION_TURNS = 10
    
    def __init__(self, bridge_url: str = None):
        self.client = AntigravityClient(bridge_url)
        self.name = "antigravity"
    
    @property
    def available(self) -> bool:
        return self.client.is_configured
    
    def is_available(self) -> bool:
        if not self.client.is_configured:
            return False
        return self.client.health_check()
    
    def chat(self, messages: List[Dict], system_prompt: str = None) -> Dict:
        if not self.client.is_configured:
            return {
                "success": False, 
                "error": "Antigravity Bridge not configured. Set ANTIGRAVITY_BRIDGE_URL.", 
                "provider": self.name
            }
        
        prompt_parts = []
        
        if system_prompt:
            prompt_parts.append(f"[Sistema]\n{system_prompt}")
        
        conversation_turns = messages[-self.MAX_CONVERSATION_TURNS:]
        
        for msg in conversation_turns:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                prompt_parts.append(f"[Usuario]\n{content}")
            elif role == "assistant":
                prompt_parts.append(f"[Asistente]\n{content}")
            elif role == "system":
                prompt_parts.append(f"[Sistema]\n{content}")
        
        full_prompt = "\n\n".join(prompt_parts)
        
        result = self.client.query(full_prompt)
        
        if result.get("success"):
            response_text = result.get("response", "")
            
            code_blocks = result.get("code_blocks", [])
            if code_blocks:
                for block in code_blocks:
                    lang = block.get("language", "")
                    code = block.get("code", "")
                    if code and f"```{lang}" not in response_text:
                        response_text += f"\n\n```{lang}\n{code}\n```"
            
            return {
                "success": True, 
                "response": response_text, 
                "provider": self.name
            }
        else:
            return {
                "success": False, 
                "error": result.get("error", "Unknown error"), 
                "provider": self.name
            }
    
    def check_bridge_status(self) -> Dict[str, Any]:
        return self.client.get_status()
    
    def refresh_availability(self):
        self.client.invalidate_health_cache()
