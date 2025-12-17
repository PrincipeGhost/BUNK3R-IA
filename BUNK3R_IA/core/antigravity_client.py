"""
Antigravity Client - Cliente para comunicarse con el Antigravity Bridge
Conecta BUNK3R_IA con Google Antigravity corriendo en la PC del usuario via Cloudflare Tunnel
"""
import os
import logging
import asyncio
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.warning("httpx not installed. Using requests as fallback.")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class AntigravityClient:
    """
    Cliente para comunicarse con el Antigravity Bridge
    Soporta tanto operaciones síncronas como asíncronas
    """
    
    def __init__(self, bridge_url: str = None):
        self.bridge_url = bridge_url or os.getenv("ANTIGRAVITY_BRIDGE_URL", "")
        self.timeout = 180
        self._async_client = None
    
    @property
    def is_configured(self) -> bool:
        return bool(self.bridge_url)
    
    def _get_url(self, endpoint: str) -> str:
        base = self.bridge_url.rstrip('/')
        return f"{base}/{endpoint.lstrip('/')}"
    
    def health_check(self) -> bool:
        if not self.is_configured:
            return False
        
        try:
            if REQUESTS_AVAILABLE:
                response = requests.get(
                    self._get_url("/health"),
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("status") == "ok"
            return False
        except Exception as e:
            logger.warning(f"Antigravity health check failed: {e}")
            return False
    
    def query(self, prompt: str, context: Optional[Dict] = None, use_ocr: bool = True) -> Dict[str, Any]:
        if not self.is_configured:
            return {"error": "ANTIGRAVITY_BRIDGE_URL not configured", "status": "error"}
        
        payload = {
            "prompt": prompt,
            "use_ocr": use_ocr,
            "context": context or {}
        }
        
        try:
            if REQUESTS_AVAILABLE:
                response = requests.post(
                    self._get_url("/query"),
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
            else:
                return {"error": "No HTTP client available", "status": "error"}
        except requests.exceptions.Timeout:
            return {"error": "Timeout waiting for Antigravity response", "status": "timeout"}
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status": "error"}
        except Exception as e:
            logger.error(f"Antigravity query error: {e}")
            return {"error": str(e), "status": "error"}
    
    def get_status(self) -> Dict[str, Any]:
        if not self.is_configured:
            return {"error": "URL not configured", "available": False}
        
        try:
            if REQUESTS_AVAILABLE:
                response = requests.get(
                    self._get_url("/status"),
                    timeout=10
                )
                data = response.json()
                data["available"] = True
                return data
            return {"error": "No HTTP client available", "available": False}
        except Exception as e:
            return {"error": str(e), "available": False}
    
    def calibrate(self) -> Dict[str, Any]:
        if not self.is_configured:
            return {"error": "URL not configured", "status": "error"}
        
        try:
            if REQUESTS_AVAILABLE:
                response = requests.post(
                    self._get_url("/calibrate"),
                    timeout=30
                )
                return response.json()
            return {"error": "No HTTP client available", "status": "error"}
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    async def async_health_check(self) -> bool:
        if not self.is_configured or not HTTPX_AVAILABLE:
            return self.health_check()
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(self._get_url("/health"))
                if response.status_code == 200:
                    data = response.json()
                    return data.get("status") == "ok"
            return False
        except Exception as e:
            logger.warning(f"Async Antigravity health check failed: {e}")
            return False
    
    async def async_query(self, prompt: str, context: Optional[Dict] = None, use_ocr: bool = True) -> Dict[str, Any]:
        if not self.is_configured:
            return {"error": "ANTIGRAVITY_BRIDGE_URL not configured", "status": "error"}
        
        if not HTTPX_AVAILABLE:
            return self.query(prompt, context, use_ocr)
        
        payload = {
            "prompt": prompt,
            "use_ocr": use_ocr,
            "context": context or {}
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self._get_url("/query"),
                    json=payload
                )
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            return {"error": "Timeout waiting for Antigravity response", "status": "timeout"}
        except Exception as e:
            logger.error(f"Async Antigravity query error: {e}")
            return {"error": str(e), "status": "error"}


class AntigravityProvider:
    """
    Proveedor de IA compatible con AIService que usa Antigravity via Bridge
    """
    
    def __init__(self, bridge_url: str = None):
        self.client = AntigravityClient(bridge_url)
        self.name = "antigravity"
        self.available = self.client.is_configured
    
    def is_available(self) -> bool:
        if not self.available:
            return False
        return self.client.health_check()
    
    def chat(self, messages: List[Dict], system_prompt: str = None) -> Dict:
        if not self.client.is_configured:
            return {"success": False, "error": "Antigravity Bridge URL not configured", "provider": self.name}
        
        prompt_parts = []
        
        if system_prompt:
            prompt_parts.append(f"[SISTEMA]\n{system_prompt}\n")
        
        for msg in messages[-5:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                prompt_parts.append(f"[USUARIO]\n{content}")
            elif role == "assistant":
                prompt_parts.append(f"[ASISTENTE]\n{content}")
        
        full_prompt = "\n\n".join(prompt_parts)
        
        try:
            result = self.client.query(full_prompt)
            
            if result.get("status") == "success":
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
                    "provider": self.name,
                    "method": result.get("method", "unknown")
                }
            else:
                error = result.get("error", "Unknown error from Antigravity Bridge")
                return {"success": False, "error": error, "provider": self.name}
                
        except Exception as e:
            logger.error(f"Antigravity provider error: {e}")
            return {"success": False, "error": str(e), "provider": self.name}
    
    def check_bridge_status(self) -> Dict[str, Any]:
        return self.client.get_status()
    
    def calibrate_bridge(self) -> Dict[str, Any]:
        return self.client.calibrate()
