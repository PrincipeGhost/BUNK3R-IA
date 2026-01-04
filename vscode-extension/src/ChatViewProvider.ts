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
        context: vscode.WebviewViewResolveContext,
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
                    await this.processUserMessage(data.message);
                    break;
            }
        });
    }

    private async processUserMessage(message: string) {
        if (!this._view) { return; }

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
            const response = await fetch('http://127.0.0.1:5000/api/ide/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-User-ID': 'vscode-user' },
                body: JSON.stringify({
                    message: message + (activeContext ? activeContext.substring(0, 5000) : ""), // Truncate context for now
                    active_repo: "vscode-workspace"
                })
            });

            const data: any = await response.json();

            if (data.success) {
                this._view.webview.postMessage({ type: 'addMessage', role: 'ai', content: data.reply });
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

    private _getHtmlForWebview(webview: vscode.Webview) {
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
