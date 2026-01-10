import * as vscode from 'vscode';
import fetch from 'node-fetch'; // Requires node-fetch (will need to install or use built-in fetch if Node 18+)

export class ChatViewProvider implements vscode.WebviewViewProvider {

    public static readonly viewType = 'bunk3r-sidebar-view';
    private _view?: vscode.WebviewView;

    constructor(
        private readonly _extensionUri: vscode.Uri,
    ) { }

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        _context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [
                this._extensionUri
            ]
        };

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        webviewView.webview.onDidReceiveMessage(async (data) => {
            switch (data.type) {
                case 'askAI':
                    await this.processUserMessage(data.message, data.userId);
                    break;
            }
        });
    }

    private async processUserMessage(message: string, userId: string = 'vscode-user') {
        if (!this._view) { return; }

        // Add User Message to UI
        this._view.webview.postMessage({ type: 'addMessage', role: 'user', content: message });

        // Get Editor Context (Active File)
        let activeContext = "";
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            const fileName = editor.document.fileName;
            const text = editor.document.getText();
            activeContext = `\n\n[Active File: ${fileName}]\n${text}`;
        }

        try {
            // Call BUNK3R Python Backend (Inside the container)
            const response = await fetch('http://127.0.0.1:5000/api/ide/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-ID': userId
                },
                body: JSON.stringify({
                    message: message + (activeContext ? activeContext.substring(0, 10000) : ""),
                    active_repo: "workspace"
                })
            });

            const data: any = await response.json();

            if (data.success) {
                this._view.webview.postMessage({ type: 'addMessage', role: 'ai', content: data.response || data.reply });
            } else {
                this._view.webview.postMessage({ type: 'addMessage', role: 'error', content: data.error || "Unknown error" });
            }

        } catch (error: any) {
            this._view.webview.postMessage({ type: 'addMessage', role: 'error', content: "Backend Connection Failed: " + error.message });
        }
    }

    public sendMessageToWebview(message: any) {
        if (this._view) {
            this._view.webview.postMessage(message);
        }
    }

    private _getHtmlForWebview(_webview: vscode.Webview) {
        return `<!DOCTYPE html>
			<html lang="en">
			<head>
				<meta charset="UTF-8">
				<meta name="viewport" content="width=device-width, initial-scale=1.0">
				<title>BUNK3R Chat</title>
				<style>
					body { font-family: var(--vscode-font-family); padding: 10px; color: var(--vscode-editor-foreground); background-color: var(--vscode-sideBar-background); }
					.chat-container { display: flex; flex-direction: column; gap: 10px; height: 95vh; }
					.messages { flex: 1; overflow-y: auto; padding-bottom: 20px; scroll-behavior: smooth; }
					.message { padding: 10px; border-radius: 8px; margin-bottom: 12px; max-width: 90%; line-height: 1.5; font-size: 0.95em; }
					.message.user { background: var(--vscode-button-background); color: var(--vscode-button-foreground); align-self: flex-end; margin-left: auto; }
					.message.ai { background: var(--vscode-editor-background); border: 1px solid var(--vscode-widget-border); align-self: flex-start; }
					.message.error { color: var(--vscode-errorForeground); border: 1px solid var(--vscode-errorForeground); background: rgba(255,0,0,0.1); }
					.input-area { position: sticky; bottom: 0; background: var(--vscode-sideBar-background); padding: 10px 0; display: flex; gap: 8px; border-top: 1px solid var(--vscode-widget-border); }
					input { flex: 1; padding: 10px; background: var(--vscode-input-background); color: var(--vscode-input-foreground); border: 1px solid var(--vscode-input-border); border-radius: 4px; outline: none; }
					input:focus { border-color: var(--vscode-focusBorder); }
					button { padding: 10px 16px; background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; border-radius: 4px; cursor: pointer; font-weight: 600; }
					button:hover { background: var(--vscode-button-hoverBackground); }
				</style>
			</head>
			<body>
				<div class="chat-container">
					<div class="messages" id="messages">
                        <div class="message ai">Hola, soy BUNK3R-IA. ¿En qué podemos trabajar hoy?</div>
                    </div>
					<div class="input-area">
						<input type="text" id="chatInput" placeholder="Escribe a BUNK3R..." />
						<button id="sendBtn">Enviar</button>
					</div>
				</div>
				<script>
					const vscode = acquireVsCodeApi();
					const messagesDiv = document.getElementById('messages');
					const input = document.getElementById('chatInput');
					const sendBtn = document.getElementById('sendBtn');
                    let currentUserId = 'unknown';

                    // Fetch User ID upon load
                    async function initAuth() {
                        try {
                            const res = await fetch('/api/auth/me');
                            const data = await res.json();
                            if (data.id) {
                                currentUserId = data.id;
                                console.log('BUNK3R Auth: Identified user ' + currentUserId);
                            }
                        } catch (e) {
                            console.error('BUNK3R Auth: Failed to identify user', e);
                        }
                    }
                    initAuth();

					function addMessage(role, content) {
						const div = document.createElement('div');
						div.className = 'message ' + role;
						div.innerText = content;
						messagesDiv.appendChild(div);
						messagesDiv.scrollTop = messagesDiv.scrollHeight;
					}

					function sendMessage() {
						const text = input.value;
						if (text) {
							vscode.postMessage({ type: 'askAI', message: text, userId: currentUserId });
							input.value = '';
						}
					}

					sendBtn.addEventListener('click', sendMessage);
					input.addEventListener('keydown', (e) => {
						if (e.key === 'Enter') {
							sendMessage();
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
