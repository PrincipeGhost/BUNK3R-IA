import websocket
import json

url = "wss://bunk3r-ia.onrender.com/api/ai/stream"

def on_message(ws, message):
    print("Received:", message)

def on_error(ws, error):
    print("ERROR:", error)

def on_close(ws, close_status_code, close_msg):
    print("Closed:", close_status_code, close_msg)

def on_open(ws):
    print("Connected!")
    payload = {
        "messages": [{"role": "user", "content": "Hola, prueba"}],
        "session_id": "test123"
    }
    ws.send(json.dumps(payload))

ws = websocket.WebSocketApp(url,
                            on_open=on_open,
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)

ws.run_forever()
