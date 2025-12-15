const Workspace = {
    state: {
        currentFile: null,
        files: [],
        messages: [],
        mentalState: 'LISTO',
        isProcessing: false
    },

    init() {
        this.setupEventListeners();
        this.loadFiles();
        this.updateTime();
        this.setupResizers();
        setInterval(() => this.updateTime(), 1000);
    },

    setupEventListeners() {
        document.getElementById('send-btn').addEventListener('click', () => this.sendMessage());
        document.getElementById('chat-input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        document.getElementById('chat-input').addEventListener('input', (e) => {
            e.target.style.height = 'auto';
            e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
        });

        document.getElementById('clear-chat').addEventListener('click', () => this.clearChat());
        document.getElementById('refresh-files').addEventListener('click', () => this.loadFiles());
        document.getElementById('refresh-preview').addEventListener('click', () => this.refreshPreview());
        document.getElementById('open-external').addEventListener('click', () => this.openExternal());

        document.getElementById('preview-url').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.refreshPreview();
            }
        });

        document.getElementById('files-search').addEventListener('input', (e) => {
            this.filterFiles(e.target.value);
        });

        document.getElementById('close-file-modal').addEventListener('click', () => {
            document.getElementById('file-modal').classList.add('hidden');
        });

        document.getElementById('save-file-btn').addEventListener('click', () => this.saveFile());

        document.getElementById('new-file-btn').addEventListener('click', () => this.createNewFile());
        document.getElementById('new-folder-btn').addEventListener('click', () => this.createNewFolder());
    },

    setupResizers() {
        const resizerLeft = document.getElementById('resizer-left');
        const resizerRight = document.getElementById('resizer-right');
        const panelLeft = document.getElementById('panel-chat');
        const panelRight = document.getElementById('panel-files');

        this.makeResizable(resizerLeft, panelLeft, 'left');
        this.makeResizable(resizerRight, panelRight, 'right');
    },

    makeResizable(resizer, panel, direction) {
        let startX, startWidth;

        resizer.addEventListener('mousedown', (e) => {
            startX = e.clientX;
            startWidth = panel.offsetWidth;
            resizer.classList.add('active');

            document.addEventListener('mousemove', resize);
            document.addEventListener('mouseup', stopResize);
        });

        const resize = (e) => {
            const diff = direction === 'left' ? e.clientX - startX : startX - e.clientX;
            const newWidth = startWidth + diff;
            const minWidth = parseInt(getComputedStyle(panel).minWidth) || 200;
            const maxWidth = parseInt(getComputedStyle(panel).maxWidth) || 500;

            if (newWidth >= minWidth && newWidth <= maxWidth) {
                panel.style.width = newWidth + 'px';
            }
        };

        const stopResize = () => {
            resizer.classList.remove('active');
            document.removeEventListener('mousemove', resize);
            document.removeEventListener('mouseup', stopResize);
        };
    },

    getApiHeaders() {
        const headers = { 'Content-Type': 'application/json' };
        if (typeof App !== 'undefined') {
            if (App.isDemoMode) {
                headers['X-Demo-Mode'] = 'true';
                const token = App.demoSessionToken || sessionStorage.getItem('demoSessionToken');
                if (token) {
                    headers['X-Demo-Session'] = token;
                }
            } else if (App.initData) {
                headers['X-Telegram-Init-Data'] = App.initData;
            }
        }
        return headers;
    },

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();

        if (!message || this.state.isProcessing) return;

        this.addMessage(message, 'user');
        input.value = '';
        input.style.height = 'auto';

        this.setMentalState('PROCESANDO', '🤔');
        this.state.isProcessing = true;

        try {
            const response = await fetch('/api/ai-constructor/process', {
                method: 'POST',
                headers: this.getApiHeaders(),
                body: JSON.stringify({ message })
            });

            const data = await response.json();

            if (data.success) {
                if (data.fase_nombre) {
                    this.updateCurrentTask(`Fase ${data.fase}: ${data.fase_nombre}`);
                }
                
                if (data.response) {
                    this.addMessage(data.response, 'assistant');
                }
                
                if (data.plan && data.esperando_input) {
                    this.showPlanConfirmation(data.plan);
                }
                
                if (data.files) {
                    this.handleGeneratedFiles(data.files);
                }
            } else if (data.error) {
                this.addMessage('Error: ' + data.error, 'assistant');
            }
        } catch (error) {
            this.addMessage('Error de conexion. Intenta de nuevo.', 'assistant');
        }

        this.setMentalState('LISTO', '🧘');
        this.state.isProcessing = false;
    },

    updateCurrentTask(taskText) {
        const taskEl = document.getElementById('current-task');
        if (taskEl) {
            taskEl.innerHTML = `<span class="task-icon">⚙️</span><span class="task-text">${this.escapeHtml(taskText)}</span>`;
        }
    },

    showPlanConfirmation(plan) {
        const container = document.getElementById('chat-messages');
        const confirmDiv = document.createElement('div');
        confirmDiv.className = 'plan-confirmation';
        confirmDiv.id = 'plan-confirmation';
        confirmDiv.innerHTML = `
            <div class="plan-actions">
                <button class="plan-btn confirm" id="confirm-plan">Continuar</button>
                <button class="plan-btn cancel" id="cancel-plan">Ajustar</button>
            </div>
        `;
        container.appendChild(confirmDiv);
        
        document.getElementById('confirm-plan').addEventListener('click', () => {
            confirmDiv.remove();
            this.respondToPlan('Si, continuar');
        });
        
        document.getElementById('cancel-plan').addEventListener('click', () => {
            confirmDiv.remove();
            this.respondToPlan('No, quiero ajustar');
        });
    },

    async respondToPlan(response) {
        this.addMessage(response, 'user');
        this.setMentalState('GENERANDO', '🚀');
        this.state.isProcessing = true;
        
        try {
            const resp = await fetch('/api/ai-constructor/process', {
                method: 'POST',
                headers: this.getApiHeaders(),
                body: JSON.stringify({ message: response })
            });
            
            const data = await resp.json();
            
            if (data.success && data.response) {
                this.addMessage(data.response, 'assistant');
            }
            
            if (data.files) {
                this.handleGeneratedFiles(data.files);
            }
        } catch (error) {
            this.addMessage('Error de conexion.', 'assistant');
        }
        
        this.setMentalState('LISTO', '🧘');
        this.state.isProcessing = false;
    },

    async handleGeneratedFiles(files) {
        const generatedPaths = [];
        
        for (const [filename, content] of Object.entries(files)) {
            try {
                const response = await fetch('/api/files/save', {
                    method: 'POST',
                    headers: this.getApiHeaders(),
                    body: JSON.stringify({ path: filename, content: content })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.addMessage(`Archivo generado: ${filename}`, 'assistant');
                    generatedPaths.push(filename);
                } else {
                    this.addMessage(`Error guardando ${filename}: ${data.error}`, 'assistant');
                }
            } catch (error) {
                this.addMessage(`Error guardando ${filename}`, 'assistant');
            }
        }
        
        await this.loadFiles();
        
        if (generatedPaths.length > 0) {
            this.highlightGeneratedFiles(generatedPaths);
            this.autoExpandToFile(generatedPaths[0]);
            
            const htmlFiles = generatedPaths.filter(p => p.endsWith('.html'));
            if (htmlFiles.length > 0) {
                this.updatePreviewWithFile(htmlFiles[0]);
            }
        }
    },
    
    highlightGeneratedFiles(paths) {
        paths.forEach(path => {
            const item = document.querySelector(`[data-path="${path}"]`);
            if (item) {
                item.classList.add('tree-item-new');
                setTimeout(() => item.classList.remove('tree-item-new'), 3000);
            }
        });
    },
    
    autoExpandToFile(path) {
        const parts = path.split('/');
        let currentPath = '';
        
        parts.forEach((part, index) => {
            if (index < parts.length - 1) {
                currentPath = currentPath ? `${currentPath}/${part}` : part;
                const folderItem = document.querySelector(`[data-path="${currentPath}"]`);
                if (folderItem) {
                    const children = folderItem.nextElementSibling;
                    if (children && children.classList.contains('tree-children')) {
                        children.classList.remove('collapsed');
                        const toggle = folderItem.querySelector('.tree-toggle');
                        if (toggle) toggle.classList.add('expanded');
                    }
                }
            }
        });
        
        const fileItem = document.querySelector(`[data-path="${path}"]`);
        if (fileItem) {
            fileItem.classList.add('selected');
            fileItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    },
    
    updatePreviewWithFile(htmlPath) {
        const urlInput = document.getElementById('preview-url');
        if (urlInput) {
            urlInput.value = '/' + htmlPath;
        }
        this.refreshPreview();
    },

    addMessage(text, type) {
        const container = document.getElementById('chat-messages');
        const now = new Date();
        const time = now.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });

        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${type}`;

        if (type === 'assistant') {
            messageDiv.innerHTML = `
                <div class="message-avatar">
                    <span class="avatar-icon">🤖</span>
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <span class="message-author">BUNK3R</span>
                        <span class="message-time">${time}</span>
                    </div>
                    <div class="message-text">${this.formatMessage(text)}</div>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-avatar">
                    <span class="avatar-icon">👤</span>
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <span class="message-author">Tu</span>
                        <span class="message-time">${time}</span>
                    </div>
                    <div class="message-text">${this.escapeHtml(text)}</div>
                </div>
            `;
        }

        container.appendChild(messageDiv);
        container.scrollTop = container.scrollHeight;
    },

    formatMessage(text) {
        let formatted = this.escapeHtml(text);
        formatted = formatted.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
        formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
        formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        formatted = formatted.replace(/\n/g, '<br>');
        return formatted;
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    clearChat() {
        const container = document.getElementById('chat-messages');
        container.innerHTML = `
            <div class="message message-assistant">
                <div class="message-avatar">
                    <span class="avatar-icon">🤖</span>
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <span class="message-author">BUNK3R</span>
                        <span class="message-time">Ahora</span>
                    </div>
                    <div class="message-text">
                        <p>Chat limpiado. ¿En que puedo ayudarte?</p>
                    </div>
                </div>
            </div>
        `;
    },

    async loadFiles() {
        const tree = document.getElementById('files-tree');
        tree.innerHTML = '<div class="tree-loading"><div class="spinner"></div><span>Cargando archivos...</span></div>';

        try {
            const response = await fetch('/api/files/tree');
            const data = await response.json();

            if (data.tree) {
                this.state.files = data.tree;
                this.renderFileTree(data.tree);
                document.getElementById('files-count').textContent = `${data.total_files || 0} archivos`;
            }
        } catch (error) {
            tree.innerHTML = '<div class="tree-loading"><span>Error cargando archivos</span></div>';
        }
    },

    renderFileTree(items, container = null) {
        if (!container) {
            container = document.getElementById('files-tree');
            container.innerHTML = '';
        }

        items.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.className = `tree-item tree-item-${item.type}`;
            itemDiv.dataset.path = item.path;

            const icon = item.type === 'folder' ? '📁' : this.getFileIcon(item.name);

            if (item.type === 'folder') {
                itemDiv.innerHTML = `
                    <span class="tree-toggle">▶</span>
                    <span class="tree-item-icon">${icon}</span>
                    <span class="tree-item-name">${this.escapeHtml(item.name)}</span>
                `;

                itemDiv.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.toggleFolder(itemDiv, item);
                    document.querySelectorAll('.tree-item').forEach(el => el.classList.remove('selected'));
                    itemDiv.classList.add('selected');
                });
            } else {
                itemDiv.innerHTML = `
                    <span class="tree-item-icon">${icon}</span>
                    <span class="tree-item-name">${this.escapeHtml(item.name)}</span>
                `;

                itemDiv.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.openFile(item);
                });
            }
            
            itemDiv.addEventListener('contextmenu', (e) => {
                this.showContextMenu(e, item);
            });

            container.appendChild(itemDiv);

            if (item.type === 'folder' && item.children) {
                const childrenDiv = document.createElement('div');
                childrenDiv.className = 'tree-children collapsed';
                this.renderFileTree(item.children, childrenDiv);
                container.appendChild(childrenDiv);
            }
        });
    },

    getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const icons = {
            'py': '🐍',
            'js': '📜',
            'ts': '📘',
            'html': '🌐',
            'css': '🎨',
            'json': '📋',
            'md': '📝',
            'txt': '📄',
            'sql': '🗃️',
            'png': '🖼️',
            'jpg': '🖼️',
            'gif': '🖼️',
            'svg': '🎨'
        };
        return icons[ext] || '📄';
    },

    toggleFolder(element, item) {
        const toggle = element.querySelector('.tree-toggle');
        const children = element.nextElementSibling;

        if (children && children.classList.contains('tree-children')) {
            children.classList.toggle('collapsed');
            toggle.classList.toggle('expanded');
        }
    },

    async openFile(item) {
        document.querySelectorAll('.tree-item').forEach(el => el.classList.remove('selected'));
        document.querySelector(`[data-path="${item.path}"]`)?.classList.add('selected');

        try {
            const response = await fetch(`/api/files/content?path=${encodeURIComponent(item.path)}`);
            const data = await response.json();

            if (data.content !== undefined) {
                this.state.currentFile = item.path;
                document.getElementById('file-modal-title').textContent = item.name;
                document.getElementById('editor-file-path').textContent = item.path;
                document.getElementById('file-content').value = data.content;
                document.getElementById('file-modal').classList.remove('hidden');
            }
        } catch (error) {
            console.error('Error opening file:', error);
        }
    },

    async saveFile() {
        if (!this.state.currentFile) return;

        const content = document.getElementById('file-content').value;

        try {
            const response = await fetch('/api/files/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    path: this.state.currentFile,
                    content: content
                })
            });

            const data = await response.json();

            if (data.success) {
                this.addMessage(`Archivo guardado: ${this.state.currentFile}`, 'assistant');
                document.getElementById('file-modal').classList.add('hidden');
            }
        } catch (error) {
            console.error('Error saving file:', error);
        }
    },

    filterFiles(query) {
        const items = document.querySelectorAll('.tree-item');
        query = query.toLowerCase();

        items.forEach(item => {
            const name = item.querySelector('.tree-item-name').textContent.toLowerCase();
            const matches = name.includes(query);
            item.style.display = matches || !query ? '' : 'none';
        });
    },

    refreshPreview() {
        const url = document.getElementById('preview-url').value || '/';
        const iframe = document.getElementById('preview-iframe');
        const placeholder = document.getElementById('preview-placeholder');

        placeholder.classList.add('hidden');
        iframe.src = url;
    },

    openExternal() {
        const url = document.getElementById('preview-url').value || '/';
        window.open(url, '_blank');
    },

    handleApiError(response, data) {
        if (response.status === 401) {
            this.addMessage('Sesion expirada. Por favor verifica tu autenticacion.', 'assistant');
            window.location.href = '/';
            return true;
        }
        if (!data.success && data.error) {
            this.addMessage(`Error: ${data.error}`, 'assistant');
            return true;
        }
        return false;
    },

    async createNewFile() {
        const name = prompt('Nombre del archivo (ej: mi_archivo.py):');
        if (!name) return;
        
        const path = this.getSelectedFolderPath() + '/' + name;
        const cleanPath = path.replace(/^\/+/, '');
        
        try {
            const response = await fetch('/api/files/create', {
                method: 'POST',
                headers: this.getApiHeaders(),
                body: JSON.stringify({ path: cleanPath, content: '' })
            });
            
            const data = await response.json();
            
            if (this.handleApiError(response, data)) return;
            
            if (data.success) {
                this.addMessage(`Archivo creado: ${cleanPath}`, 'assistant');
                this.loadFiles();
                this.openFileByPath(cleanPath);
            }
        } catch (error) {
            this.addMessage('Error de conexion al crear archivo', 'assistant');
        }
    },

    async createNewFolder() {
        const name = prompt('Nombre de la carpeta:');
        if (!name) return;
        
        const path = this.getSelectedFolderPath() + '/' + name;
        const cleanPath = path.replace(/^\/+/, '');
        
        try {
            const response = await fetch('/api/files/folder', {
                method: 'POST',
                headers: this.getApiHeaders(),
                body: JSON.stringify({ path: cleanPath })
            });
            
            const data = await response.json();
            
            if (this.handleApiError(response, data)) return;
            
            if (data.success) {
                this.addMessage(`Carpeta creada: ${cleanPath}`, 'assistant');
                this.loadFiles();
            }
        } catch (error) {
            this.addMessage('Error de conexion al crear carpeta', 'assistant');
        }
    },

    getSelectedFolderPath() {
        const selected = document.querySelector('.tree-item.selected');
        if (selected) {
            const path = selected.dataset.path;
            if (selected.classList.contains('tree-item-folder')) {
                return path;
            }
            const parts = path.split('/');
            parts.pop();
            return parts.join('/');
        }
        return '';
    },

    async openFileByPath(path) {
        try {
            const response = await fetch(`/api/files/content?path=${encodeURIComponent(path)}`);
            const data = await response.json();
            
            if (data.content !== undefined) {
                this.state.currentFile = path;
                const name = path.split('/').pop();
                document.getElementById('file-modal-title').textContent = name;
                document.getElementById('editor-file-path').textContent = path;
                document.getElementById('file-content').value = data.content;
                document.getElementById('file-modal').classList.remove('hidden');
            }
        } catch (error) {
            console.error('Error opening file:', error);
        }
    },

    async deleteFile(path) {
        const isFolder = document.querySelector(`[data-path="${path}"]`)?.classList.contains('tree-item-folder');
        const type = isFolder ? 'carpeta' : 'archivo';
        
        if (!confirm(`Eliminar ${type}: ${path}?`)) return;
        
        try {
            const response = await fetch('/api/files/delete', {
                method: 'POST',
                headers: this.getApiHeaders(),
                body: JSON.stringify({ path: path, confirm: true })
            });
            
            const data = await response.json();
            
            if (this.handleApiError(response, data)) return;
            
            if (data.success) {
                this.addMessage(`${type.charAt(0).toUpperCase() + type.slice(1)} eliminado: ${path}`, 'assistant');
                this.loadFiles();
                document.getElementById('file-modal').classList.add('hidden');
            }
        } catch (error) {
            this.addMessage('Error de conexion al eliminar', 'assistant');
        }
    },

    async renameFile(oldPath) {
        const oldName = oldPath.split('/').pop();
        const newName = prompt('Nuevo nombre:', oldName);
        if (!newName || newName === oldName) return;
        
        const pathParts = oldPath.split('/');
        pathParts.pop();
        const newPath = pathParts.length > 0 ? pathParts.join('/') + '/' + newName : newName;
        
        try {
            const response = await fetch('/api/files/rename', {
                method: 'POST',
                headers: this.getApiHeaders(),
                body: JSON.stringify({ old_path: oldPath, new_path: newPath })
            });
            
            const data = await response.json();
            
            if (this.handleApiError(response, data)) return;
            
            if (data.success) {
                this.addMessage(`Renombrado: ${oldPath} -> ${newPath}`, 'assistant');
                this.loadFiles();
            }
        } catch (error) {
            this.addMessage('Error de conexion al renombrar', 'assistant');
        }
    },

    async duplicateFile(path) {
        try {
            const response = await fetch('/api/files/duplicate', {
                method: 'POST',
                headers: this.getApiHeaders(),
                body: JSON.stringify({ path: path })
            });
            
            const data = await response.json();
            
            if (this.handleApiError(response, data)) return;
            
            if (data.success) {
                this.addMessage(`Archivo duplicado: ${data.copy}`, 'assistant');
                this.loadFiles();
            }
        } catch (error) {
            this.addMessage('Error de conexion al duplicar', 'assistant');
        }
    },

    showContextMenu(event, item) {
        event.preventDefault();
        event.stopPropagation();
        
        this.hideContextMenu();
        
        const menu = document.createElement('div');
        menu.className = 'context-menu';
        menu.id = 'file-context-menu';
        
        const isFolder = item.type === 'folder';
        
        menu.innerHTML = `
            ${!isFolder ? `<div class="context-menu-item" data-action="open"><span class="menu-icon">📂</span> Abrir</div>` : ''}
            <div class="context-menu-item" data-action="rename"><span class="menu-icon">✏️</span> Renombrar</div>
            ${!isFolder ? `<div class="context-menu-item" data-action="duplicate"><span class="menu-icon">📋</span> Duplicar</div>` : ''}
            <div class="context-menu-divider"></div>
            <div class="context-menu-item context-menu-danger" data-action="delete"><span class="menu-icon">🗑️</span> Eliminar</div>
        `;
        
        document.body.appendChild(menu);
        
        const x = Math.min(event.clientX, window.innerWidth - menu.offsetWidth - 10);
        const y = Math.min(event.clientY, window.innerHeight - menu.offsetHeight - 10);
        menu.style.left = x + 'px';
        menu.style.top = y + 'px';
        
        menu.querySelectorAll('.context-menu-item').forEach(menuItem => {
            menuItem.addEventListener('click', () => {
                const action = menuItem.dataset.action;
                switch (action) {
                    case 'open':
                        this.openFile(item);
                        break;
                    case 'rename':
                        this.renameFile(item.path);
                        break;
                    case 'duplicate':
                        this.duplicateFile(item.path);
                        break;
                    case 'delete':
                        this.deleteFile(item.path);
                        break;
                }
                this.hideContextMenu();
            });
        });
        
        document.addEventListener('click', () => this.hideContextMenu(), { once: true });
    },

    hideContextMenu() {
        const existing = document.getElementById('file-context-menu');
        if (existing) existing.remove();
    },

    async showDiffViewer(path, newContent) {
        try {
            const response = await fetch('/api/files/diff', {
                method: 'POST',
                headers: this.getApiHeaders(),
                body: JSON.stringify({ path: path, new_content: newContent })
            });
            
            const data = await response.json();
            
            if (!data.success) {
                this.addMessage(`Error generando diff: ${data.error}`, 'assistant');
                return;
            }
            
            const modal = document.createElement('div');
            modal.id = 'diff-viewer-modal';
            modal.className = 'modal-overlay';
            
            const formattedDiff = this.formatDiffOutput(data.diff);
            
            modal.innerHTML = `
                <div class="diff-viewer-container">
                    <div class="diff-header">
                        <div class="diff-title">
                            <span class="diff-icon">📝</span>
                            <span>${data.is_new ? 'Nuevo archivo' : 'Cambios en'}: ${path}</span>
                        </div>
                        <div class="diff-stats">
                            <span class="diff-stat diff-additions">+${data.stats.additions}</span>
                            <span class="diff-stat diff-deletions">-${data.stats.deletions}</span>
                        </div>
                    </div>
                    <div class="diff-content">
                        <pre class="diff-code">${formattedDiff}</pre>
                    </div>
                    <div class="diff-actions">
                        <button class="diff-btn diff-btn-apply" id="apply-diff-btn">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="20 6 9 17 4 12"></polyline>
                            </svg>
                            Aplicar cambios
                        </button>
                        <button class="diff-btn diff-btn-cancel" id="cancel-diff-btn">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                            Cancelar
                        </button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            document.getElementById('apply-diff-btn').addEventListener('click', async () => {
                await this.applyDiff(path, newContent);
                modal.remove();
            });
            
            document.getElementById('cancel-diff-btn').addEventListener('click', () => {
                modal.remove();
            });
            
            modal.addEventListener('click', (e) => {
                if (e.target === modal) modal.remove();
            });
            
        } catch (error) {
            console.error('Error showing diff:', error);
            this.addMessage('Error mostrando diferencias', 'assistant');
        }
    },
    
    formatDiffOutput(diffText) {
        if (!diffText) return '<span class="diff-empty">No hay cambios</span>';
        
        return diffText.split('\n').map(line => {
            let className = 'diff-line';
            if (line.startsWith('+')) {
                className += ' diff-line-add';
            } else if (line.startsWith('-')) {
                className += ' diff-line-remove';
            } else if (line.startsWith('@@')) {
                className += ' diff-line-info';
            }
            return `<span class="${className}">${this.escapeHtml(line)}</span>`;
        }).join('\n');
    },
    
    async applyDiff(path, newContent) {
        try {
            const response = await fetch('/api/files/apply-diff', {
                method: 'POST',
                headers: this.getApiHeaders(),
                body: JSON.stringify({ path: path, new_content: newContent, confirmed: true })
            });
            
            const data = await response.json();
            
            if (this.handleApiError(response, data)) return;
            
            if (data.success) {
                this.addMessage(`Cambios aplicados: ${path}`, 'assistant');
                this.loadFiles();
            }
        } catch (error) {
            this.addMessage('Error de conexion al aplicar cambios', 'assistant');
        }
    },

    setMentalState(state, emoji) {
        this.state.mentalState = state;
        document.querySelector('.mental-state .state-emoji').textContent = emoji;
        document.querySelector('.mental-state .state-text').textContent = state;

        const indicator = document.getElementById('status-indicator');
        indicator.className = 'status-indicator ' + (state === 'PROCESANDO' ? 'working' : 'online');
    },

    updateTime() {
        const now = new Date();
        document.getElementById('current-time').textContent = now.toLocaleTimeString('es-ES', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }
};

document.addEventListener('DOMContentLoaded', () => Workspace.init());
