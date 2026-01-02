import asyncio
from typing import List, Optional, AsyncGenerator

class AiService:
    """
    Minimal AiService for Phase 1.
    - Proporciona stream_chat(messages) como un async generator que produce tokens uno a uno.
    - En Fase 2 reemplazaremos el cuerpo por la integración real con llm_phase_integrator/providers.
    """
    def __init__(self):
        pass

    async def stream_chat(self, messages: List[dict], session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        Generador async que emula streaming de tokens.
        messages: lista de {role, content} tal como el cliente enviará.
        """
        prompt_text = " ".join([m.get("content", "") for m in messages])[:200]
        reply = f"Respuesta simulada para: {prompt_text}".strip()
        if not reply:
            reply = "Respuesta por defecto simulada."

        # Stream por palabra para que el cliente reciba tokens legibles
        for chunk in reply.split(" "):
            await asyncio.sleep(0.03)  # simula latencia / generación
            yield chunk + " "
