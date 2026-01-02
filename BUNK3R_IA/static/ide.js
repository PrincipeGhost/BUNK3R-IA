/**
 * BUNK3R IDE - Premium Development Environment
 * JavaScript Logic
 */

const IDE = {
    // State
    activeRepo: null,
    activeFile: null,
    editor: null,
    terminal: null,
    files: {},

    // Initialize IDE
    async init() {
        console.log('[IDE] Initializing BUNK3R IDE...');

        // Initialize components
        this.initEditor();
        this.initTerminal();
        this.initEventListeners();
        this.initTabs();

        // Load sync status
        await this.loadSyncStatus();

        // Load repositories
        await this.loadRepositories();

        console.log('[IDE] IDE initialized successfully');
    },

    // Monaco Editor
    initEditor() {
        require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' } });

        require(['vs/editor/editor.main'], () => {
            this.editor = monaco.editor.create(document.getElementById('monaco-editor'), {
                value: '// Selecciona un archivo para empezar',
                language: 'javascript',
                theme: 'vs-dark',
                automaticLayout: true,
                fontSize: 14,
                minimap: { enabled: true },
                scrollBeyondLastLine: false,
                wordWrap: 'on'
            });

            // Auto-save on change (debounced)
            let saveTimeout;
            this.editor.onDidChangeModelContent(() => {
                clearTimeout(saveTimeout);
                saveTimeout = setTimeout(() => this.autoSave(), 2000);
            });

            console.log('[IDE] Monaco Editor initialized');
        });
    },

    // Xterm Terminal
    initTerminal() {
        this.terminal = new Terminal({
            cursorBlink: true,
            fontSize: 13,
            fontFamily: 'Menlo, Monaco, "Courier New", monospace',
            theme: {
                background: '#0d1117',
                foreground: '#c9d1d9',
                cursor: '#f0b90b',
                selection: 'rgba(240, 185, 11, 0.3)'
            }
        });

        const fitAddon = new FitAddon.FitAddon();
        this.terminal.loadAddon(fitAddon);

        this.terminal.open(document.getElementById('terminal-container'));
        fitAddon.fit();

        this.terminal.writeln('\x1b[1;33m╔═══════════════════════════════════════╗\x1b[0m');
        this.terminal.writeln('\x1b[1;33m║\x1b[0m   BUNK3R Terminal - Ready          \x1b[1;33m║\x1b[0m');
        this.terminal.writeln('\x1b[1;33m╚═══════════════════════════════════════╝\x1b[0m');
        this.terminal.writeln('');

        // Handle terminal input
        let currentLine = '';
        this.terminal.onData(data => {
            if (data === '\r') { // Enter
                this.terminal.writeln('');
                this.executeCommand(currentLine);
                currentLine = '';
            } else if (data === '\u007F') { // Backspace
                if (currentLine.length > 0) {
                    currentLine = currentLine.slice(0, -1);
                    this.terminal.write('\b \b');
                }
            } else {
                currentLine += data;
                this.terminal.write(data);
            }
        });

        console.log('[IDE] Terminal initialized');
    },

    // Event Listeners
    initEventListeners() {
        // Tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => this.switchTab(btn.dataset.tab));
        });

        // Chat
        document.getElementById('send-btn').addEventListener('click', () => this.sendMessage());
        document.getElementById('chat-input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Repo selector
        document.getElementById('repo-selector').addEventListener('change', (e) => {
            this.switchRepo(e.target.value);
        });

        // Sync button
        document.getElementById('sync-btn').addEventListener('click', () => this.syncRepositories());

        // Settings
        document.getElementById('settings-btn').addEventListener('click', () => this.openSettings());
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', () => this.closeSettings());
        });
        document.getElementById('save-token-btn').addEventListener('click', () => this.saveGitHubToken());

        // Save button
        document.getElementById('save-btn').addEventListener('click', () => this.saveFile());

        // Preview refresh
        document.getElementById('refresh-preview-btn').addEventListener('click', () => this.refreshPreview());

        // Terminal clear
        document.getElementById('clear-terminal-btn').addEventListener('click', () => this.terminal.clear());

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                this.saveFile();
            }
        });
    },

    // Tab Management
    initTabs() {
        // Default to chat tab
        this.switchTab('chat');
    },

    switchTab(tabName) {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `${tabName}-tab`);
        });
    },

    // GitHub Sync
    async loadSyncStatus() {
        try {
            const response = await fetch('/api/github/sync/status');
            const data = await response.json();

            if (data.success) {
                this.updateSyncStatus(data);
            }
        } catch (error) {
            console.error('[IDE] Error loading sync status:', error);
        }
    },

    updateSyncStatus(status) {
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-text');

        if (status.ready > 0) {
            statusDot.className = 'status-dot synced';
            statusText.textContent = `${status.ready} repos sincronizados`;
        } else if (!status.has_token) {
            statusDot.className = 'status-dot';
            statusText.textContent = 'No sincronizado';
        } else {
            statusDot.className = 'status-dot syncing';
            statusText.textContent = 'Sincronizando...';
        }
    },

    async loadRepositories() {
        try {
            const response = await fetch('/api/ide/repos');
            const data = await response.json();

            if (data.success) {
                const selector = document.getElementById('repo-selector');
                selector.innerHTML = '<option value="">Seleccionar repositorio...</option>';

                data.repos.forEach(repo => {
                    const option = document.createElement('option');
                    option.value = repo.name;
                    option.textContent = repo.name;
                    selector.appendChild(option);
                });
            }
        } catch (error) {
            console.error('[IDE] Error loading repositories:', error);
        }
    },

    async switchRepo(repoName) {
        if (!repoName) return;

        this.activeRepo = repoName;
        console.log('[IDE] Switched to repo:', repoName);

        // Load file tree
        await this.loadFileTree(repoName);

        // Update terminal prompt
        this.terminal.writeln(`\x1b[1;33m[${repoName}]\x1b[0m Repository loaded`);
    },

    async loadFileTree(repoName) {
        try {
            const response = await fetch(`/api/ide/repo/index`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repo: repoName })
            });

            const data = await response.json();

            if (data.success) {
                this.renderFileTree(data.index.structure);
            }
        } catch (error) {
            console.error('[IDE] Error loading file tree:', error);
        }
    },

    renderFileTree(structure) {
        const fileTree = document.getElementById('file-tree');
        fileTree.innerHTML = '';

        structure.forEach(item => {
            if (item.type === 'file') {
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item';
                fileItem.style.paddingLeft = `${item.depth * 16 + 8}px`;
                fileItem.innerHTML = `📄 ${item.name}`;
                fileItem.addEventListener('click', () => this.openFile(item.path));
                fileTree.appendChild(fileItem);
            }
        });
    },

    async openFile(filePath) {
        if (!this.activeRepo) return;

        try {
            const response = await fetch(`/api/ide/file?repo=${this.activeRepo}&path=${encodeURIComponent(filePath)}`);
            const data = await response.json();

            if (data.success) {
                this.activeFile = filePath;

                // Detect language
                const ext = filePath.split('.').pop();
                const langMap = {
                    'js': 'javascript',
                    'ts': 'typescript',
                    'py': 'python',
                    'html': 'html',
                    'css': 'css',
                    'json': 'json',
                    'md': 'markdown'
                };
                const language = langMap[ext] || 'plaintext';

                // Update editor
                monaco.editor.setModelLanguage(this.editor.getModel(), language);
                this.editor.setValue(data.content);

                // Update preview if HTML
                if (ext === 'html') {
                    this.updatePreview(data.content);
                }

                console.log('[IDE] Opened file:', filePath);
            }
        } catch (error) {
            console.error('[IDE] Error opening file:', error);
        }
    },

    async saveFile() {
        if (!this.activeRepo || !this.activeFile) {
            console.warn('[IDE] No active file to save');
            return;
        }

        const content = this.editor.getValue();

        try {
            const response = await fetch('/api/ide/file', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    repo: this.activeRepo,
                    path: this.activeFile,
                    content: content
                })
            });

            const data = await response.json();

            if (data.success) {
                console.log('[IDE] File saved:', this.activeFile);
                this.terminal.writeln(`\x1b[1;32m✓\x1b[0m Saved: ${this.activeFile}`);

                // Update preview if HTML
                if (this.activeFile.endsWith('.html')) {
                    this.updatePreview(content);
                }
            }
        } catch (error) {
            console.error('[IDE] Error saving file:', error);
            this.terminal.writeln(`\x1b[1;31m✗\x1b[0m Error saving file`);
        }
    },

    autoSave() {
        if (this.activeFile) {
            this.saveFile();
        }
    },

    // Preview
    updatePreview(html) {
        const iframe = document.getElementById('preview-frame');
        iframe.srcdoc = html;
    },

    refreshPreview() {
        if (this.activeFile && this.activeFile.endsWith('.html')) {
            this.updatePreview(this.editor.getValue());
        }
    },

    // Chat with AI
    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();

        if (!message) return;

        // Add user message
        this.addChatMessage('user', message);
        input.value = '';

        // Show typing indicator
        const typingId = this.addChatMessage('assistant', '...');

        try {
            const response = await fetch('/api/ide/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    active_repo: this.activeRepo
                })
            });

            const data = await response.json();

            // Remove typing indicator
            document.getElementById(typingId).remove();

            if (data.success) {
                this.addChatMessage('assistant', data.response);
            } else {
                this.addChatMessage('assistant', `Error: ${data.error}`);
            }
        } catch (error) {
            document.getElementById(typingId).remove();
            this.addChatMessage('assistant', 'Error de conexión. Intenta de nuevo.');
            console.error('[IDE] Chat error:', error);
        }
    },

    addChatMessage(role, content) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        const messageId = `msg-${Date.now()}`;
        messageDiv.id = messageId;
        messageDiv.className = `chat-message ${role}`;

        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble';
        bubble.textContent = content;

        messageDiv.appendChild(bubble);
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        return messageId;
    },

    // Terminal
    async executeCommand(command) {
        if (!command.trim()) return;

        this.terminal.writeln(`\x1b[1;36m>\x1b[0m ${command}`);

        // Simple built-in commands
        if (command === 'clear') {
            this.terminal.clear();
            return;
        }

        if (command === 'help') {
            this.terminal.writeln('Available commands:');
            this.terminal.writeln('  clear  - Clear terminal');
            this.terminal.writeln('  help   - Show this help');
            this.terminal.writeln('');
            return;
        }

        // For now, just echo
        this.terminal.writeln(`Command not implemented: ${command}`);
        this.terminal.writeln('');
    },

    // Settings
    openSettings() {
        document.getElementById('settings-modal').classList.add('active');
    },

    closeSettings() {
        document.getElementById('settings-modal').classList.remove('active');
    },

    async saveGitHubToken() {
        const tokenInput = document.getElementById('github-token-input');
        const token = tokenInput.value.trim();

        if (!token) {
            alert('Por favor ingresa un token válido');
            return;
        }

        // Show loading
        document.getElementById('loading-overlay').classList.add('active');
        this.closeSettings();

        try {
            const response = await fetch('/api/github/token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token: token })
            });

            const data = await response.json();

            if (data.success) {
                console.log('[IDE] Token saved and repos synced:', data.sync_results);

                // Reload repositories
                await this.loadRepositories();
                await this.loadSyncStatus();

                // Clear token input
                tokenInput.value = '';

                alert(`✅ ${data.message}`);
            } else {
                alert(`Error: ${data.error}`);
            }
        } catch (error) {
            console.error('[IDE] Error saving token:', error);
            alert('Error de conexión. Intenta de nuevo.');
        } finally {
            document.getElementById('loading-overlay').classList.remove('active');
        }
    },

    async syncRepositories() {
        document.getElementById('loading-overlay').classList.add('active');

        try {
            const response = await fetch('/api/github/sync', { method: 'POST' });
            const data = await response.json();

            if (data.success) {
                await this.loadRepositories();
                await this.loadSyncStatus();
                alert('✅ Repositorios sincronizados');
            } else {
                alert(`Error: ${data.error}`);
            }
        } catch (error) {
            console.error('[IDE] Sync error:', error);
            alert('Error de conexión');
        } finally {
            document.getElementById('loading-overlay').classList.remove('active');
        }
    }
};

// Initialize on load
window.addEventListener('DOMContentLoaded', () => {
    IDE.init();
});
