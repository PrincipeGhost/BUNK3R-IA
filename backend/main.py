from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
from backend.core.ai_service import AiService

app = FastAPI(title="BUNK3R-IA - Minimal AI Backend (Phase 1)")

ai = AiService()

@app.websocket("/api/ai/stream")
async def websocket_stream(websocket: WebSocket):
    """
    WebSocket endpoint minimal:
    - Cliente abre WS y envía un JSON inicial con { messages: [...] , session_id?: "..."}
    - Backend responde enviando mensajes tipo { type: 'token'|'complete'|'error', data: '...' }
    """
    await websocket.accept()
    try:
        payload = await websocket.receive_json()  # first message must be JSON
        messages = payload.get("messages", [])
        session_id = payload.get("session_id", None)

        # Notify start
        await websocket.send_json({"type": "start", "data": "streaming_started", "session_id": session_id})

        # Stream tokens from ai.stream_chat (async generator)
        async for token in ai.stream_chat(messages=messages, session_id=session_id):
            await websocket.send_json({"type": "token", "data": token})

        # Complete
        await websocket.send_json({"type": "complete", "data": "streaming_finished"})
    except WebSocketDisconnect:
        # client disconnected
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "data": str(e)})
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
