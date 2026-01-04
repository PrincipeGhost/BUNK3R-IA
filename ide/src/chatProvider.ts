import * as vscode from 'vscode';

export class Bunk3rChatProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'bunk3r.chatView';
    private _view?: vscode.WebviewView;

    constructor(private readonly _extensionUri: vscode.Uri) { }

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        _context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        webviewView.webview.onDidReceiveMessage((data: any) => {
            switch (data.type) {
                case 'sendMessage':
                    this._handleMessage(data.value);
                    break;
            }
        });
    }

    private async _handleMessage(message: string) {
        if (!this._view) return;

        // Add user message to UI
        this._view.webview.postMessage({ type: 'addMessage', role: 'user', content: message });

        try {
            // In a real scenario, we would call the BUNK3R API here
            // Example: const response = await this._callBunk3rAPI(message);
            const response = await this._mockAIService(message);

            this._view.webview.postMessage({ type: 'addMessage', role: 'assistant', content: response });

            // Safety check for [EDIT] tags (BUNK3R protocol)
            if (response.includes('[EDIT]')) {
                this._applyChanges(response);
            }
        } catch (error: any) {
            this._view.webview.postMessage({ type: 'addMessage', role: 'assistant', content: `Error: ${error.message}` });
        }
    }

    private async _mockAIService(message: string): Promise<string> {
        // Mocking a response with some logic
        return new Promise((resolve) => {
            setTimeout(() => {
                if (message.toLowerCase().includes('hola')) {
                    resolve("¡Hola! Soy BUNK3R AI. ¿En qué puedo ayudarte hoy?");
                } else if (message.toLowerCase().includes('crea un archivo')) {
                    resolve("Entendido. Creando archivo index.html... [EDIT] [NEW] index.html: <html><body><h1>Bunk3r Live</h1></body></html> [/EDIT]");
                } else {
                    resolve(`He recibido tu mensaje: "${message}". Estoy analizando tu repositorio.`);
                }
            }, 1000);
        });
    }

    private async _applyChanges(aiOutput: string) {
        // Robust parsing of [EDIT] blocks and usage of WorkspaceEdit
        const edit = new vscode.WorkspaceEdit();
        // Placeholder for real parsing logic
        console.log("Applying changes from AI output:", aiOutput);
        // await vscode.workspace.applyEdit(edit);
    }

    private _getHtmlForWebview(webview: vscode.Webview) {
        return `<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <style>
                    body { font-family: sans-serif; padding: 10px; background: #0d1117; color: #c9d1d9; }
                    #chat { height: calc(100vh - 80px); overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
                    .message { padding: 8px 12px; border-radius: 6px; max-width: 85%; }
                    .user { align-self: flex-end; background: #238636; color: white; }
                    .assistant { align-self: flex-start; background: #161b22; border: 1px solid #30363d; }
                    #input-container { display: flex; gap: 5px; margin-top: 10px; }
                    input { flex: 1; padding: 8px; border-radius: 4px; border: 1px solid #30363d; background: #0d1117; color: white; }
                    button { padding: 8px; background: #238636; color: white; border: none; border-radius: 4px; cursor: pointer; }
                </style>
            </head>
            <body>
                <div id="chat"></div>
                <div id="input-container">
                    <input type="text" id="userInput" placeholder="Pregunta a BUNK3R..." />
                    <button onclick="send()">Enviar</button>
                </div>
                <script>
                    const vscode = acquireVsCodeApi();
                    const chat = document.getElementById('chat');
                    const input = document.getElementById('userInput');

                    function send() {
                        const val = input.value.trim();
                        if (val) {
                            vscode.postMessage({ type: 'sendMessage', value: val });
                            input.value = '';
                        }
                    }

                    input.addEventListener('keypress', (e) => {
                        if (e.key === 'Enter') send();
                    });

                    window.addEventListener('message', event => {
                        const message = event.data;
                        if (message.type === 'addMessage') {
                            const div = document.createElement('div');
                            div.className = 'message ' + message.role;
                            div.textContent = message.content;
                            chat.appendChild(div);
                            chat.scrollTop = chat.scrollHeight;
                        }
                    });
                </script>
            </body>
            </html>`;
    }
}
