import * as vscode from 'vscode';
import { Bunk3rChatProvider } from './chatProvider';
import { Bunk3rPreviewProvider } from './previewProvider';

export function activate(context: vscode.ExtensionContext) {
    console.log('BUNK3R AI is now active!');

    // Register Chat Provider for the secondary sidebar
    const chatProvider = new Bunk3rChatProvider(context.extensionUri);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(Bunk3rChatProvider.viewType, chatProvider)
    );

    // Register Preview Provider as a Custom Editor
    context.subscriptions.push(
        vscode.window.registerCustomEditorProvider(Bunk3rPreviewProvider.viewType, new Bunk3rPreviewProvider(context))
    );

    // Command to open chat (optional)
    context.subscriptions.push(vscode.commands.registerCommand('bunk3r.openChat', () => {
        vscode.commands.executeCommand('workbench.view.extension.bunk3r-ai-container');
    }));
}

export function deactivate() { }
