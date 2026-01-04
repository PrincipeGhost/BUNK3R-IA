import * as vscode from 'vscode';
import { ChatViewProvider } from './ChatViewProvider';

export function activate(context: vscode.ExtensionContext) {
    console.log('Activating BUNK3R AI Extension...');

    // Register the Chat View Provider
    const provider = new ChatViewProvider(context.extensionUri);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(ChatViewProvider.viewType, provider)
    );

    // Commands
    context.subscriptions.push(
        vscode.commands.registerCommand('bunk3r.refreshChat', () => {
            provider.sendMessageToWebview({ type: 'refresh' });
        })
    );

    console.log('BUNK3R AI Extension Activated.');
}

export function deactivate() { }
