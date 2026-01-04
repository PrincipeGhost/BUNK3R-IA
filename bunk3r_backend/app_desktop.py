import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QScrollBar
)
from PySide6.QtCore import Qt, QThread, Signal
import asyncio
import websockets
import json

# --- Worker para manejar WebSocket sin bloquear la UI ---
class WSWorker(QThread):
    new_token = Signal(str)
    finished = Signal()
    error = Signal(str)

    def __init__(self, ws_url, messages, session_id=None):
        super().__init__()
        self.ws_url = ws_url
        self.messages = messages
        self.session_id = session_id

    def run(self):
        asyncio.run(self.main())

    async def main(self):
        try:
            async with websockets.connect(self.ws_url) as ws:
                payload = {
                    "messages": self.messages,
                    "session_id": self.session_id
                }
                await ws.send(json.dumps(payload))

                async for message in ws:
                    obj = json.loads(message)
                    if obj.get("type") == "token":
                        self.new_token.emit(obj["data"])
                    elif obj.get("type") == "complete":
                        self.finished.emit()
                        break
        except Exception as e:
            self.error.emit(str(e))


# --- Ventana principal ---
class ChatApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BUNK3R-IA Desktop")
        self.resize(600, 700)

        self.layout = QVBoxLayout(self)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.layout.addWidget(self.chat_display)

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Escribe tu mensaje...")
        self.layout.addWidget(self.input_line)

        self.send_button = QPushButton("Enviar")
        self.layout.addWidget(self.send_button)

        self.send_button.clicked.connect(self.send_message)

        # WebSocket
        self.ws_worker = None
        self.ws_url = "wss://bunk3r-ia.onrender.com/api/ai/stream"

    def send_message(self):
        message = self.input_line.text().strip()
        if not message:
            return
        self.chat_display.append(f"<b>Usuario:</b> {message}")
        self.input_line.clear()

        # Lanzamos el worker de WebSocket
        self.ws_worker = WSWorker(self.ws_url, messages=[{"role": "user", "content": message}])
        self.ws_worker.new_token.connect(self.append_token)
        self.ws_worker.finished.connect(self.finish_stream)
        self.ws_worker.error.connect(self.show_error)
        self.ws_worker.start()

    def append_token(self, token):
        self.chat_display.moveCursor(Qt.TextCursor.End)
        self.chat_display.insertPlainText(token)
        self.chat_display.moveCursor(Qt.TextCursor.End)

    def finish_stream(self):
        self.chat_display.append("\n<b>IA:</b> [fin de respuesta]")

    def show_error(self, err):
        self.chat_display.append(f"<span style='color:red;'>Error: {err}</span>")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatApp()
    window.show()
    sys.exit(app.exec())
