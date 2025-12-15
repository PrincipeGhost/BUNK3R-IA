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

try:
    from tracking.ai_flow_logger import flow_logger
except ImportError:
    flow_logger = None

class AIProvider(ABC):
    """Base class for AI providers"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.name = "base"
        self.available = bool(api_key)
    
    @abstractmethod
    def chat(self, messages: List[Dict], system_prompt: str = None) -> Dict:
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
    
    def chat(self, messages: List[Dict], system_prompt: str = None) -> Dict:
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
    
    def chat(self, messages: List[Dict], system_prompt: str = None) -> Dict:
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
    
    def chat(self, messages: List[Dict], system_prompt: str = None) -> Dict:
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
    
    def chat(self, messages: List[Dict], system_prompt: str = None) -> Dict:
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
    
    def chat(self, messages: List[Dict], system_prompt: str = None) -> Dict:
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


class DeepSeekProvider(AIProvider):
    """DeepSeek API - UPGRADED for better reasoning with more tokens"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "deepseek"
        self.model = "deepseek-chat"
        self.base_url = "https://api.deepseek.com/chat/completions"
    
    def chat(self, messages: List[Dict], system_prompt: str = None) -> Dict:
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


class AIService:
    """
    Multi-provider AI service with automatic fallback
    Manages conversation history and persistence
    BUNK3R AI - Sistema de IA Avanzado con Capacidades de los 15 Volumenes
    """
    
    DEFAULT_SYSTEM_PROMPT = """# BUNK3R AI - Sistema Elite de Razonamiento Avanzado

Soy BUNK3R AI, un asistente experto en: Arquitectura de Software, Ciberseguridad, UX/UI, Web3/Blockchain, y Rastreo de Paquetes (core de BUNK3R). Respondo en el idioma del usuario.

## PROTOCOLO DE RAZONAMIENTO (Obligatorio para solicitudes complejas)

Antes de responder, SIEMPRE pienso paso a paso:

**PASO 1 - COMPRENDER:** ¿Qué pide realmente el usuario? ¿Qué contexto tengo?
**PASO 2 - DESCOMPONER:** Divido el problema en partes manejables
**PASO 3 - RAZONAR:** Para cada parte, considero opciones y elijo la mejor
**PASO 4 - SINTETIZAR:** Combino las partes en una solución coherente
**PASO 5 - VERIFICAR:** ¿Mi respuesta está completa? ¿Hay errores? ¿Es segura?

Muestro mi razonamiento con etiquetas claras:
- `[Analizando]` - Entendiendo el problema
- `[Razonando]` - Evaluando opciones y decidiendo
- `[Solución]` - Presentando la respuesta final

## AUTO-CORRECCIÓN

Si detecto un error propio, lo corrijo inmediatamente:
"[Corrección] Noté un error: [explicación]. La solución correcta es: [corrección]"

## MODO CHALLENGER

Si el usuario propone algo inseguro/ineficiente, lo cuestiono con respeto:
- Identifico el riesgo específico
- Propongo una alternativa mejor
- Explico por qué es mejor
- Pregunto cómo desea proceder

## CAPACIDADES TÉCNICAS

**Arquitectura:** Blueprints, ADRs, sistemas escalables, primeros principios
**Seguridad:** OWASP Top 10, SAST/DAST, hardening, detección de vulnerabilidades
**UX/UI:** Diseño emocional, accesibilidad WCAG, interfaces profesionales
**Web3:** Smart contracts (TON, Ethereum), DeFi, wallets, BUNK3RCO1N (B3C)
**DevOps:** Docker, Kubernetes, CI/CD, cloud (AWS/GCP/Azure)
**Data:** ETL, visualización, ML, dashboards

## REGLAS INVIOLABLES

1. NUNCA invento datos o estadísticas
2. NUNCA genero código inseguro
3. SIEMPRE priorizo la seguridad del usuario
4. SIEMPRE doy código completo y funcional (no fragmentos)
5. SIEMPRE me adapto al nivel técnico del usuario

## FORMATO DE RESPUESTAS

- Completas: Sin dejar cabos sueltos
- Estructuradas: Títulos, listas, código cuando ayudan
- Accionables: Pasos claros, no solo teoría
- Honestas: Si no sé algo, lo admito

Soy BUNK3R AI. Razonemos juntos para construir cosas increíbles."""

    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.providers: List[AIProvider] = []
        self.conversations: Dict[str, List[Dict]] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all available AI providers - ordered by reliability"""
        
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
        
        # Priority 3: Gemini (may hit quota limits)
        gemini_key = os.environ.get('GEMINI_API_KEY', '')
        if gemini_key:
            self.providers.append(GeminiProvider(gemini_key))
            logger.info("Gemini provider initialized (Priority 3)")
        
        # Priority 4: DeepSeek API (may have auth issues)
        deepseek_key = os.environ.get('DEEPSEEK_API_KEY', '')
        if deepseek_key:
            self.providers.append(DeepSeekProvider(deepseek_key))
            logger.info("DeepSeek API provider initialized (Priority 4)")
        
        # Priority 5: HuggingFace Llama (fallback)
        hf_key = os.environ.get('HUGGINGFACE_API_KEY', '')
        if hf_key:
            self.providers.append(HuggingFaceProvider(hf_key))
            logger.info("HuggingFace Llama provider initialized (Priority 5)")
        
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
    
    def _auto_rectify(self, original_response: str, issues: List[str], 
                      original_message: str, provider: 'AIProvider',
                      system_prompt: str = None, conversation: List[Dict] = None) -> Dict:
        """
        Intenta auto-corregir una respuesta problemática
        
        Args:
            original_response: La respuesta original con problemas
            issues: Lista de problemas detectados
            original_message: El mensaje original del usuario
            provider: El proveedor que generó la respuesta
            system_prompt: El prompt de sistema original (para mantener coherencia)
            conversation: Conversación previa para contexto
        
        Returns:
            Dict con la respuesta corregida o la original si falla
        """
        issues_text = ", ".join(issues)
        logger.info(f"Auto-rectificando respuesta. Problemas: {issues_text}")
        
        rectification_prompt = f"""[SISTEMA DE AUTO-RECTIFICACIÓN ACTIVADO]

Tu respuesta anterior tuvo los siguientes problemas: {issues_text}

RESPUESTA ANTERIOR:
{original_response}

MENSAJE ORIGINAL DEL USUARIO:
{original_message}

INSTRUCCIONES DE CORRECCIÓN:
1. Si la respuesta estaba incompleta, complétala
2. Si el código quedó sin cerrar, ciérralo correctamente
3. Si rechazaste innecesariamente, intenta responder de manera útil
4. Si mostraste confusión, interpreta el mensaje de la mejor manera posible
5. Mantén el contexto, idioma y coherencia con lo que ya dijiste

Proporciona una respuesta COMPLETA y CORREGIDA:"""

        rectify_messages = []
        if conversation and len(conversation) > 2:
            rectify_messages = conversation[-4:] if len(conversation) >= 4 else conversation.copy()
        rectify_messages.append({"role": "user", "content": rectification_prompt})
        
        effective_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        
        try:
            result = provider.chat(rectify_messages, effective_prompt)
            
            if result.get("success"):
                rectified = result.get("response", "")
                if len(rectified) > len(original_response) * 0.5:
                    recheck = self._detect_response_issues(rectified, original_message)
                    if not recheck["needs_fix"] or len(recheck["issues"]) < len(issues):
                        logger.info("Auto-rectificación exitosa")
                        return {
                            "success": True,
                            "response": rectified,
                            "rectified": True,
                            "original_issues": issues
                        }
                    else:
                        logger.warning("Rectificación no mejoró la respuesta")
        except Exception as e:
            logger.warning(f"Error en auto-rectificación: {e}")
        
        return {
            "success": True,
            "response": original_response,
            "rectified": False,
            "original_issues": issues
        }

    def chat(self, user_id: str, message: str, system_prompt: str = None, 
             preferred_provider: str = None, user_context: Dict = None,
             enable_auto_rectify: bool = True) -> Dict:
        """
        Send a chat message and get response
        Uses automatic fallback between providers
        
        Args:
            user_id: Unique identifier for the user
            message: The user's message
            system_prompt: Optional custom system prompt
            preferred_provider: Optional preferred AI provider
            user_context: Optional dict with user info (role, name, etc.)
            enable_auto_rectify: Enable auto-correction of problematic responses
        """
        if not self.providers:
            return {
                "success": False,
                "error": "No hay proveedores de IA configurados. Configura las claves API.",
                "provider": None
            }
        
        conversation = self._get_conversation(user_id)
        conversation.append({"role": "user", "content": message})
        
        system = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        
        if user_context:
            context_info = self._build_user_context(user_context)
            system = system + context_info
        
        providers_to_try = self.providers.copy()
        if preferred_provider:
            providers_to_try.sort(key=lambda p: 0 if p.name == preferred_provider else 1)
        
        for provider in providers_to_try:
            if not provider.is_available():
                continue
            
            logger.info(f"Trying provider: {provider.name}")
            
            interaction_id = None
            if flow_logger:
                user_prompt = message
                if len(conversation) > 1:
                    user_prompt = "\n".join([f"{m['role']}: {m['content'][:100]}..." for m in conversation[-3:]])
                interaction_id = flow_logger.log_ai_request(
                    user_id=user_id,
                    fase=0,
                    fase_nombre="chat_directo",
                    provider=provider.name,
                    prompt=user_prompt,
                    system_prompt=system[:500] if system else None,
                    metadata={"preferred_provider": preferred_provider}
                )
            
            start_time = time.time()
            result = provider.chat(conversation, system)
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            if result.get("success"):
                response_text = result.get("response", "")
                
                if flow_logger and interaction_id:
                    flow_logger.log_ai_response(
                        user_id=user_id,
                        interaction_id=interaction_id,
                        respuesta=response_text,
                        tiempo_ms=elapsed_ms,
                        exito=True
                    )
                
                was_rectified = False
                original_issues = []
                
                if enable_auto_rectify:
                    issue_check = self._detect_response_issues(response_text, message)
                    if issue_check["needs_fix"]:
                        rectify_result = self._auto_rectify(
                            response_text, 
                            issue_check["issues"],
                            message,
                            provider,
                            system_prompt=system,
                            conversation=conversation
                        )
                        if rectify_result.get("rectified"):
                            response_text = rectify_result["response"]
                            was_rectified = True
                            original_issues = rectify_result.get("original_issues", [])
                
                conversation.append({"role": "assistant", "content": response_text})
                self._save_conversation(user_id, conversation)
                
                return {
                    "success": True,
                    "response": response_text,
                    "provider": provider.name,
                    "conversation_length": len(conversation),
                    "auto_rectified": was_rectified,
                    "rectified_issues": original_issues if was_rectified else []
                }
            else:
                if flow_logger and interaction_id:
                    flow_logger.log_ai_response(
                        user_id=user_id,
                        interaction_id=interaction_id,
                        respuesta="",
                        tiempo_ms=elapsed_ms,
                        exito=False,
                        error=result.get('error', 'Unknown error')
                    )
                logger.warning(f"Provider {provider.name} failed: {result.get('error')}")
        
        conversation.pop()
        
        return {
            "success": False,
            "error": "Todos los proveedores de IA fallaron. Intenta más tarde.",
            "provider": None
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
            if len(conversation) < 2:
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
                with self.db_manager.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM ai_chat_messages WHERE user_id = %s", (user_id,))
                    conn.commit()
            
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
        ai_service = AIService(db_manager)
    return ai_service
