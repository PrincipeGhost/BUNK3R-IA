"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChatViewProvider = void 0;
const vscode = require("vscode");
const node_fetch_1 = require("node-fetch"); // Requires node-fetch (will need to install or use built-in fetch if Node 18+)
class ChatViewProvider {
    constructor(_extensionUri) {
        this._extensionUri = _extensionUri;
    }
    resolveWebviewView(webviewView, _context, _token) {
        this._view = webviewView;
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [
                this._extensionUri
            ]
        };
        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);
        webviewView.webview.onDidReceiveMessage((data) => __awaiter(this, void 0, void 0, function* () {
            switch (data.type) {
                case 'askAI':
                    yield this.processUserMessage(data.message);
                    break;
            }
        }));
    }
    processUserMessage(message) {
        return __awaiter(this, void 0, void 0, function* () {
            if (!this._view) {
                return;
            }
            // Add User Message to UI
            this._view.webview.postMessage({ type: 'addMessage', role: 'user', content: message });
            // Get Editor Context (Active File)
            let activeContext = "";
            const editor = vscode.window.activeTextEditor;
            if (editor) {
                activeContext = `\n\n[Active File: ${editor.document.fileName}]\n${editor.document.getText()}`;
            }
            try {
                // Call BUNK3R Python Backend
                // Assuming backend is running on localhost:5000
                const response = yield (0, node_fetch_1.default)('http://127.0.0.1:5000/api/ide/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-User-ID': 'vscode-user' },
                    body: JSON.stringify({
                        message: message + (activeContext ? activeContext.substring(0, 5000) : ""),
                        active_repo: "vscode-workspace"
                    })
                });
                const data = yield response.json();
                if (data.success) {
                    this._view.webview.postMessage({ type: 'addMessage', role: 'ai', content: data.reply });
                }
                else {
                    this._view.webview.postMessage({ type: 'addMessage', role: 'error', content: data.error || "Unknown error" });
                }
            }
            catch (error) {
                this._view.webview.postMessage({ type: 'addMessage', role: 'error', content: "Backend Connection Failed: " + error.message });
            }
        });
    }
    sendMessageToWebview(message) {
        if (this._view) {
            this._view.webview.postMessage(message);
        }
    }
    _getHtmlForWebview(_webview) {
        return `<!DOCTYPE html>
			<html lang="en">
			<head>
				<meta charset="UTF-8">
				<meta name="viewport" content="width=device-width, initial-scale=1.0">
				<title>BUNK3R Chat</title>
				<style>
					body { font-family: var(--vscode-font-family); padding: 10px; color: var(--vscode-editor-foreground); }
					.chat-container { display: flex; flex-direction: column; gap: 10px; height: 90vh; }
					.messages { flex: 1; overflow-y: auto; padding-bottom: 50px; }
					.message { padding: 8px; border-radius: 4px; margin-bottom: 8px; max-width: 90%; }
					.message.user { background: var(--vscode-button-background); color: var(--vscode-button-foreground); align-self: flex-end; margin-left: auto; }
					.message.ai { background: var(--vscode-editor-background); border: 1px solid var(--vscode-widget-border); align-self: flex-start; }
					.message.error { color: var(--vscode-errorForeground); border: 1px solid var(--vscode-errorForeground); }
					.input-area { position: fixed; bottom: 10px; left: 10px; right: 10px; display: flex; gap: 5px; }
					input { flex: 1; padding: 8px; background: var(--vscode-input-background); color: var(--vscode-input-foreground); border: 1px solid var(--vscode-input-border); }
					button { padding: 8px; background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; cursor: pointer; }
				</style>
			</head>
			<body>
				<div class="chat-container">
					<div class="messages" id="messages"></div>
					<div class="input-area">
						<input type="text" id="chatInput" placeholder="Ask BUNK3R..." />
						<button id="sendBtn">Send</button>
					</div>
				</div>
				<script>
					const vscode = acquireVsCodeApi();
					const messagesDiv = document.getElementById('messages');
					const input = document.getElementById('chatInput');
					const sendBtn = document.getElementById('sendBtn');

					function addMessage(role, content) {
						const div = document.createElement('div');
						div.className = 'message ' + role;
						div.innerText = content; // Simple text for now, could act HTML/Markdown later
						messagesDiv.appendChild(div);
						messagesDiv.scrollTop = messagesDiv.scrollHeight;
					}

					sendBtn.addEventListener('click', () => {
						const text = input.value;
						if (text) {
							vscode.postMessage({ type: 'askAI', message: text });
							input.value = '';
						}
					});

					input.addEventListener('keydown', (e) => {
						if (e.key === 'Enter') {
							const text = input.value;
							if (text) {
								vscode.postMessage({ type: 'askAI', message: text });
								input.value = '';
							}
						}
					});

					window.addEventListener('message', event => {
						const message = event.data;
						switch (message.type) {
							case 'addMessage':
								addMessage(message.role, message.content);
								break;
						}
					});
				</script>
			</body>
			</html>`;
    }
}
exports.ChatViewProvider = ChatViewProvider;
ChatViewProvider.viewType = 'bunk3r-sidebar-view';
//# sourceMappingURL=ChatViewProvider.js.map