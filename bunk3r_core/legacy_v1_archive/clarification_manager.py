"""
BUNK3R AI - ClarificationManager (34.3)
Sistema de Preguntas Inteligentes Clarificadoras

Funcionalidades:
- Detección de solicitudes ambiguas
- Generación de preguntas clarificadoras
- Priorización de preguntas (máx 3)
- Integración con flujo de 8 fases
- Persistencia de respuestas
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class AmbiguityType(Enum):
    SCOPE = "scope"
    TECHNOLOGY = "technology"
    DESIGN = "design"
    FUNCTIONALITY = "functionality"
    DATA = "data"
    INTEGRATION = "integration"
    TIMELINE = "timeline"
    BUDGET = "budget"


class QuestionPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class ClarificationQuestion:
    id: str
    question: str
    ambiguity_type: AmbiguityType
    priority: QuestionPriority
    options: List[str] = field(default_factory=list)
    default_value: Optional[str] = None
    context: str = ""
    answered: bool = False
    answer: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "question": self.question,
            "ambiguity_type": self.ambiguity_type.value,
            "priority": self.priority.value,
            "options": self.options,
            "default_value": self.default_value,
            "context": self.context,
            "answered": self.answered,
            "answer": self.answer
        }


@dataclass
class AmbiguityDetection:
    detected: bool
    ambiguity_types: List[AmbiguityType]
    confidence: float
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            "detected": self.detected,
            "ambiguity_types": [a.value for a in self.ambiguity_types],
            "confidence": self.confidence,
            "details": self.details
        }


@dataclass
class ClarificationSession:
    session_id: str
    user_id: str
    original_request: str
    questions: List[ClarificationQuestion]
    answers: Dict[str, str]
    completed: bool
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "original_request": self.original_request,
            "questions": [q.to_dict() for q in self.questions],
            "answers": self.answers,
            "completed": self.completed,
            "created_at": self.created_at.isoformat()
        }


class ClarificationManager:
    """
    Gestor de Clarificación - Fase 3 del Constructor
    
    Detecta ambigüedades en solicitudes y genera preguntas inteligentes
    para obtener información faltante del usuario.
    """
    
    MAX_QUESTIONS = 3
    
    AMBIGUITY_PATTERNS = {
        AmbiguityType.SCOPE: [
            r'\b(simple|básico|completo|grande|pequeño)\b',
            r'\b(algo|algún|algunos?)\b',
            r'\b(más o menos|aproximadamente|como)\b',
            r'(?:quiero|necesito)\s+(?:un|una)\s+\w+$',
        ],
        AmbiguityType.TECHNOLOGY: [
            r'\b(web|app|aplicación|sistema)\b(?!\s+(?:en|con|usando))',
            r'\b(página|sitio)\b(?!\s+(?:en|con|usando))',
            r'(?:crear|hacer|desarrollar)\s+(?:un|una)\s+\w+',
        ],
        AmbiguityType.DESIGN: [
            r'\b(bonito|lindo|moderno|profesional)\b(?!\s+(?:con|tipo|como))',
            r'\b(diseño)\b(?!\s+(?:tipo|como|similar|estilo))',
            r'\b(colores?)\b(?!\s+(?:como|tipo|azul|rojo|verde|#))',
        ],
        AmbiguityType.FUNCTIONALITY: [
            r'\b(funciones?|características?|features?)\b(?!\s+(?:como|de|para))',
            r'\b(que\s+(?:haga|permita|tenga))\b(?!\s+(?:lo\s+siguiente|esto|:))',
            r'\b(interactivo|dinámico)\b',
        ],
        AmbiguityType.DATA: [
            r'\b(datos?|información|contenido)\b(?!\s+(?:como|de|sobre))',
            r'\b(usuarios?|clientes?|productos?)\b(?!\s+(?:como|de))',
            r'\b(base\s+de\s+datos|database)\b(?!\s+(?:con|tipo|postgresql|mysql))',
        ],
        AmbiguityType.INTEGRATION: [
            r'\b(conectar|integrar|vincular)\b(?!\s+(?:con|a))',
            r'\b(api|servicio)\b(?!\s+(?:de|como|tipo))',
            r'\b(pagos?|pago)\b(?!\s+(?:con|stripe|paypal))',
        ],
    }
    
    QUESTION_TEMPLATES = {
        AmbiguityType.SCOPE: [
            ClarificationQuestion(
                id="scope_size",
                question="¿Cuál es el alcance del proyecto?",
                ambiguity_type=AmbiguityType.SCOPE,
                priority=QuestionPriority.CRITICAL,
                options=["MVP mínimo (1-3 páginas)", "Proyecto mediano (4-8 páginas)", "Proyecto completo (8+ páginas)"],
                default_value="MVP mínimo (1-3 páginas)",
                context="Ayuda a determinar complejidad y tiempo"
            ),
            ClarificationQuestion(
                id="scope_sections",
                question="¿Qué secciones principales necesitas?",
                ambiguity_type=AmbiguityType.SCOPE,
                priority=QuestionPriority.HIGH,
                options=["Inicio", "Sobre nosotros", "Servicios", "Contacto", "Blog", "Tienda"],
                context="Selecciona las secciones que necesitas"
            ),
        ],
        AmbiguityType.TECHNOLOGY: [
            ClarificationQuestion(
                id="tech_stack",
                question="¿Qué tecnología prefieres?",
                ambiguity_type=AmbiguityType.TECHNOLOGY,
                priority=QuestionPriority.HIGH,
                options=["HTML/CSS/JS puro", "Python Flask", "React", "Vue.js", "No tengo preferencia"],
                default_value="HTML/CSS/JS puro",
                context="Determina el stack tecnológico"
            ),
            ClarificationQuestion(
                id="tech_backend",
                question="¿Necesitas backend/base de datos?",
                ambiguity_type=AmbiguityType.TECHNOLOGY,
                priority=QuestionPriority.MEDIUM,
                options=["Sí, con base de datos", "Solo frontend estático", "No estoy seguro"],
                default_value="Solo frontend estático",
                context="Define si requiere servidor"
            ),
        ],
        AmbiguityType.DESIGN: [
            ClarificationQuestion(
                id="design_style",
                question="¿Qué estilo de diseño prefieres?",
                ambiguity_type=AmbiguityType.DESIGN,
                priority=QuestionPriority.HIGH,
                options=["Moderno oscuro", "Minimalista claro", "Corporativo profesional", "Colorido y vibrante", "Neo-bank/Fintech"],
                default_value="Moderno oscuro",
                context="Define la estética visual"
            ),
            ClarificationQuestion(
                id="design_colors",
                question="¿Tienes colores de marca?",
                ambiguity_type=AmbiguityType.DESIGN,
                priority=QuestionPriority.MEDIUM,
                options=["Sí, tengo paleta definida", "Prefiero azules", "Prefiero verdes", "Prefiero tonos cálidos", "Sorpréndeme"],
                default_value="Sorpréndeme",
                context="Define la paleta de colores"
            ),
        ],
        AmbiguityType.FUNCTIONALITY: [
            ClarificationQuestion(
                id="func_features",
                question="¿Qué funcionalidades necesitas?",
                ambiguity_type=AmbiguityType.FUNCTIONALITY,
                priority=QuestionPriority.CRITICAL,
                options=["Formulario de contacto", "Login/registro", "Carrito de compras", "Chat en vivo", "Búsqueda", "Ninguna especial"],
                context="Define las características principales"
            ),
            ClarificationQuestion(
                id="func_interactive",
                question="¿Necesitas elementos interactivos?",
                ambiguity_type=AmbiguityType.FUNCTIONALITY,
                priority=QuestionPriority.MEDIUM,
                options=["Animaciones y transiciones", "Sliders/carruseles", "Menú hamburguesa móvil", "Todo básico está bien"],
                default_value="Todo básico está bien",
                context="Define nivel de interactividad"
            ),
        ],
        AmbiguityType.DATA: [
            ClarificationQuestion(
                id="data_source",
                question="¿De dónde vendrán los datos?",
                ambiguity_type=AmbiguityType.DATA,
                priority=QuestionPriority.HIGH,
                options=["Contenido estático (yo lo proporciono)", "Base de datos propia", "API externa", "No requiere datos"],
                default_value="Contenido estático (yo lo proporciono)",
                context="Define origen de datos"
            ),
        ],
        AmbiguityType.INTEGRATION: [
            ClarificationQuestion(
                id="integration_services",
                question="¿Necesitas integrar algún servicio?",
                ambiguity_type=AmbiguityType.INTEGRATION,
                priority=QuestionPriority.MEDIUM,
                options=["Pagos (Stripe/PayPal)", "Email (SendGrid/Mailchimp)", "Analytics (Google)", "Redes sociales", "Ninguno"],
                default_value="Ninguno",
                context="Define integraciones externas"
            ),
        ],
    }
    
    CLARITY_INDICATORS = [
        r'(?:usando|con|en)\s+(?:python|flask|react|vue|html|javascript)',
        r'(?:estilo|diseño)\s+(?:tipo|como|similar\s+a)',
        r'(?:colores?)\s+(?:#[0-9a-fA-F]+|azul|rojo|verde|amarillo)',
        r'(?:secciones?|páginas?)\s*:',
        r'(?:funcionalidades?|características?)\s*:',
        r'\d+\s+(?:páginas?|secciones?|productos?|usuarios?)',
    ]
    
    def __init__(self):
        self.sessions: Dict[str, ClarificationSession] = {}
    
    def detect_ambiguity(self, request: str) -> AmbiguityDetection:
        """
        Detecta ambigüedades en una solicitud
        
        Args:
            request: Solicitud del usuario
        
        Returns:
            AmbiguityDetection con tipos de ambigüedad detectados
        """
        request_lower = request.lower()
        detected_types = []
        details = {}
        
        clarity_score = 0
        for pattern in self.CLARITY_INDICATORS:
            if re.search(pattern, request_lower):
                clarity_score += 1
        
        for amb_type, patterns in self.AMBIGUITY_PATTERNS.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, request_lower)
                if found:
                    matches.extend(found if isinstance(found[0], str) else [str(f) for f in found])
            
            if matches:
                detected_types.append(amb_type)
                details[amb_type.value] = {
                    "matches": matches[:3],
                    "count": len(matches)
                }
        
        word_count = len(request.split())
        if word_count < 10:
            if AmbiguityType.SCOPE not in detected_types:
                detected_types.append(AmbiguityType.SCOPE)
                details["scope"] = {"reason": "solicitud_muy_corta", "word_count": word_count}
        
        total_possible = len(self.AMBIGUITY_PATTERNS)
        ambiguity_ratio = len(detected_types) / total_possible
        
        confidence = max(0.2, min(1.0, ambiguity_ratio + (0.3 if word_count < 15 else 0) - (clarity_score * 0.15)))
        
        return AmbiguityDetection(
            detected=len(detected_types) > 0 and confidence > 0.3,
            ambiguity_types=detected_types,
            confidence=confidence,
            details=details
        )
    
    def generate_questions(self, request: str, 
                          ambiguity: AmbiguityDetection = None,
                          max_questions: int = None) -> List[ClarificationQuestion]:
        """
        Genera preguntas clarificadoras basadas en la solicitud
        
        Args:
            request: Solicitud original
            ambiguity: Detección de ambigüedad (si ya existe)
            max_questions: Número máximo de preguntas
        
        Returns:
            Lista de preguntas priorizadas
        """
        if ambiguity is None:
            ambiguity = self.detect_ambiguity(request)
        
        if not ambiguity.detected:
            return []
        
        max_q = max_questions or self.MAX_QUESTIONS
        all_questions = []
        
        for amb_type in ambiguity.ambiguity_types:
            templates = self.QUESTION_TEMPLATES.get(amb_type, [])
            for template in templates:
                question = ClarificationQuestion(
                    id=template.id,
                    question=template.question,
                    ambiguity_type=template.ambiguity_type,
                    priority=template.priority,
                    options=template.options.copy(),
                    default_value=template.default_value,
                    context=template.context
                )
                all_questions.append(question)
        
        all_questions.sort(key=lambda q: q.priority.value)
        
        seen_ids = set()
        unique_questions = []
        for q in all_questions:
            if q.id not in seen_ids:
                seen_ids.add(q.id)
                unique_questions.append(q)
        
        return unique_questions[:max_q]
    
    def create_session(self, session_id: str, user_id: str, 
                      request: str) -> ClarificationSession:
        """
        Crea una sesión de clarificación
        
        Args:
            session_id: ID de sesión
            user_id: ID de usuario
            request: Solicitud original
        
        Returns:
            ClarificationSession nueva
        """
        ambiguity = self.detect_ambiguity(request)
        questions = self.generate_questions(request, ambiguity)
        
        session = ClarificationSession(
            session_id=session_id,
            user_id=user_id,
            original_request=request,
            questions=questions,
            answers={},
            completed=len(questions) == 0
        )
        
        self.sessions[session_id] = session
        return session
    
    def submit_answer(self, session_id: str, question_id: str, 
                     answer: str) -> Tuple[bool, Optional[ClarificationQuestion]]:
        """
        Registra respuesta a una pregunta
        
        Args:
            session_id: ID de sesión
            question_id: ID de la pregunta
            answer: Respuesta del usuario
        
        Returns:
            Tupla (éxito, siguiente_pregunta o None si completado)
        """
        session = self.sessions.get(session_id)
        if not session:
            return False, None
        
        for question in session.questions:
            if question.id == question_id:
                question.answered = True
                question.answer = answer
                session.answers[question_id] = answer
                break
        
        unanswered = [q for q in session.questions if not q.answered]
        
        if not unanswered:
            session.completed = True
            return True, None
        
        return True, unanswered[0]
    
    def get_session(self, session_id: str) -> Optional[ClarificationSession]:
        """Obtiene una sesión por ID"""
        return self.sessions.get(session_id)
    
    def is_complete(self, session_id: str) -> bool:
        """Verifica si la clarificación está completa"""
        session = self.sessions.get(session_id)
        return session.completed if session else True
    
    def get_enriched_request(self, session_id: str) -> str:
        """
        Genera solicitud enriquecida con las respuestas
        
        Args:
            session_id: ID de sesión
        
        Returns:
            Solicitud original + contexto de respuestas
        """
        session = self.sessions.get(session_id)
        if not session:
            return ""
        
        enriched = session.original_request
        
        if session.answers:
            enriched += "\n\n### Especificaciones adicionales:\n"
            for q in session.questions:
                if q.answered and q.answer:
                    enriched += f"- {q.question} **{q.answer}**\n"
        
        return enriched
    
    def get_preferences(self, session_id: str) -> Dict[str, Any]:
        """
        Extrae preferencias detectadas de las respuestas
        
        Args:
            session_id: ID de sesión
        
        Returns:
            Dict con preferencias extraídas
        """
        session = self.sessions.get(session_id)
        if not session:
            return {}
        
        preferences = {}
        
        answer_mapping = {
            "scope_size": "scope",
            "scope_sections": "sections",
            "tech_stack": "technology",
            "tech_backend": "backend_needed",
            "design_style": "style",
            "design_colors": "colors",
            "func_features": "features",
            "func_interactive": "interactivity",
            "data_source": "data_source",
            "integration_services": "integrations",
        }
        
        for question_id, answer in session.answers.items():
            pref_key = answer_mapping.get(question_id, question_id)
            preferences[pref_key] = answer
        
        return preferences
    
    def format_questions_for_chat(self, questions: List[ClarificationQuestion]) -> str:
        """
        Formatea preguntas para mostrar en chat
        
        Args:
            questions: Lista de preguntas
        
        Returns:
            Texto formateado para el chat
        """
        if not questions:
            return ""
        
        output = "Para ayudarte mejor, necesito algunas aclaraciones:\n\n"
        
        for i, q in enumerate(questions, 1):
            output += f"**{i}. {q.question}**\n"
            if q.options:
                for opt in q.options:
                    output += f"   - {opt}\n"
            if q.default_value:
                output += f"   _(Por defecto: {q.default_value})_\n"
            output += "\n"
        
        output += "Responde con los números o escribe tu preferencia."
        
        return output
    
    def needs_clarification(self, request: str, threshold: float = 0.4) -> bool:
        """
        Verifica rápidamente si una solicitud necesita clarificación
        
        Args:
            request: Solicitud del usuario
            threshold: Umbral de confianza (default 0.4)
        
        Returns:
            True si necesita clarificación
        """
        ambiguity = self.detect_ambiguity(request)
        return ambiguity.detected and ambiguity.confidence >= threshold


clarification_manager = ClarificationManager()


def needs_clarification(request: str) -> bool:
    """Helper para verificar si necesita clarificación"""
    return clarification_manager.needs_clarification(request)


def generate_clarification_questions(request: str) -> List[Dict]:
    """Helper para generar preguntas"""
    questions = clarification_manager.generate_questions(request)
    return [q.to_dict() for q in questions]
