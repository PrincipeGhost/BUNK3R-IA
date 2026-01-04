/**
 * BUNK3R IDE - Visual Studio Code Replica
 * Core JavaScript Logic
 */

const IDE = {
    // State
    activeRepo: null,
    activeFile: null,
    editor: null,
    terminal: null,
    fitAddon: null,
    openFiles: [], // For tabs

    // Initialize
    async init() {
        console.log('[IDE] Initializing VS Code Environment...');

        this.initSidebar();
        this.initEditor();
        this.initTerminal();
        this.initEventListeners();
        this.initPalette();

        // Load Initial Data
        await this.loadSyncStatus();
        await this.loadRepositories();

        // Check if there's a last opened repo/file in localStorage
        const lastRepo = localStorage.getItem('bunk3r_last_repo');
        if (lastRepo) {
            document.getElementById('repo-selector').value = lastRepo;
            await this.switchRepo(lastRepo);
        }

        console.log('[IDE] Ready.');
    },

    // Sidebar View Switching
    initSidebar() {
        const activityItems = document.querySelectorAll('.activity-item[data-sidebar]');
        activityItems.forEach(item => {
            item.addEventListener('click', () => {
                const viewName = item.dataset.sidebar;
                this.switchSidebarView(viewName);

                // Active state for icons
                activityItems.forEach(i => i.classList.remove('active'));
                item.classList.add('active');
            });
        });
    },

    switchSidebarView(viewName) {
        const sidebar = document.getElementById('side-bar');
        const views = document.querySelectorAll('.sidebar-view');
        const title = document.getElementById('sidebar-title');

        views.forEach(v => v.classList.remove('active'));
        const targetView = document.getElementById(`${viewName}-view`);

        if (targetView) {
            targetView.classList.add('active');
            title.textContent = viewName.toUpperCase();
            sidebar.style.display = 'flex';
        } else {
            // If view not found, maybe just toggle search or other built-ins
            console.warn(`[IDE] Sidebar view ${viewName} not implemented yet`);
        }
    },

    // Monaco Editor
    initEditor() {
        require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' } });

        require(['vs/editor/editor.main'], () => {
            // Define a more VS Code-like theme if possible (vs-dark is standard)
            this.editor = monaco.editor.create(document.getElementById('monaco-editor'), {
                value: '/* Welcome to BUNK3R IDE */\n// Select a file to start coding',
                language: 'javascript',
                theme: 'vs-dark',
                automaticLayout: true,
                fontSize: 14,
                fontFamily: "'Cascadia Code', 'Consolas', 'Courier New', monospace",
                minimap: { enabled: true, scale: 1, renderCharacters: false },
                scrollBeyondLastLine: false,
                wordWrap: 'on',
                lineHeight: 22,
                letterSpacing: 0.5,
                roundedSelection: true,
                cursorStyle: 'line',
                cursorBlinking: 'smooth',
                renderWhitespace: 'none',
                scrollbar: {
                    vertical: 'visible',
                    horizontal: 'visible',
                    useShadows: false,
                    verticalHasArrows: false,
                    horizontalHasArrows: false,
                    verticalScrollbarSize: 10,
                    horizontalScrollbarSize: 10
                }
            });

            // Handle content changes
            let saveTimeout;
            this.editor.onDidChangeModelContent(() => {
                clearTimeout(saveTimeout);
                saveTimeout = setTimeout(() => this.autoSave(), 3000);
            });

            window.addEventListener('resize', () => this.editor.layout());
        });
    },

    // Terminal
    initTerminal() {
        this.terminal = new Terminal({
            cursorBlink: true,
            fontSize: 13,
            fontFamily: "'Cascadia Code', 'Consolas', 'Courier New', monospace",
            theme: {
                background: '#1e1e1e',
                foreground: '#cccccc',
                cursor: '#aeafad',
                selection: '#264f78',
                black: '#000000',
                red: '#cd3131',
                green: '#0dbc79',
                yellow: '#e5e510',
                blue: '#2472c8',
                magenta: '#bc3fbc',
                cyan: '#11a8cd',
                white: '#e5e5e5'
            },
            allowProposedApi: true
        });

        this.fitAddon = new FitAddon.FitAddon();
        this.terminal.loadAddon(this.fitAddon);

        const container = document.getElementById('terminal-container');
        this.terminal.open(container);
        this.fitAddon.fit();

        this.terminal.writeln('\x1b[1;36mBUNK3R Terminal v2.0 - VS Code Integrated\x1b[0m');
        this.terminal.writeln('Type \x1b[1;33mhelp\x1b[0m to see available commands.');
        this.terminal.write('\r\n$ ');

        let currentLine = '';
        this.terminal.onData(data => {
            const code = data.charCodeAt(0);
            if (code === 13) { // Enter
                this.terminal.write('\r\n');
                this.executeTerminalCommand(currentLine);
                currentLine = '';
            } else if (code === 127) { // Backspace
                if (currentLine.length > 0) {
                    currentLine = currentLine.slice(0, -1);
                    this.terminal.write('\b \b');
                }
            } else if (code < 32) {
                // Ignore other control chars
            } else {
                currentLine += data;
                this.terminal.write(data);
            }
        });
    },

    async executeTerminalCommand(command) {
        const cmd = command.trim();
        if (!cmd) {
            this.terminal.write('$ ');
            return;
        }

        if (cmd === 'clear') {
            this.terminal.clear();
            this.terminal.write('$ ');
            return;
        }

        if (cmd === 'help') {
            this.terminal.writeln('Built-in commands: clear, help, exit');
            this.terminal.writeln('Internal API commands are proxied to the backend.');
            this.terminal.write('$ ');
            return;
        }

        try {
            // Use the actual terminal API
            const response = await fetch('/api/terminal/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    command: cmd,
                    repo: this.activeRepo
                })
            });
            const data = await response.json();

            if (data.output) {
                this.terminal.writeln(data.output);
            }
            if (data.error) {
                this.terminal.writeln(`\x1b[1;31mError: ${data.error}\x1b[0m`);
            }
        } catch (e) {
            this.terminal.writeln(`\x1b[1;31mConnection Error: ${e.message}\x1b[0m`);
        }

        this.terminal.write('$ ');
    },

    // UI Events
    initEventListeners() {
        // Repo Selection
        document.getElementById('repo-selector').addEventListener('change', (e) => {
            this.switchRepo(e.target.value);
        });

        // Chat
        document.getElementById('chat-input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendChatMessage();
            }
        });

        // Layout Resizing
        const resizer = document.getElementById('horizontal-resizer');
        const panel = document.getElementById('bottom-panel');
        let isResizing = false;

        resizer.addEventListener('mousedown', (e) => {
            isResizing = true;
            document.body.style.cursor = 'row-resize';
        });

        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            const containerHeight = document.querySelector('.editor-and-panel').offsetHeight;
            const offsetTop = document.querySelector('.editor-and-panel').getBoundingClientRect().top;
            const newPanelHeight = containerHeight - (e.clientY - offsetTop);

            if (newPanelHeight > 100 && newPanelHeight < containerHeight - 100) {
                panel.style.height = `${newPanelHeight}px`;
                if (this.editor) this.editor.layout();
                if (this.fitAddon) this.fitAddon.fit();
            }
        });

        document.addEventListener('mouseup', () => {
            isResizing = false;
            document.body.style.cursor = 'default';
        });

        // Global Shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                this.saveActiveFile();
            }
        });

        // Search
        document.getElementById('global-search-input').addEventListener('input', () => {
            clearTimeout(this.searchTimer);
            this.searchTimer = setTimeout(() => this.searchInRepo(), 500);
        });

        // SCM Commit
        document.getElementById('scm-commit-btn').addEventListener('click', () => this.commitChanges());
        document.getElementById('scm-commit-message').addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                this.commitChanges();
            }
        });

        // Settings/Modal
        document.getElementById('save-token-btn').addEventListener('click', () => this.saveGitHubToken());
    },

    // Repo and Files
    async switchRepo(repoName) {
        if (!repoName) return;
        this.activeRepo = repoName;
        localStorage.setItem('bunk3r_last_repo', repoName);

        // UI updates
        document.getElementById('loading-overlay').classList.add('active');

        try {
            const response = await fetch('/api/ide/repo/index', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repo: repoName })
            });
            const data = await response.json();

            if (data.success) {
                this.renderFileTree(data.index.structure);
                this.terminal.writeln(`\x1b[1;32mWorkspace loaded: ${repoName}\x1b[0m`);

                // Refresh Git Status
                await this.refreshGitStatus();
            }
        } catch (e) {
            console.error('Error switching repo', e);
        } finally {
            document.getElementById('loading-overlay').classList.remove('active');
        }
    },

    // Source Control Logic
    async refreshGitStatus() {
        if (!this.activeRepo) return;
        try {
            const res = await fetch(`/api/git/status?repo=${this.activeRepo}`);
            const data = await res.json();
            if (data.success) {
                this.renderGitChanges(data.changes);
                document.getElementById('git-branch-name').textContent = `${data.branch}*`;
            }
        } catch (e) {
            console.error('Git status failed', e);
        }
    },

    renderGitChanges(changes) {
        const container = document.getElementById('scm-changes-list');
        container.innerHTML = '<div class="scm-section-header">Changes</div>';

        if (changes.length === 0) {
            container.innerHTML += '<div style="padding: 10px; color: #888; font-size: 11px;">No changes detected.</div>';
            return;
        }

        changes.forEach(change => {
            const el = document.createElement('div');
            el.className = `scm-item ${change.status === ' M' ? 'modified' : change.status === '??' ? 'added' : ''}`;

            let statusChar = 'M';
            if (change.status === '??') statusChar = 'U';
            if (change.status === ' D') statusChar = 'D';

            el.innerHTML = `
                <span class="status">${statusChar}</span>
                <span class="path">${change.path}</span>
            `;

            // Interaction: Click to open
            el.addEventListener('click', () => this.openFile(change.path));
            container.appendChild(el);
        });
    },

    async commitChanges() {
        const msg = document.getElementById('scm-commit-message').value.trim();
        if (!msg || !this.activeRepo) return;

        try {
            // First stage all (simplified for now)
            await fetch('/api/git/stage', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repo: this.activeRepo, path: '.' })
            });

            const res = await fetch('/api/git/commit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repo: this.activeRepo, message: msg })
            });

            const data = await res.json();
            if (data.success) {
                document.getElementById('scm-commit-message').value = '';
                this.terminal.writeln(`\x1b[1;32m✓ Committed: ${msg}\x1b[0m`);
                await this.refreshGitStatus();
            } else {
                this.terminal.writeln(`\x1b[1;31m✗ Commit failed: ${data.stderr || data.error}\x1b[0m`);
            }
        } catch (e) {
            console.error('Commit error', e);
        }
    },

    // Search Logic
    async searchInRepo() {
        const query = document.getElementById('global-search-input').value.trim();
        const resultsContainer = document.getElementById('search-results');

        if (!query) {
            resultsContainer.innerHTML = '';
            return;
        }

        if (!this.activeRepo) return;

        resultsContainer.innerHTML = '<div style="color: #888; padding: 10px;">Searching...</div>';

        try {
            const res = await fetch('/api/ide/repo/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repo: this.activeRepo, query: query })
            });

            const data = await res.json();

            if (data.success) {
                this.renderSearchResults(data.results);
            } else {
                resultsContainer.innerHTML = `<div style="color: #f48771; padding: 10px;">Error: ${data.error}</div>`;
            }
        } catch (e) {
            console.error('Search error', e);
            resultsContainer.innerHTML = '<div style="color: #f48771; padding: 10px;">Connection Error</div>';
        }
    },

    renderSearchResults(results) {
        const container = document.getElementById('search-results');
        container.innerHTML = '';

        if (!results || results.length === 0) {
            container.innerHTML = '<div style="padding: 10px; color: #888; font-size: 11px;">No results found.</div>';
            return;
        }

        // Group by file
        const grouped = {};
        results.forEach(m => {
            if (!grouped[m.file]) grouped[m.file] = [];
            grouped[m.file].push(m);
        });

        Object.keys(grouped).forEach(fileName => {
            const fileGroup = document.createElement('div');
            fileGroup.className = 'search-file-group';

            const header = document.createElement('div');
            header.className = 'search-match-file';
            header.innerHTML = `Folder: ${fileName} <span style="background: #333; padding: 0 4px; border-radius: 10px; font-size: 10px;">${grouped[fileName].length}</span>`;
            fileGroup.appendChild(header);

            grouped[fileName].forEach(match => {
                const item = document.createElement('div');
                item.className = 'search-match-item';
                item.innerHTML = `
                    <div class="search-match-line">
                        <span style="color: #666; width: 20px; display: inline-block;">${match.line_number}</span>
                        ${this.escapeHtml(match.content).replace(new RegExp('(' + document.getElementById('global-search-input').value + ')', 'gi'), '<b>$1</b>')}
                    </div>
                `;
                item.addEventListener('click', async () => {
                    await this.openFile(fileName);
                    this.editor.revealLine(match.line_number);
                    this.editor.setPosition({ lineNumber: match.line_number, column: 1 });
                });
                fileGroup.appendChild(item);
            });

            container.appendChild(fileGroup);
        });
    },

    // Command Palette
    initPalette() {
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.key === 'P') {
                e.preventDefault();
                this.togglePalette();
            } else if (e.ctrlKey && e.key === 'P') {
                e.preventDefault();
                this.togglePalette('file');
            } else if (e.key === 'Escape') {
                document.getElementById('command-palette').classList.remove('active');
            }
        });

        const input = document.getElementById('palette-input');
        if (input) {
            input.addEventListener('input', (e) => this.filterPalette(e.target.value));
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') this.executePaletteCommand();
            });
        }
    },

    togglePalette(mode = 'command') {
        const palette = document.getElementById('command-palette');
        const input = document.getElementById('palette-input');
        const prefix = mode === 'command' ? '>' : '';

        palette.classList.add('active');
        input.value = prefix;
        input.focus();

        this.renderPaletteItems(mode);
    },

    renderPaletteItems(mode) {
        const list = document.getElementById('palette-list');
        list.innerHTML = '';

        let items = [];
        if (mode === 'command') {
            items = [
                { label: 'File: Save', command: () => this.saveActiveFile() },
                { label: 'Git: Commit', command: () => this.switchSidebarView('scm') },
                { label: 'View: Toggle Sync', command: () => this.syncRepositories() },
                { label: 'View: Output', command: () => this.switchTab('output') },
                { label: 'Developer: Reload Window', command: () => location.reload() }
            ];
        } else {
            // File mode (Quick Open)
            // Ideally should filter workspace files. 
            // For now, list open tabs or just a placeholder
            items = [
                { label: 'Search files by name logic not fully implemented yet' }
            ];
        }

        items.forEach((item, index) => {
            const el = document.createElement('div');
            el.className = 'palette-item';
            if (index === 0) el.classList.add('active');
            el.textContent = item.label;
            el.addEventListener('click', () => {
                if (item.command) item.command();
                document.getElementById('command-palette').classList.remove('active');
            });
            list.appendChild(el);
        });
    },

    renderFileTree(structure) {
        const fileTree = document.getElementById('file-tree');
        fileTree.innerHTML = `
            <div class="sidebar-section-header">
                <span class="arrow">▼</span>
                <span class="title">WORKSPACE</span>
            </div>
            <div class="sidebar-section-header">
                <span class="arrow">▼</span>
                <span class="title">FILES</span>
            </div>
            <div id="file-list-container"></div>
        `;

        const container = fileTree.querySelector('#file-list-container');

        // Sort items: folders first, then files
        const sorted = [...structure].sort((a, b) => {
            if (a.type !== b.type) return a.type === 'dir' ? -1 : 1;
            return a.name.localeCompare(b.name);
        });

        sorted.forEach(item => {
            if (item.type === 'file') {
                const el = document.createElement('div');
                el.className = 'file-item';
                el.style.paddingLeft = `${(item.depth * 15) + 30}px`;

                // Icon based on extension
                const ext = item.name.split('.').pop().toLowerCase();
                let icon = '📄';
                if (ext === 'py') icon = '🐍';
                if (ext === 'js' || ext === 'ts') icon = '📜';
                if (ext === 'html') icon = '🌐';
                if (ext === 'css') icon = '🎨';

                el.innerHTML = `<span class="icon" style="margin-right: 6px; font-size: 14px;">${icon}</span> <span class="name">${item.name}</span>`;
                el.addEventListener('click', () => this.openFile(item.path));
                container.appendChild(el);
            }
        });
    },

    async openFile(path) {
        if (!this.activeRepo) return;

        // Check if already open
        if (this.activeFile === path) return;
        this.activeFile = path;

        document.getElementById('active-filename').textContent = `${path.split('/').pop()} - BUNK3R IDE`;

        try {
            const response = await fetch(`/api/ide/file?repo=${this.activeRepo}&path=${encodeURIComponent(path)}`);
            const data = await response.json();

            if (data.success) {
                // Set language
                const ext = path.split('.').pop().toLowerCase();
                const model = this.editor.getModel();

                let lang = 'plaintext';
                if (ext === 'py') lang = 'python';
                if (ext === 'js') lang = 'javascript';
                if (ext === 'ts') lang = 'typescript';
                if (ext === 'html') lang = 'html';
                if (ext === 'css') lang = 'css';
                if (ext === 'json') lang = 'json';
                if (ext === 'md') lang = 'markdown';

                monaco.editor.setModelLanguage(model, lang);
                this.editor.setValue(data.content);

                // Add tab if not exists
                this.updateTabs(path);
            }
        } catch (e) {
            console.error('Error opening file', e);
        }
    },

    updateTabs(path) {
        const container = document.getElementById('editor-tabs');
        const filename = path.split('/').pop();

        // For now, simple single-active tab management
        container.innerHTML = `
            <div class="tab active">
                <span class="tab-title">${filename}</span>
                <span class="tab-close">&times;</span>
            </div>
        `;
    },

    async saveActiveFile() {
        if (!this.activeRepo || !this.activeFile) return;

        const content = this.editor.getValue();
        try {
            const res = await fetch('/api/ide/file', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    repo: this.activeRepo,
                    path: this.activeFile,
                    content: content
                })
            });
            const data = await res.json();
            if (data.success) {
                console.log('Saved successfully');
            }
        } catch (e) {
            console.error('Save failed', e);
        }
    },

    autoSave() {
        this.saveActiveFile();
    },

    // AI Chat
    async sendChatMessage() {
        const input = document.getElementById('chat-input');
        const text = input.value.trim();
        if (!text) return;

        this.addMessage('user', text);
        input.value = '';

        try {
            const res = await fetch('/api/ide/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    active_repo: this.activeRepo,
                    current_file: this.activeFile
                })
            });
            const data = await res.json();
            if (data.success) {
                this.addMessage('assistant', data.response);
            }
        } catch (e) {
            this.addMessage('assistant', 'Error connecting to Singularity.');
        }
    },

    addMessage(role, text) {
        const container = document.getElementById('chat-messages');
        const msg = document.createElement('div');
        msg.className = `chat-message ${role}`;
        msg.innerHTML = `
            <div class="msg-header">${role === 'user' ? 'You' : 'BUNK3R AI'}</div>
            <div class="msg-body">${this.escapeHtml(text).replace(/\n/g, '<br>')}</div>
        `;
        container.appendChild(msg);
        container.scrollTop = container.scrollHeight;
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    // Sync & Token
    async loadSyncStatus() {
        try {
            const res = await fetch('/api/github/sync/status');
            const data = await res.json();
            this.updateStatusBarSync(data);
        } catch (e) { }
    },

    updateStatusBarSync(data) {
        const text = document.querySelector('#sync-status .status-text');
        const dot = document.querySelector('#sync-status .status-dot');
        if (data.ready > 0) {
            text.textContent = 'Synced';
            dot.style.background = '#00ff00';
        } else {
            text.textContent = 'Pending Sync';
            dot.style.background = '#f0b90b';
        }
    },

    async loadRepositories() {
        try {
            const res = await fetch('/api/ide/repos');
            const data = await res.json();
            if (data.success) {
                const sel = document.getElementById('repo-selector');
                data.repos.forEach(r => {
                    const opt = document.createElement('option');
                    opt.value = r.name;
                    opt.textContent = r.name;
                    sel.appendChild(opt);
                });
            }
        } catch (e) { }
    },

    async saveGitHubToken() {
        const token = document.getElementById('github-token-input').value.trim();
        if (!token) return;

        try {
            const res = await fetch('/api/github/token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token })
            });
            const data = await res.json();
            if (data.success) {
                location.reload();
            }
        } catch (e) { }
    }
};

window.addEventListener('DOMContentLoaded', () => IDE.init());
