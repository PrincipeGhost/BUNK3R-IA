import * as vscode from 'vscode';

export class Bunk3rPreviewProvider implements vscode.CustomTextEditorProvider {
    public static readonly viewType = 'bunk3r.preview';

    constructor(private readonly context: vscode.ExtensionContext) { }

    public async resolveCustomTextEditor(
        document: vscode.TextDocument,
        webviewPanel: vscode.WebviewPanel,
        _token: vscode.CancellationToken
    ): Promise<void> {
        webviewPanel.webview.options = { enableScripts: true };

        const updateWebview = () => {
            webviewPanel.webview.html = this._getHtmlForWebview(webviewPanel.webview, document.getText());
        };

        const changeDocumentSubscription = vscode.workspace.onDidChangeTextDocument((e: vscode.TextDocumentChangeEvent) => {
            if (e.document.uri.toString() === document.uri.toString()) {
                updateWebview();
            }
        });

        webviewPanel.onDidDispose(() => {
            changeDocumentSubscription.dispose();
        });

        updateWebview();
    }

    private _getHtmlForWebview(webview: vscode.Webview, content: string) {
        return `<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <style>
                    body, html { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background: white; }
                    iframe { width: 100%; height: 100%; border: none; background: white; }
                </style>
            </head>
            <body>
                <iframe id="preview" srcdoc="${content.replace(/"/g, '&quot;')}"></iframe>
                <script>
                    window.addEventListener('message', event => {
                        // Keep connection alive or handle interaction
                    });
                </script>
            </body>
            </html>`;
    }
}
