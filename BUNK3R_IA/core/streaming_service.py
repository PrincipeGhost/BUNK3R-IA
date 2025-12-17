"""
Streaming Service - Server-Sent Events (SSE) para respuestas de IA en tiempo real
Implementa 34.15 - Sistema de streaming de respuestas

Soporta streaming para:
- Groq (nativo)
- Gemini (nativo)
- DeepSeek (nativo)
- Cerebras (nativo)
"""

import os
import json
import time
import logging
from typing import Generator, Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class StreamEventType(Enum):
    """Tipos de eventos SSE"""
    START = "start"
    TOKEN = "token"
    CHUNK = "chunk"
    COMPLETE = "complete"
    ERROR = "error"
    PHASE = "phase"
    METADATA = "metadata"


@dataclass
class StreamEvent:
    """Evento de streaming SSE"""
    event_type: StreamEventType
    data: str
    metadata: Dict = field(default_factory=dict)
    
    def to_sse(self) -> str:
        """Convierte a formato SSE"""
        payload = {
            "type": self.event_type.value,
            "data": self.data,
            "metadata": self.metadata,
            "timestamp": time.time()
        }
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


class StreamingProvider:
    """Base class para proveedores con streaming"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.name = "base"
        self.available = bool(api_key)
    
    def stream_chat(self, messages: List[Dict], system_prompt: str = None) -> Generator[StreamEvent, None, None]:
        """Override en subclases"""
        raise NotImplementedError


class GroqStreamingProvider(StreamingProvider):
    """Groq con streaming nativo - Muy rápido"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "groq"
        self.model = "llama-3.3-70b-versatile"
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def stream_chat(self, messages: List[Dict], system_prompt: str = None) -> Generator[StreamEvent, None, None]:
        try:
            import requests
            
            yield StreamEvent(StreamEventType.START, "", {"provider": self.name, "model": self.model})
            
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
                    "max_tokens": 8192,
                    "stream": True
                },
                stream=True,
                timeout=120
            )
            
            if response.status_code != 200:
                yield StreamEvent(StreamEventType.ERROR, f"HTTP {response.status_code}", {"provider": self.name})
                return
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        data = line_text[6:]
                        if data == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk.get('choices', [{}])[0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                full_response += content
                                yield StreamEvent(StreamEventType.TOKEN, content, {"provider": self.name})
                        except json.JSONDecodeError:
                            continue
            
            yield StreamEvent(StreamEventType.COMPLETE, full_response, {
                "provider": self.name,
                "total_length": len(full_response)
            })
            
        except Exception as e:
            logger.error(f"Groq streaming error: {e}")
            yield StreamEvent(StreamEventType.ERROR, str(e), {"provider": self.name})


class GeminiStreamingProvider(StreamingProvider):
    """Google Gemini con streaming nativo"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "gemini"
        self.model = "gemini-2.0-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
    
    def stream_chat(self, messages: List[Dict], system_prompt: str = None) -> Generator[StreamEvent, None, None]:
        try:
            import requests
            
            yield StreamEvent(StreamEventType.START, "", {"provider": self.name, "model": self.model})
            
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
                f"{self.base_url}/{self.model}:streamGenerateContent?alt=sse&key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json=payload,
                stream=True,
                timeout=120
            )
            
            if response.status_code != 200:
                yield StreamEvent(StreamEventType.ERROR, f"HTTP {response.status_code}", {"provider": self.name})
                return
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        data = line_text[6:]
                        try:
                            chunk = json.loads(data)
                            candidates = chunk.get('candidates', [])
                            if candidates:
                                parts = candidates[0].get('content', {}).get('parts', [])
                                for part in parts:
                                    text = part.get('text', '')
                                    if text:
                                        full_response += text
                                        yield StreamEvent(StreamEventType.TOKEN, text, {"provider": self.name})
                        except json.JSONDecodeError:
                            continue
            
            yield StreamEvent(StreamEventType.COMPLETE, full_response, {
                "provider": self.name,
                "total_length": len(full_response)
            })
            
        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            yield StreamEvent(StreamEventType.ERROR, str(e), {"provider": self.name})


class DeepSeekStreamingProvider(StreamingProvider):
    """DeepSeek API con streaming"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "deepseek"
        self.model = "deepseek-chat"
        self.base_url = "https://api.deepseek.com/chat/completions"
    
    def stream_chat(self, messages: List[Dict], system_prompt: str = None) -> Generator[StreamEvent, None, None]:
        try:
            import requests
            
            yield StreamEvent(StreamEventType.START, "", {"provider": self.name, "model": self.model})
            
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
                    "max_tokens": 8192,
                    "stream": True
                },
                stream=True,
                timeout=180
            )
            
            if response.status_code != 200:
                yield StreamEvent(StreamEventType.ERROR, f"HTTP {response.status_code}", {"provider": self.name})
                return
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        data = line_text[6:]
                        if data == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk.get('choices', [{}])[0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                full_response += content
                                yield StreamEvent(StreamEventType.TOKEN, content, {"provider": self.name})
                        except json.JSONDecodeError:
                            continue
            
            yield StreamEvent(StreamEventType.COMPLETE, full_response, {
                "provider": self.name,
                "total_length": len(full_response)
            })
            
        except Exception as e:
            logger.error(f"DeepSeek streaming error: {e}")
            yield StreamEvent(StreamEventType.ERROR, str(e), {"provider": self.name})


class CerebrasStreamingProvider(StreamingProvider):
    """Cerebras con streaming"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "cerebras"
        self.model = "llama-3.3-70b"
        self.base_url = "https://api.cerebras.ai/v1/chat/completions"
    
    def stream_chat(self, messages: List[Dict], system_prompt: str = None) -> Generator[StreamEvent, None, None]:
        try:
            import requests
            
            yield StreamEvent(StreamEventType.START, "", {"provider": self.name, "model": self.model})
            
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
                    "max_tokens": 8192,
                    "stream": True
                },
                stream=True,
                timeout=120
            )
            
            if response.status_code != 200:
                yield StreamEvent(StreamEventType.ERROR, f"HTTP {response.status_code}", {"provider": self.name})
                return
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        data = line_text[6:]
                        if data == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk.get('choices', [{}])[0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                full_response += content
                                yield StreamEvent(StreamEventType.TOKEN, content, {"provider": self.name})
                        except json.JSONDecodeError:
                            continue
            
            yield StreamEvent(StreamEventType.COMPLETE, full_response, {
                "provider": self.name,
                "total_length": len(full_response)
            })
            
        except Exception as e:
            logger.error(f"Cerebras streaming error: {e}")
            yield StreamEvent(StreamEventType.ERROR, str(e), {"provider": self.name})


class StreamingService:
    """
    Servicio principal de streaming con fallback automático
    Maneja múltiples proveedores y cambia automáticamente si uno falla
    """
    
    DEFAULT_SYSTEM_PROMPT = """Soy BUNK3R AI, un asistente experto. Respondo de forma clara y estructurada."""
    
    def __init__(self):
        self.providers: List[StreamingProvider] = []
        self.conversations: Dict[str, List[Dict]] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Inicializa proveedores de streaming en orden de prioridad"""
        
        groq_key = os.environ.get('GROQ_API_KEY', '')
        if groq_key:
            self.providers.append(GroqStreamingProvider(groq_key))
            logger.info("Groq streaming provider initialized")
        
        cerebras_key = os.environ.get('CEREBRAS_API_KEY', '')
        if cerebras_key:
            self.providers.append(CerebrasStreamingProvider(cerebras_key))
            logger.info("Cerebras streaming provider initialized")
        
        gemini_key = os.environ.get('GEMINI_API_KEY', '')
        if gemini_key:
            self.providers.append(GeminiStreamingProvider(gemini_key))
            logger.info("Gemini streaming provider initialized")
        
        deepseek_key = os.environ.get('DEEPSEEK_API_KEY', '')
        if deepseek_key:
            self.providers.append(DeepSeekStreamingProvider(deepseek_key))
            logger.info("DeepSeek streaming provider initialized")
        
        if not self.providers:
            logger.warning("No streaming providers available")
    
    def get_available_providers(self) -> List[str]:
        """Lista de proveedores disponibles"""
        return [p.name for p in self.providers if p.available]
    
    def get_conversation(self, user_id: str) -> List[Dict]:
        """Obtiene historial de conversación"""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        return self.conversations[user_id]
    
    def add_message(self, user_id: str, role: str, content: str):
        """Agrega mensaje al historial"""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        self.conversations[user_id].append({"role": role, "content": content})
        if len(self.conversations[user_id]) > 20:
            self.conversations[user_id] = self.conversations[user_id][-20:]
    
    def clear_conversation(self, user_id: str):
        """Limpia historial de conversación"""
        self.conversations[user_id] = []
    
    def stream_chat(self, user_id: str, message: str, 
                    system_prompt: str = None,
                    preferred_provider: str = None) -> Generator[StreamEvent, None, None]:
        """
        Stream de chat con fallback automático
        
        Args:
            user_id: ID del usuario
            message: Mensaje del usuario
            system_prompt: Prompt del sistema (opcional)
            preferred_provider: Proveedor preferido (opcional)
        
        Yields:
            StreamEvent: Eventos SSE en tiempo real
        """
        if not self.providers:
            yield StreamEvent(StreamEventType.ERROR, "No hay proveedores de IA disponibles")
            return
        
        self.add_message(user_id, "user", message)
        conversation = self.get_conversation(user_id)
        effective_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        
        providers_to_try = list(self.providers)
        if preferred_provider:
            for i, p in enumerate(providers_to_try):
                if p.name == preferred_provider:
                    providers_to_try.insert(0, providers_to_try.pop(i))
                    break
        
        full_response = ""
        success = False
        
        for provider in providers_to_try:
            try:
                yield StreamEvent(StreamEventType.METADATA, "", {
                    "action": "trying_provider",
                    "provider": provider.name
                })
                
                error_occurred = False
                for event in provider.stream_chat(conversation, effective_prompt):
                    if event.event_type == StreamEventType.ERROR:
                        error_occurred = True
                        logger.warning(f"Provider {provider.name} failed: {event.data}")
                        break
                    elif event.event_type == StreamEventType.COMPLETE:
                        full_response = event.data
                        success = True
                    yield event
                
                if success:
                    break
                    
                if error_occurred:
                    continue
                    
            except Exception as e:
                logger.error(f"Provider {provider.name} exception: {e}")
                continue
        
        if success and full_response:
            self.add_message(user_id, "assistant", full_response)
        elif not success:
            yield StreamEvent(StreamEventType.ERROR, "Todos los proveedores fallaron")
    
    def stream_constructor_phase(self, phase_name: str, phase_data: Dict) -> Generator[StreamEvent, None, None]:
        """
        Stream de progreso de fases del constructor
        
        Args:
            phase_name: Nombre de la fase
            phase_data: Datos de la fase
        
        Yields:
            StreamEvent con información de la fase
        """
        yield StreamEvent(StreamEventType.PHASE, phase_name, {
            "phase": phase_name,
            "status": "started",
            **phase_data
        })


_streaming_service: Optional[StreamingService] = None


def get_streaming_service() -> StreamingService:
    """Obtiene instancia singleton del servicio de streaming"""
    global _streaming_service
    if _streaming_service is None:
        _streaming_service = StreamingService()
    return _streaming_service
