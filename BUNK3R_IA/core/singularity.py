import logging
import json
import time
import re
from typing import Optional, Dict, List, Any
from BUNK3R_IA.core.nervous_system import nervous_system
from BUNK3R_IA.core.gravity_core import gravity_core

logger = logging.getLogger(__name__)

class Singularity:
    """
    SINGULARIDAD (El Alma): Motor de razonamiento unificado.
    Implementa el Ciclo Consciente: REFLEXIÓN -> SIMULACIÓN -> EJECUCIÓN.
    """

    def __init__(self, ai_service=None):
        self.ai = ai_service  # Referencia al AIService para llamadas LLM
        self.monologue = []

    def solve(self, message: str, user_id: str, conversation: list, system_prompt: str) -> Dict:
        """Ciclo Maestro de Resolución: Pensar -> Simular -> Actuar."""
        logger.info("Singularity: Iniciando pulso de pensamiento unificado...")
        
        # 1. MONÓLOGO INTERNO (REFLEXIÓN)
        # BUNK3R analiza la petición antes de ver herramientas.
        reflection_prompt = f"USER MSG: {message}\nREFLEXIÓN INTERNA: Analiza el impacto técnico, riesgos de seguridad y qué archivos del core se verán afectados. No respondas al usuario aún, solo reflexiona."
        reflection = self._llm_call(reflection_prompt, "Eres el Arquitecto Senior BUNK3R. Tu monólogo interno es crítico y técnico.")
        logger.info(f"🧠 MONÓLOGO: {reflection}")
        
        # 2. EVALUACIÓN DE RIESGO & SANDBOX
        # Si la reflexión detecta peligro, activamos el Sandbox.
        risk_keywords = [
            "crash", "delete", "format", "rm -rf", "db migration", "main.py",
            "exploit", "vulnerabilit", "security hole", "break into", "hacker",
            "malware", "virus", "shell script", "root access", "sandbox"
        ]
        # Búsqueda robusta e insensible a mayúsculas
        reflection_lower = reflection.lower()
        high_risk = any(k in reflection_lower for k in risk_keywords)
        nervous_system.sandbox_mode = high_risk
        
        if high_risk:
            logger.warning("🧪 MODO SIMULACIÓN ACTIVADO: Sistema en Sandbox por seguridad.")
            reflection += "\n[ALERTA DE SEGURIDAD] Operación redirigida al Sandbox."

        # 3. PLANIFICACIÓN & EJECUCIÓN AGÉNTICA
        # Aquí delegamos al loop de herramientas unificado
        final_response = self._run_agent_loop(message, conversation, system_prompt, reflection)
        
        return {
            "success": True,
            "response": final_response,
            "reflection": reflection,
            "simulated": high_risk
        }

    def _llm_call(self, prompt: str, system: str) -> str:
        """Llamada rápida al LLM (vía AIService) para procesos internos."""
        if not self.ai: return "Reflexión offline activa."
        # Usamos council_query para reflexiones de alta calidad si es posible
        return self.ai.council_query(prompt, system)

    def _run_agent_loop(self, message: str, conversation: list, system: str, reflection: str) -> str:
        """Loop de ejecución unificado con el Nervous System."""
        
        # 1. ¿Hay herramientas en la reflexión inicial? (Caso de uso del usuario)
        import re
        tool_match = re.search(r'<TOOL>(.*?)</TOOL>', reflection, re.DOTALL)
        if tool_match:
            tool_json_str = tool_match.group(1).strip()
            try:
                # Si la reflexión ya trae una herramienta, la ejecutamos antes del loop
                logger.info(f"Singularity: Detectada herramienta en REFLEXIÓN: {tool_json_str[:50]}...")
                tool_call = json.loads(tool_json_str)
                tool_output = self.ai._call_tool(tool_call.get("name"), tool_call.get("args", {}))
                reflection += f"\n[SISTEMA] Resultado de herramienta en reflexión: {tool_output}"
            except Exception as e:
                logger.error(f"Error procesando herramienta en reflexión: {e}")

        # Inyectamos la reflexión (posiblemente con resultado de tool) en el contexto
        enhanced_system = f"{system}\n\nTU REFLEXIÓN INTERNA:\n{reflection}\n\nSi necesitas actuar, usa <TOOL>{{'name': '...', 'args': {{...}}}}</TOOL>."
        
        # 2. Delegamos al loop interactivo para pasos adicionales
        res = self.ai._internal_chat_loop(conversation, enhanced_system)
        return res

# El Alma Unificada lista para latir
singularity = Singularity()

# El Alma Unificada lista para latir
singularity = Singularity()
