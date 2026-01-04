"""
AI Flow Logger - Sistema de logging para ver el flujo completo de la IA
Captura todas las interacciones entre el AIConstructor y los proveedores de IA
"""
import json
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field, asdict
from collections import deque
import threading

logger = logging.getLogger(__name__)

@dataclass
class AIInteraction:
    """Una interacción individual con la IA"""
    id: str
    timestamp: str
    fase: int
    fase_nombre: str
    tipo: str  # "request" o "response"
    provider: str
    prompt_enviado: Optional[str] = None
    system_prompt: Optional[str] = None
    respuesta_recibida: Optional[str] = None
    tokens_prompt: Optional[int] = None
    tokens_respuesta: Optional[int] = None
    tiempo_ms: Optional[int] = None
    exito: bool = True
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass 
class FaseLog:
    """Log de una fase completa"""
    fase: int
    nombre: str
    inicio: str
    fin: Optional[str] = None
    duracion_ms: Optional[int] = None
    entrada: Optional[Dict] = None
    salida: Optional[Dict] = None
    interacciones_ia: List[AIInteraction] = field(default_factory=list)
    estado: str = "en_progreso"  # "en_progreso", "completada", "error"
    
    def to_dict(self) -> Dict:
        return {
            "fase": self.fase,
            "nombre": self.nombre,
            "inicio": self.inicio,
            "fin": self.fin,
            "duracion_ms": self.duracion_ms,
            "entrada": self.entrada,
            "salida": self.salida,
            "interacciones_ia": [i.to_dict() for i in self.interacciones_ia],
            "estado": self.estado
        }

@dataclass
class SessionFlowLog:
    """Log completo de una sesión de usuario"""
    session_id: str
    user_id: str
    inicio: str
    mensaje_original: str
    fases: List[FaseLog] = field(default_factory=list)
    estado: str = "activa"
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "inicio": self.inicio,
            "mensaje_original": self.mensaje_original,
            "fases": [f.to_dict() for f in self.fases],
            "estado": self.estado
        }


class AIFlowLogger:
    """
    Logger central para el flujo de la IA
    Captura todas las interacciones para debugging y análisis
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.sessions: Dict[str, SessionFlowLog] = {}
        self.recent_interactions: deque = deque(maxlen=100)  # Últimas 100 interacciones
        self.enabled = True
        self._interaction_counter = 0
        logger.info("AIFlowLogger initialized")
    
    def start_session(self, session_id: str, user_id: str, mensaje: str) -> SessionFlowLog:
        """Inicia el logging de una nueva sesión"""
        session_log = SessionFlowLog(
            session_id=session_id,
            user_id=user_id,
            inicio=datetime.now().isoformat(),
            mensaje_original=mensaje
        )
        self.sessions[user_id] = session_log
        logger.info(f"[FLOW] Session started: {session_id} for user {user_id}")
        return session_log
    
    def get_session(self, user_id: str) -> Optional[SessionFlowLog]:
        """Obtiene el log de sesión de un usuario"""
        return self.sessions.get(user_id)
    
    def start_fase(self, user_id: str, fase: int, nombre: str, entrada: Dict = None) -> Optional[FaseLog]:
        """Inicia el logging de una fase"""
        session = self.get_session(user_id)
        if not session:
            return None
            
        fase_log = FaseLog(
            fase=fase,
            nombre=nombre,
            inicio=datetime.now().isoformat(),
            entrada=entrada
        )
        session.fases.append(fase_log)
        
        logger.info(f"[FLOW] Fase {fase} ({nombre}) started for user {user_id}")
        return fase_log
    
    def end_fase(self, user_id: str, fase: int, salida: Dict = None, estado: str = "completada"):
        """Finaliza el logging de una fase"""
        session = self.get_session(user_id)
        if not session:
            return
            
        for fase_log in session.fases:
            if fase_log.fase == fase and fase_log.estado == "en_progreso":
                fase_log.fin = datetime.now().isoformat()
                fase_log.salida = salida
                fase_log.estado = estado
                
                inicio = datetime.fromisoformat(fase_log.inicio)
                fin = datetime.fromisoformat(fase_log.fin)
                fase_log.duracion_ms = int((fin - inicio).total_seconds() * 1000)
                
                logger.info(f"[FLOW] Fase {fase} completed in {fase_log.duracion_ms}ms")
                break
    
    def log_ai_request(self, user_id: str, fase: int, fase_nombre: str, 
                       provider: str, prompt: str, system_prompt: str = None,
                       metadata: Dict = None) -> str:
        """Registra una solicitud a la IA"""
        self._interaction_counter += 1
        interaction_id = f"int_{self._interaction_counter}_{datetime.now().strftime('%H%M%S')}"
        
        interaction = AIInteraction(
            id=interaction_id,
            timestamp=datetime.now().isoformat(),
            fase=fase,
            fase_nombre=fase_nombre,
            tipo="request",
            provider=provider,
            prompt_enviado=prompt,
            system_prompt=system_prompt,
            tokens_prompt=len(prompt.split()) if prompt else 0,
            metadata=metadata or {}
        )
        
        self.recent_interactions.append(interaction)
        
        session = self.get_session(user_id)
        if session and session.fases:
            for fase_log in reversed(session.fases):
                if fase_log.fase == fase:
                    fase_log.interacciones_ia.append(interaction)
                    break
        
        logger.info(f"[FLOW] AI Request to {provider}: {prompt[:100]}...")
        return interaction_id
    
    def log_ai_response(self, user_id: str, interaction_id: str, 
                        respuesta: str, tiempo_ms: int = None,
                        exito: bool = True, error: str = None):
        """Registra una respuesta de la IA"""
        for interaction in self.recent_interactions:
            if interaction.id == interaction_id:
                interaction.respuesta_recibida = respuesta
                interaction.tokens_respuesta = len(respuesta.split()) if respuesta else 0
                interaction.tiempo_ms = tiempo_ms
                interaction.exito = exito
                interaction.error = error
                
                logger.info(f"[FLOW] AI Response ({tiempo_ms}ms): {respuesta[:100]}...")
                break
    
    def get_session_flow(self, user_id: str) -> Optional[Dict]:
        """Obtiene el flujo completo de una sesión"""
        session = self.get_session(user_id)
        if session:
            return session.to_dict()
        return None
    
    def get_recent_interactions(self, limit: int = 50) -> List[Dict]:
        """Obtiene las interacciones recientes"""
        interactions = list(self.recent_interactions)[-limit:]
        return [i.to_dict() for i in interactions]
    
    def get_all_sessions_summary(self) -> List[Dict]:
        """Obtiene un resumen de todas las sesiones"""
        summaries = []
        for user_id, session in self.sessions.items():
            summaries.append({
                "session_id": session.session_id,
                "user_id": user_id,
                "inicio": session.inicio,
                "mensaje": session.mensaje_original[:100] + "..." if len(session.mensaje_original) > 100 else session.mensaje_original,
                "fases_completadas": len([f for f in session.fases if f.estado == "completada"]),
                "total_fases": len(session.fases),
                "estado": session.estado
            })
        return summaries
    
    def format_flow_for_display(self, user_id: str) -> str:
        """Formatea el flujo para mostrar en consola/UI"""
        session = self.get_session(user_id)
        if not session:
            return "No hay sesión activa para este usuario"
        
        output = []
        output.append("=" * 60)
        output.append(f"🤖 FLUJO DE IA - Sesión: {session.session_id}")
        output.append(f"📝 Mensaje original: {session.mensaje_original}")
        output.append("=" * 60)
        
        for fase in session.fases:
            status_icon = "✅" if fase.estado == "completada" else "🔄" if fase.estado == "en_progreso" else "❌"
            output.append(f"\n{status_icon} FASE {fase.fase}: {fase.nombre}")
            output.append(f"   Duración: {fase.duracion_ms}ms" if fase.duracion_ms else "   En progreso...")
            
            if fase.entrada:
                output.append(f"   📥 Entrada: {json.dumps(fase.entrada, ensure_ascii=False)[:200]}...")
            
            if fase.salida:
                output.append(f"   📤 Salida: {json.dumps(fase.salida, ensure_ascii=False)[:200]}...")
            
            for inter in fase.interacciones_ia:
                output.append(f"\n   🔹 Interacción con {inter.provider}:")
                if inter.prompt_enviado:
                    output.append(f"      📤 Prompt ({inter.tokens_prompt} tokens):")
                    prompt_preview = inter.prompt_enviado[:300].replace('\n', '\n         ')
                    output.append(f"         {prompt_preview}...")
                
                if inter.respuesta_recibida:
                    output.append(f"      📥 Respuesta ({inter.tokens_respuesta} tokens, {inter.tiempo_ms}ms):")
                    resp_preview = inter.respuesta_recibida[:300].replace('\n', '\n         ')
                    output.append(f"         {resp_preview}...")
                
                if not inter.exito:
                    output.append(f"      ❌ Error: {inter.error}")
        
        output.append("\n" + "=" * 60)
        return "\n".join(output)
    
    def clear_session(self, user_id: str):
        """Limpia el log de una sesión"""
        if user_id in self.sessions:
            del self.sessions[user_id]
    
    def clear_all(self):
        """Limpia todos los logs"""
        self.sessions.clear()
        self.recent_interactions.clear()


flow_logger = AIFlowLogger()
