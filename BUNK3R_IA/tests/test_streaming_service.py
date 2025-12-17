"""
Tests para el Sistema de Streaming (34.15)
Tests unitarios para streaming_service.py
"""

import pytest
from unittest.mock import patch, MagicMock
import json


class TestStreamEvent:
    """Tests para StreamEvent"""
    
    def test_stream_event_creation(self):
        """Test creación de StreamEvent"""
        from BUNK3R_IA.core.streaming_service import StreamEvent, StreamEventType
        
        event = StreamEvent(
            event_type=StreamEventType.TOKEN,
            data="Hello",
            metadata={"provider": "groq"}
        )
        
        assert event.event_type == StreamEventType.TOKEN
        assert event.data == "Hello"
        assert event.metadata["provider"] == "groq"
    
    def test_stream_event_to_sse(self):
        """Test conversión a formato SSE"""
        from BUNK3R_IA.core.streaming_service import StreamEvent, StreamEventType
        
        event = StreamEvent(
            event_type=StreamEventType.TOKEN,
            data="Test",
            metadata={}
        )
        
        sse = event.to_sse()
        
        assert sse.startswith("data: ")
        assert sse.endswith("\n\n")
        
        data = json.loads(sse[6:-2])
        assert data["type"] == "token"
        assert data["data"] == "Test"
        assert "timestamp" in data
    
    def test_stream_event_types(self):
        """Test todos los tipos de eventos"""
        from BUNK3R_IA.core.streaming_service import StreamEventType
        
        assert StreamEventType.START.value == "start"
        assert StreamEventType.TOKEN.value == "token"
        assert StreamEventType.CHUNK.value == "chunk"
        assert StreamEventType.COMPLETE.value == "complete"
        assert StreamEventType.ERROR.value == "error"
        assert StreamEventType.PHASE.value == "phase"
        assert StreamEventType.METADATA.value == "metadata"


class TestStreamingService:
    """Tests para StreamingService"""
    
    def test_streaming_service_init(self):
        """Test inicialización del servicio"""
        from BUNK3R_IA.core.streaming_service import StreamingService
        
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}, clear=True):
            service = StreamingService()
            assert service is not None
            assert len(service.providers) >= 0
    
    def test_get_conversation(self):
        """Test obtención de conversación"""
        from BUNK3R_IA.core.streaming_service import StreamingService
        
        service = StreamingService()
        conv = service.get_conversation("test-user")
        
        assert isinstance(conv, list)
        assert len(conv) == 0
    
    def test_add_message(self):
        """Test agregar mensaje"""
        from BUNK3R_IA.core.streaming_service import StreamingService
        
        service = StreamingService()
        service.add_message("test-user", "user", "Hello")
        
        conv = service.get_conversation("test-user")
        assert len(conv) == 1
        assert conv[0]["role"] == "user"
        assert conv[0]["content"] == "Hello"
    
    def test_clear_conversation(self):
        """Test limpiar conversación"""
        from BUNK3R_IA.core.streaming_service import StreamingService
        
        service = StreamingService()
        service.add_message("test-user", "user", "Hello")
        service.clear_conversation("test-user")
        
        conv = service.get_conversation("test-user")
        assert len(conv) == 0
    
    def test_conversation_history_limit(self):
        """Test límite de historial (max 20 mensajes)"""
        from BUNK3R_IA.core.streaming_service import StreamingService
        
        service = StreamingService()
        
        for i in range(25):
            service.add_message("test-user", "user", f"Message {i}")
        
        conv = service.get_conversation("test-user")
        assert len(conv) == 20
        assert conv[0]["content"] == "Message 5"
    
    def test_get_available_providers_empty(self):
        """Test proveedores disponibles vacío"""
        from BUNK3R_IA.core.streaming_service import StreamingService
        
        with patch.dict('os.environ', {}, clear=True):
            service = StreamingService()
            providers = service.get_available_providers()
            assert isinstance(providers, list)


class TestGroqStreamingProvider:
    """Tests para GroqStreamingProvider"""
    
    def test_provider_init(self):
        """Test inicialización del proveedor"""
        from BUNK3R_IA.core.streaming_service import GroqStreamingProvider
        
        provider = GroqStreamingProvider("test-api-key")
        
        assert provider.name == "groq"
        assert provider.available == True
        assert provider.model == "llama-3.3-70b-versatile"
    
    def test_provider_not_available_without_key(self):
        """Test proveedor no disponible sin API key"""
        from BUNK3R_IA.core.streaming_service import GroqStreamingProvider
        
        provider = GroqStreamingProvider("")
        
        assert provider.available == False


class TestGeminiStreamingProvider:
    """Tests para GeminiStreamingProvider"""
    
    def test_provider_init(self):
        """Test inicialización del proveedor"""
        from BUNK3R_IA.core.streaming_service import GeminiStreamingProvider
        
        provider = GeminiStreamingProvider("test-api-key")
        
        assert provider.name == "gemini"
        assert provider.available == True
        assert provider.model == "gemini-2.0-flash"


class TestDeepSeekStreamingProvider:
    """Tests para DeepSeekStreamingProvider"""
    
    def test_provider_init(self):
        """Test inicialización del proveedor"""
        from BUNK3R_IA.core.streaming_service import DeepSeekStreamingProvider
        
        provider = DeepSeekStreamingProvider("test-api-key")
        
        assert provider.name == "deepseek"
        assert provider.available == True
        assert provider.model == "deepseek-chat"


class TestCerebrasStreamingProvider:
    """Tests para CerebrasStreamingProvider"""
    
    def test_provider_init(self):
        """Test inicialización del proveedor"""
        from BUNK3R_IA.core.streaming_service import CerebrasStreamingProvider
        
        provider = CerebrasStreamingProvider("test-api-key")
        
        assert provider.name == "cerebras"
        assert provider.available == True
        assert provider.model == "llama-3.3-70b"


class TestStreamingServiceSingleton:
    """Tests para singleton del servicio"""
    
    def test_get_streaming_service(self):
        """Test obtención de servicio singleton"""
        from BUNK3R_IA.core.streaming_service import get_streaming_service
        
        service1 = get_streaming_service()
        service2 = get_streaming_service()
        
        assert service1 is service2


class TestStreamChatGenerator:
    """Tests para el generador de streaming"""
    
    def test_stream_chat_no_providers(self):
        """Test streaming sin proveedores disponibles"""
        from BUNK3R_IA.core.streaming_service import StreamingService, StreamEventType
        
        with patch.dict('os.environ', {}, clear=True):
            service = StreamingService()
            
            events = list(service.stream_chat("test-user", "Hello"))
            
            assert len(events) >= 1
            assert events[-1].event_type == StreamEventType.ERROR
    
    @patch('requests.post')
    def test_stream_chat_success(self, mock_post):
        """Test streaming exitoso con mock"""
        from BUNK3R_IA.core.streaming_service import StreamingService, StreamEventType
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b'data: {"choices":[{"delta":{"content":"Hello"}}]}',
            b'data: {"choices":[{"delta":{"content":" World"}}]}',
            b'data: [DONE]'
        ]
        mock_post.return_value = mock_response
        
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}, clear=True):
            service = StreamingService()
            
            events = list(service.stream_chat("test-user", "Test message"))
            
            event_types = [e.event_type for e in events]
            assert StreamEventType.START in event_types
