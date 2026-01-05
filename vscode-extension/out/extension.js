"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = void 0;
const vscode = require("vscode");
const ChatViewProvider_1 = require("./ChatViewProvider");
function activate(context) {
    console.log('Activating BUNK3R AI Extension...');
    // Register the Chat View Provider
    const provider = new ChatViewProvider_1.ChatViewProvider(context.extensionUri);
    context.subscriptions.push(vscode.window.registerWebviewViewProvider(ChatViewProvider_1.ChatViewProvider.viewType, provider));
    // Commands
    context.subscriptions.push(vscode.commands.registerCommand('bunk3r.refreshChat', () => {
        provider.sendMessageToWebview({ type: 'refresh' });
    }));
    console.log('BUNK3R AI Extension Activated.');
}
exports.activate = activate;
function deactivate() { }
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map