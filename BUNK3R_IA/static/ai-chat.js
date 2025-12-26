const AIChat = {
    isOpen: false,
    messages: [],
    isLoading: false,
    isPageMode: false,
    files: {},
    activeTab: 'preview',
    currentSession: null,
    currentPhase: 0,
    esperandoConfirmacion: false,
    esperandoClarificacion: false,
    
    devLog(...args) {
        if (window.App?.isDevMode || window.App?.isDemoMode) {
            console.log('[AI-DEV]', ...args);
        }
    },
    
    async loadProjectFiles(projectId) {
        const listContainer = document.getElementById('ai-projects-list');
        if (!listContainer) return;

        try {
            const response = await fetch(`/api/projects/${projectId}/files`);
            const data = await response.json();
            
            if (data.files) {
                listContainer.innerHTML = '';
                this.renderFileStructure(data.files, listContainer);
            }
        } catch (e) {
            listContainer.innerHTML = '<div class="error">Error al cargar archivos</div>';
        }
    },

    renderFileStructure(files, container, level = 0) {
        files.forEach(file => {
            const item = document.createElement('div');
            item.className = 'file-item';
            item.style.paddingLeft = `${level * 15 + 10}px`;
            item.style.cursor = 'pointer';
            item.style.color = '#c9d1d9';
            item.style.fontSize = '13px';
            item.style.padding = '4px 10px';
            
            if (file.type === 'folder') {
                item.innerHTML = `📁 ${file.name}`;
                container.appendChild(item);
                if (file.children) {
                    this.renderFileStructure(file.children, container, level + 1);
                }
            } else {
                item.innerHTML = `📄 ${file.name}`;
                item.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.openFile(file.path, file.name);
                });
                container.appendChild(item);
            }
        });
    },

    openTabs: [
        { id: 'console', name: 'Terminal', type: 'console' },
        { id: 'preview', name: 'Preview', type: 'preview' }
    ],
    activeTabId: 'preview',

    renderTabs() {
        const container = document.getElementById('ai-tabs-container');
        if (!container) return;
        container.innerHTML = '';
        
        this.openTabs.forEach(tab => {
            const tabEl = document.createElement('div');
            tabEl.className = `ai-tab-item ${this.activeTabId === tab.id ? 'active' : ''}`;
            
            // Estilos CSS vía clases, evitando inline style excesivo
            tabEl.innerHTML = `<span>${tab.name}</span>`;
            
            if (tab.type === 'file') {
                const closeBtn = document.createElement('span');
                closeBtn.innerHTML = '×';
                closeBtn.className = 'tab-close-btn';
                closeBtn.onclick = (e) => {
                    e.stopPropagation();
                    this.closeTab(tab.id);
                };
                tabEl.appendChild(closeBtn);
            }
            
            tabEl.onclick = (e) => {
                e.preventDefault();
                console.log('Tab clicked:', tab.id);
                this.switchTab(tab.id);
            };
            
            container.appendChild(tabEl);
        });
    },

    switchTab(tabId) {
        console.log('[DEBUG] switchTab called for tabId:', tabId);
        this.activeTabId = tabId;
        this.renderTabs();
        
        const panels = {
            'console': document.getElementById('ai-console'),
            'editor': document.getElementById('editor-wrapper'),
            'preview': document.getElementById('ai-preview-panel'),
            'empty': document.querySelector('.ai-empty-state'),
            'toolbar': document.getElementById('editor-toolbar')
        };

        console.log('[DEBUG] Panels found in DOM:', Object.keys(panels).map(k => `${k}: ${!!panels[k]}`));

        // LIMPIEZA TOTAL: Ocultar todo y remover visibilidad
        Object.keys(panels).forEach(key => {
            const panel = panels[key];
            if (panel) {
                panel.style.setProperty('display', 'none', 'important');
                panel.style.setProperty('visibility', 'hidden', 'important');
                panel.style.setProperty('opacity', '0', 'important');
                panel.classList.add('hidden-panel');
            }
        });

        // MOSTRAR PANEL ESPECÍFICO
        if (tabId === 'console') {
            console.log('[DEBUG] Activating console panel');
            if (panels.console) {
                panels.console.style.setProperty('display', 'flex', 'important');
                panels.console.style.setProperty('visibility', 'visible', 'important');
                panels.console.style.setProperty('opacity', '1', 'important');
                panels.console.classList.remove('hidden-panel');
                const input = document.getElementById('ai-console-input');
                if (input) input.focus();
            }
        } else if (tabId === 'preview') {
            console.log('[DEBUG] Activating preview panel');
            if (panels.preview) {
                panels.preview.style.setProperty('display', 'block', 'important');
                panels.preview.style.setProperty('visibility', 'visible', 'important');
                panels.preview.style.setProperty('opacity', '1', 'important');
                panels.preview.classList.remove('hidden-panel');
            }
        } else if (tabId.startsWith('file-')) {
            const tab = this.openTabs.find(t => t.id === tabId);
            console.log('[DEBUG] File tab data found:', !!tab);
            
            if (tab && panels.editor) {
                console.log('[DEBUG] Rendering Editor for:', tab.path);
                
                // ASEGURAR que el estado vacío se oculte PRIMERO
                if (panels.empty) {
                    panels.empty.style.setProperty('display', 'none', 'important');
                    panels.empty.style.setProperty('visibility', 'hidden', 'important');
                    panels.empty.classList.add('hidden-panel');
                }

                // Activar editor wrapper con Z-INDEX ALTO
                panels.editor.style.setProperty('display', 'flex', 'important');
                panels.editor.style.setProperty('visibility', 'visible', 'important');
                panels.editor.style.setProperty('opacity', '1', 'important');
                panels.editor.style.setProperty('z-index', '100', 'important');
                panels.editor.classList.remove('hidden-panel');
                
                // Activar toolbar
                if (panels.toolbar) {
                    panels.toolbar.style.setProperty('display', 'flex', 'important');
                    panels.toolbar.style.setProperty('visibility', 'visible', 'important');
                    panels.toolbar.style.setProperty('opacity', '1', 'important');
                    panels.toolbar.classList.remove('hidden-panel');
                }
                
                // Setear contenido
                const editor = document.getElementById('ai-real-editor');
                if (editor) {
                    console.log('[DEBUG] Setting editor value. Content length:', tab.content ? tab.content.length : 0);
                    editor.value = tab.content || '';
                    window.currentEditingFile = tab.path;
                    // Forzar reflow para asegurar que el contenido se renderice
                    editor.scrollTop = 0;
                } else {
                    console.error('[DEBUG] #ai-real-editor NOT FOUND in DOM');
                }
            } else {
                console.error('[DEBUG] Tab data or editor panel MISSING for file tab');
            }
        } else {
            console.log('[DEBUG] Showing empty state');
            if (panels.empty) {
                panels.empty.style.setProperty('display', 'flex', 'important');
                panels.empty.style.setProperty('visibility', 'visible', 'important');
                panels.empty.style.setProperty('opacity', '1', 'important');
                panels.empty.classList.remove('hidden-panel');
            }
        }
    },

    closeTab(tabId) {
        const index = this.openTabs.findIndex(t => t.id === tabId);
        if (index !== -1) {
            this.openTabs.splice(index, 1);
            if (this.activeTabId === tabId) {
                this.activeTabId = this.openTabs[index - 1]?.id || this.openTabs[0]?.id;
            }
            this.renderTabs();
            this.switchTab(this.activeTabId);
        }
    },

    async openFile(path, name) {
        console.log('[DEBUG] openFile called with path:', path, 'name:', name);
        
        // Normalización: si la ruta empieza con ./ o BUNK3R-W3B/, limpiarla para el ID de pestaña
        let cleanIdPath = path;
        if (path.startsWith('./')) cleanIdPath = path.substring(2);
        
        const tabId = `file-${cleanIdPath}`;
        console.log('[DEBUG] Generated tabId:', tabId);
        
        const existingTab = this.openTabs.find(t => t.id === tabId);
        if (existingTab) {
            console.log('[DEBUG] Tab already exists, switching to it');
            this.switchTab(tabId);
            return;
        }

        console.log('[DEBUG] Loading file content from API for path:', path);
        try {
            const url = `/api/projects/file/content?path=${encodeURIComponent(path)}`;
            console.log('[DEBUG] Fetch URL:', url);
            
            const response = await fetch(url);
            console.log('[DEBUG] API Response status:', response.status);
            
            const data = await response.json();
            console.log('[DEBUG] API Data received:', data);
            
            if (data.success) {
                console.log('[DEBUG] File content loaded successfully. Length:', data.content ? data.content.length : 0);
                const newTab = {
                    id: tabId,
                    name: name || path.split('/').pop(),
                    type: 'file',
                    path: path,
                    content: data.content
                };
                this.openTabs.push(newTab);
                this.activeTabId = tabId;
                
                console.log('[DEBUG] New tab added to openTabs. Total tabs:', this.openTabs.length);
                this.renderTabs();
                this.switchTab(tabId);
            } else {
                console.error('[DEBUG] API Error:', data.error);
                alert('Error al cargar archivo: ' + data.error);
            }
        } catch (e) {
            console.error('[DEBUG] Fetch Exception:', e);
        }
    },
            
            if (data.success) {
                console.log('File content loaded successfully');
                const newTab = {
                    id: tabId,
                    name: name || path.split('/').pop(),
                    type: 'file',
                    path: path,
                    content: data.content
                };
                this.openTabs.push(newTab);
                this.activeTabId = tabId;
                
                // Forzar el renderizado y el cambio de pestaña con el contenido cargado
                this.renderTabs();
                this.switchTab(tabId);
            } else {
                console.error('Error loading file content:', data.error);
                alert('Error: ' + data.error);
            }
        } catch (e) {
            console.error('Fetch error during openFile:', e);
        }
    },

    async saveCurrentFile() {
        if (!window.currentEditingFile) return;
        const editor = document.getElementById('ai-real-editor');
        if (!editor) return;
        const content = editor.value;

        try {
            const response = await fetch('/api/projects/file/content', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    path: window.currentEditingFile,
                    content: content
                })
            });
            const data = await response.json();
            if (data.success) {
                alert('Archivo guardado correctamente');
            } else {
                alert('Error: ' + data.error);
            }
        } catch (e) {
            alert('Error al guardar');
        }
    },

    init() {
        const pageContainer = document.getElementById('ai-chat-screen');
        if (pageContainer && !pageContainer.classList.contains('hidden')) {
            this.isPageMode = true;
            this.initPageMode();
        } else {
            this.isPageMode = false;
            this.initWidgetMode();
        }
        this.loadFromStorage();
        this.loadSession();
    },
    
    initPageMode() {
        const input = document.getElementById('ai-chat-input');
        const send = document.getElementById('ai-chat-send');
        
        if (!input || !send) return;
        
        input.removeEventListener('input', this.handleInputChange);
        input.removeEventListener('keydown', this.handleKeyDown);
        send.removeEventListener('click', this.handleSendClick);
        
        this.handleInputChange = () => {
            send.disabled = !input.value.trim();
            this.autoResize(input);
        };
        
        this.handleKeyDown = (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendCodeRequest();
            }
        };
        
        this.handleSendClick = () => this.sendCodeRequest();
        
        input.addEventListener('input', this.handleInputChange);
        input.addEventListener('keydown', this.handleKeyDown);
        send.addEventListener('click', this.handleSendClick);
        
        this.bindQuickActions();
        this.bindFileTabs();
        this.bindRefreshButton();
        this.bindCodeEditor();
        this.bindConsole();
        this.bindSidebarToggle();
        
        // CORRECCIÓN: Asegurar que el estado inicial cargue correctamente las pestañas y el panel
        setTimeout(() => {
            this.renderTabs();
            this.switchTab('preview');
        }, 100);
        
        // Configurar el botón de guardar si no se ha hecho
        const saveBtn = document.getElementById('btn-save-file');
        if (saveBtn) {
            saveBtn.onclick = () => AIChat.saveCurrentFile();
        }
        
        input.focus();
    },
    
    consoleHistory: [],
    consoleHistoryIndex: -1,
    
    bindConsole() {
        const consoleInput = document.getElementById('ai-console-input');
        if (!consoleInput) return;
        
        consoleInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const command = consoleInput.value.trim();
                if (command) {
                    this.runConsoleCommand(command);
                    consoleInput.value = '';
                }
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (this.consoleHistoryIndex < this.consoleHistory.length - 1) {
                    this.consoleHistoryIndex++;
                    consoleInput.value = this.consoleHistory[this.consoleHistory.length - 1 - this.consoleHistoryIndex];
                }
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (this.consoleHistoryIndex > 0) {
                    this.consoleHistoryIndex--;
                    consoleInput.value = this.consoleHistory[this.consoleHistory.length - 1 - this.consoleHistoryIndex];
                } else {
                    this.consoleHistoryIndex = -1;
                    consoleInput.value = '';
                }
            }
        });
    },
    
    async runConsoleCommand(command) {
        const output = document.getElementById('ai-console-output');
        if (!output) return;
        
        this.consoleHistory.push(command);
        this.consoleHistoryIndex = -1;
        
        const cmdLine = document.createElement('div');
        cmdLine.className = 'console-line command';
        cmdLine.innerHTML = `<span class="console-prompt-display">$</span>${this.escapeHtml(command)}`;
        output.appendChild(cmdLine);
        
        const loadingLine = document.createElement('div');
        loadingLine.className = 'console-loading';
        loadingLine.textContent = 'Ejecutando...';
        output.appendChild(loadingLine);
        output.scrollTop = output.scrollHeight;
        
        try {
            const headers = App.getAuthHeaders ? App.getAuthHeaders() : { 'Content-Type': 'application/json' };
            
            const response = await fetch('/api/projects/command/run', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ command, timeout: 30 })
            });
            
            const data = await response.json();
            loadingLine.remove();
            
            if (data.success) {
                if (data.stdout) {
                    const outLine = document.createElement('div');
                    outLine.className = 'console-line output';
                    outLine.textContent = data.stdout;
                    output.appendChild(outLine);
                }
                if (data.stderr) {
                    const errLine = document.createElement('div');
                    errLine.className = 'console-line error';
                    errLine.textContent = data.stderr;
                    output.appendChild(errLine);
                }
                if (!data.stdout && !data.stderr) {
                    const okLine = document.createElement('div');
                    okLine.className = 'console-line success';
                    okLine.textContent = 'Comando ejecutado correctamente';
                    output.appendChild(okLine);
                }
            } else {
                const errLine = document.createElement('div');
                errLine.className = 'console-line error';
                errLine.textContent = data.error || 'Error al ejecutar comando';
                output.appendChild(errLine);
            }
        } catch (error) {
            loadingLine.remove();
            const errLine = document.createElement('div');
            errLine.className = 'console-line error';
            errLine.textContent = `Error: ${error.message}`;
            output.appendChild(errLine);
        }
        
        output.scrollTop = output.scrollHeight;
    },
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    
    bindQuickActions() {
        document.querySelectorAll('.ai-quick-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const prompt = btn.dataset.prompt;
                if (prompt) {
                    document.getElementById('ai-chat-input').value = prompt;
                    this.sendCodeRequest();
                }
            });
        });

        // Activar botones de la barra lateral (Landing Page, Dashboard, etc)
        document.querySelectorAll('.ai-quick-btn-sidebar').forEach(btn => {
            btn.addEventListener('click', () => {
                const prompt = btn.dataset.prompt;
                if (prompt) {
                    const input = document.getElementById('ai-chat-input');
                    if (input) {
                        input.value = prompt;
                        // Forzar el redimensionamiento del textarea si existe la lógica
                        input.dispatchEvent(new Event('input')); 
                        this.sendCodeRequest();
                    }
                }
            });
        });
    },
    
    bindFileTabs() {
        document.querySelectorAll('.ai-file-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                this.switchTab(tab.dataset.file);
            });
        });
    },
    
    bindRefreshButton() {
        const refreshBtn = document.getElementById('ai-preview-refresh');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.updatePreview();
            });
        }
    },
    
    bindCodeEditor() {
        const textarea = document.getElementById('ai-code-textarea');
        if (textarea) {
            textarea.addEventListener('input', () => {
                if (this.activeTab !== 'preview') {
                    const fileMap = { html: 'index.html', css: 'styles.css', js: 'script.js' };
                    const filename = fileMap[this.activeTab];
                    if (filename) {
                        this.files[filename] = textarea.value;
                        this.saveToStorage();
                        this.updatePreview();
                    }
                }
            });
            
            textarea.addEventListener('keydown', (e) => {
                if (e.key === 'Tab') {
                    e.preventDefault();
                    const start = textarea.selectionStart;
                    const end = textarea.selectionEnd;
                    textarea.value = textarea.value.substring(0, start) + '  ' + textarea.value.substring(end);
                    textarea.selectionStart = textarea.selectionEnd = start + 2;
                }
            });
        }
    },
    
    switchTab(tabName) {
        this.activeTab = tabName;
        
        document.querySelectorAll('.ai-file-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.file === tabName);
        });
        
        const iframe = document.getElementById('ai-preview-iframe');
        const codeEditor = document.getElementById('ai-code-editor');
        const emptyState = document.getElementById('ai-preview-empty');
        const textarea = document.getElementById('ai-code-textarea');
        const consolePanel = document.getElementById('ai-console');
        
        if (consolePanel) consolePanel.classList.add('hidden');
        if (codeEditor) codeEditor.classList.add('hidden');
        if (iframe) iframe.classList.add('hidden');
        if (emptyState) emptyState.classList.add('hidden');
        
        if (tabName === 'preview') {
            const hasFiles = Object.keys(this.files).length > 0;
            if (hasFiles) {
                if (iframe) iframe.classList.remove('hidden');
            } else {
                if (emptyState) emptyState.classList.remove('hidden');
            }
            this.updatePreview();
        } else if (tabName === 'console') {
            if (consolePanel) {
                consolePanel.classList.remove('hidden');
                const consoleInput = document.getElementById('ai-console-input');
                if (consoleInput) consoleInput.focus();
            }
        } else {
            if (codeEditor) codeEditor.classList.remove('hidden');
            
            const fileMap = { html: 'index.html', css: 'styles.css', js: 'script.js' };
            const filename = fileMap[tabName];
            if (textarea && filename && this.files[filename]) {
                textarea.value = this.files[filename];
            } else if (textarea) {
                textarea.value = '';
            }
        }
    },
    
    initWidgetMode() {
        return;
    },
    
    createChatWidget() {
        return;
    },
    
    bindWidgetEvents() {
        return;
    },
    
    bindSidebarToggle() {
        // Selector más robusto que no dependa solo del ID si hay duplicados o problemas de carga
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('#toggle-sidebar-btn');
            if (!btn) return;
            
            console.log('SIDEBAR TOGGLE CLICK DETECTED');
            e.preventDefault();
            e.stopPropagation();
            
            const panel = document.getElementById('panel-projects');
            if (!panel) {
                console.error('Panel projects not found');
                return;
            }

            // Cambiar estado
            const isHidden = panel.style.display === 'none' || panel.classList.contains('hidden');
            
            if (isHidden) {
                panel.style.display = 'flex';
                panel.classList.remove('hidden');
                btn.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"></polyline></svg>';
            } else {
                panel.style.display = 'none';
                panel.classList.add('hidden');
                btn.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"></polyline></svg>';
            }
        });
    },

    autoResize(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    },
    
    toggle() {
        this.isOpen = !this.isOpen;
        const container = document.getElementById('ai-chat-container-widget');
        const toggle = document.getElementById('ai-chat-toggle');
        
        if (this.isOpen) {
            if (container) container.classList.remove('hidden');
            if (toggle) toggle.classList.add('active');
        } else {
            if (container) container.classList.add('hidden');
            if (toggle) toggle.classList.remove('active');
        }
    },
    
    close() {
        this.isOpen = false;
        const container = document.getElementById('ai-chat-container-widget');
        const toggle = document.getElementById('ai-chat-toggle');
        if (container) container.classList.add('hidden');
        if (toggle) toggle.classList.remove('active');
    },
    
    getMessagesContainer() {
        return document.getElementById('ai-chat-messages');
    },
    
    getInput() {
        return document.getElementById('ai-chat-input');
    },
    
    getSendButton() {
        return document.getElementById('ai-chat-send');
    },
    
    getProviderIndicator() {
        return document.getElementById('ai-provider-info');
    },
    
    getApiHeaders() {
        return { 'Content-Type': 'application/json' };
    },
    
    loadFromStorage() {
        try {
            const saved = localStorage.getItem('bunkr_ai_project');
            if (saved) {
                const data = JSON.parse(saved);
                this.files = data.files || {};
                if (Object.keys(this.files).length > 0) {
                    this.updatePreview();
                }
            }
        } catch (e) {
            console.error('Error loading project:', e);
        }
    },
    
    saveToStorage() {
        try {
            localStorage.setItem('bunkr_ai_project', JSON.stringify({
                files: this.files,
                savedAt: new Date().toISOString()
            }));
        } catch (e) {
            console.error('Error saving project:', e);
        }
    },
    
    async loadSession() {
        try {
            const response = await fetch('/api/ai-constructor/session', {
                method: 'GET',
                headers: this.getApiHeaders()
            });
            
            const data = await response.json();
            
            if (data.success && data.hasSession) {
                this.currentSession = data.session;
                this.currentPhase = data.session.fase_actual || 0;
                this.esperandoConfirmacion = data.session.esperando_confirmacion || false;
                this.esperandoClarificacion = data.session.esperando_clarificacion || false;
                this.updatePhaseIndicator();
            }
        } catch (e) {
            this.devLog('No active session');
        }
    },
    
    appendMessage(role, content, save = true) {
        const container = this.getMessagesContainer();
        if (!container) return;
        
        const welcomeMsg = container.querySelector('.ai-chat-welcome');
        if (welcomeMsg) welcomeMsg.style.display = 'none';
        
        const msgDiv = document.createElement('div');
        msgDiv.className = `ai-message ai-message-${role}`;
        
        if (role === 'assistant') {
            msgDiv.innerHTML = `
                <div class="ai-avatar">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="20" height="20">
                        <path d="M12 2a4 4 0 0 1 4 4v1h1a3 3 0 0 1 3 3v2a3 3 0 0 1-3 3h-1v1a4 4 0 0 1-8 0v-1H7a3 3 0 0 1-3-3v-2a3 3 0 0 1 3-3h1V6a4 4 0 0 1 4-4z"></path>
                    </svg>
                </div>
                <div class="ai-bubble">${this.formatMessage(content)}</div>
            `;
        } else {
            msgDiv.innerHTML = `
                <div class="ai-bubble">${this.escapeHtml(content)}</div>
            `;
        }
        
        container.appendChild(msgDiv);
        container.scrollTop = container.scrollHeight;
        
        if (save) {
            this.messages.push({ role, content });
        }
    },
    
    appendPhaseIndicator(phase, phaseName, isActive = true) {
        const container = this.getMessagesContainer();
        if (!container) return;
        
        const phaseDiv = document.createElement('div');
        phaseDiv.className = `ai-phase-indicator ${isActive ? 'active' : 'completed'}`;
        phaseDiv.id = `phase-indicator-${phase}`;
        
        const phaseIcons = {
            1: '1',
            2: '2',
            3: '3',
            4: '4',
            5: '5',
            6: '6',
            7: '7',
            8: '8'
        };
        
        phaseDiv.innerHTML = `
            <div class="phase-badge">
                <span class="phase-number">${phaseIcons[phase] || phase}</span>
            </div>
            <div class="phase-info">
                <span class="phase-name">${this.escapeHtml(phaseName)}</span>
                <span class="phase-status">${isActive ? 'En progreso...' : 'Completada'}</span>
            </div>
        `;
        
        container.appendChild(phaseDiv);
        container.scrollTop = container.scrollHeight;
    },
    
    updatePhaseIndicator() {
        const existingIndicator = document.getElementById(`phase-indicator-${this.currentPhase}`);
        if (existingIndicator) {
            existingIndicator.classList.remove('active');
            existingIndicator.classList.add('completed');
            const statusEl = existingIndicator.querySelector('.phase-status');
            if (statusEl) statusEl.textContent = 'Completada';
        }
    },
    
    appendConfirmationButtons(plan) {
        const container = this.getMessagesContainer();
        if (!container) return;
        
        const buttonsDiv = document.createElement('div');
        buttonsDiv.className = 'ai-confirmation-buttons';
        buttonsDiv.id = 'ai-plan-confirmation';
        
        buttonsDiv.innerHTML = `
            <div class="ai-plan-actions">
                <button class="ai-btn ai-btn-confirm" id="ai-confirm-plan">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    Continuar con el plan
                </button>
                <button class="ai-btn ai-btn-cancel" id="ai-cancel-plan">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                    Ajustar plan
                </button>
            </div>
        `;
        
        container.appendChild(buttonsDiv);
        container.scrollTop = container.scrollHeight;
        
        document.getElementById('ai-confirm-plan').addEventListener('click', () => {
            this.respondToConfirmation(true);
        });
        
        document.getElementById('ai-cancel-plan').addEventListener('click', () => {
            this.respondToConfirmation(false);
        });
    },
    
    removeConfirmationButtons() {
        const buttons = document.getElementById('ai-plan-confirmation');
        if (buttons) buttons.remove();
    },
    
    async respondToConfirmation(confirmed) {
        this.removeConfirmationButtons();
        const message = confirmed ? 'Si, continuar' : 'No, quiero ajustar';
        this.appendMessage('user', message);
        
        await this.sendConstructorMessage(message);
    },
    
    appendCodeAction(action, filename) {
        const container = this.getMessagesContainer();
        if (!container) return;
        
        const actionDiv = document.createElement('div');
        actionDiv.className = `ai-code-action ${action === 'update' ? 'update' : ''}`;
        
        const icon = action === 'create' ? 
            '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>' :
            '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>';
        
        actionDiv.innerHTML = `
            ${icon}
            <span class="ai-code-action-text">${action === 'create' ? 'Archivo creado' : 'Archivo actualizado'}</span>
            <span class="ai-code-action-file">${this.escapeHtml(filename)}</span>
        `;
        
        container.appendChild(actionDiv);
        container.scrollTop = container.scrollHeight;
    },
    
    formatMessage(text) {
        let formatted = this.escapeHtml(text);
        formatted = formatted.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
        formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
        formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        formatted = formatted.replace(/\n/g, '<br>');
        return formatted;
    },
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    
    showTyping() {
        const container = this.getMessagesContainer();
        if (!container) return;
        
        const typing = document.createElement('div');
        typing.className = 'ai-message ai-message-assistant ai-typing';
        typing.id = 'ai-typing-indicator';
        typing.innerHTML = `
            <div class="ai-avatar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="20" height="20">
                    <path d="M12 2a4 4 0 0 1 4 4v1h1a3 3 0 0 1 3 3v2a3 3 0 0 1-3 3h-1v1a4 4 0 0 1-8 0v-1H7a3 3 0 0 1-3-3v-2a3 3 0 0 1 3-3h1V6a4 4 0 0 1 4-4z"></path>
                </svg>
            </div>
            <div class="ai-bubble">
                <div class="ai-typing-dots">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        container.appendChild(typing);
        container.scrollTop = container.scrollHeight;
    },
    
    showPhaseProgress(phase, phaseName) {
        const container = this.getMessagesContainer();
        if (!container) return;
        
        let progressDiv = document.getElementById('ai-phase-progress');
        if (!progressDiv) {
            progressDiv = document.createElement('div');
            progressDiv.className = 'ai-phase-progress';
            progressDiv.id = 'ai-phase-progress';
            container.appendChild(progressDiv);
        }
        
        progressDiv.innerHTML = `
            <div class="phase-progress-content">
                <div class="phase-spinner"></div>
                <span class="phase-text">Fase ${phase}: ${this.escapeHtml(phaseName)}</span>
            </div>
        `;
        
        container.scrollTop = container.scrollHeight;
    },
    
    hidePhaseProgress() {
        const progress = document.getElementById('ai-phase-progress');
        if (progress) progress.remove();
    },
    
    hideTyping() {
        const typing = document.getElementById('ai-typing-indicator');
        if (typing) typing.remove();
    },
    
    updatePreview() {
        const iframe = document.getElementById('ai-preview-iframe');
        const emptyState = document.getElementById('ai-preview-empty');
        
        if (!iframe) {
            console.warn('AIChat: iframe not found');
            return;
        }
        
        let html = this.files['index.html'] || this.files['html'] || '';
        let css = this.files['styles.css'] || this.files['style.css'] || this.files['css'] || '';
        let js = this.files['script.js'] || this.files['main.js'] || this.files['app.js'] || this.files['js'] || '';
        
        this.devLog('AIChat updatePreview - files:', Object.keys(this.files), 'html:', !!html, 'css:', !!css, 'js:', !!js);
        
        if (!html && !css && !js) {
            if (emptyState) emptyState.classList.remove('hidden');
            iframe.classList.add('hidden');
            return;
        }
        
        if (emptyState) emptyState.classList.add('hidden');
        iframe.classList.remove('hidden');
        
        let processedHtml = html;
        
        if (!processedHtml && (css || js)) {
            processedHtml = `<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Preview</title>
    ${css ? `<style>${css}</style>` : ''}
</head>
<body>
    ${js ? `<script>${js}<\/script>` : ''}
</body>
</html>`;
        } else {
            if (processedHtml.includes('<link rel="stylesheet" href="styles.css">')) {
                processedHtml = processedHtml.replace(
                    '<link rel="stylesheet" href="styles.css">',
                    `<style>${css}</style>`
                );
            } else if (processedHtml.includes('<link rel="stylesheet" href="style.css">')) {
                processedHtml = processedHtml.replace(
                    '<link rel="stylesheet" href="style.css">',
                    `<style>${css}</style>`
                );
            } else if (css && !processedHtml.includes('<style>')) {
                if (processedHtml.includes('</head>')) {
                    processedHtml = processedHtml.replace('</head>', `<style>${css}</style></head>`);
                } else {
                    processedHtml = `<style>${css}</style>` + processedHtml;
                }
            }
            
            const scriptPatterns = [
                '<script src="script.js"></script>',
                '<script src="main.js"></script>',
                '<script src="app.js"></script>'
            ];
            let scriptReplaced = false;
            for (const pattern of scriptPatterns) {
                if (processedHtml.includes(pattern)) {
                    processedHtml = processedHtml.replace(pattern, `<script>${js}<\/script>`);
                    scriptReplaced = true;
                    break;
                }
            }
            if (js && !scriptReplaced && !processedHtml.includes('<script>')) {
                if (processedHtml.includes('</body>')) {
                    processedHtml = processedHtml.replace('</body>', `<script>${js}<\/script></body>`);
                } else {
                    processedHtml = processedHtml + `<script>${js}<\/script>`;
                }
            }
        }
        
        this.devLog('AIChat updatePreview - setting srcdoc, length:', processedHtml.length);
        iframe.srcdoc = processedHtml;
    },
    
    async sendCodeRequest() {
        const input = this.getInput();
        const send = this.getSendButton();
        
        if (!input) return;
        
        const message = input.value.trim();
        
        if (!message || this.isLoading) return;
        
        this.isLoading = true;
        input.value = '';
        input.style.height = 'auto';
        if (send) send.disabled = true;
        
        this.appendMessage('user', message);
        
        const isCodeRequest = this.isCodeGenerationRequest(message);
        
        if (isCodeRequest) {
            await this.sendConstructorMessage(message);
        } else {
            await this.sendSimpleChat(message);
        }
    },
    
    async sendSimpleChat(message) {
        this.showTyping();
        try {
            const response = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: this.getApiHeaders(),
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            this.hideTyping();
            
            if (data.success) {
                this.appendMessage('assistant', data.response || data.message || 'Respuesta recibida');
            } else {
                this.appendMessage('assistant', data.error || 'Error al procesar. Intenta de nuevo.');
            }
        } catch (error) {
            this.hideTyping();
            this.appendMessage('assistant', 'Error de conexion. Verifica tu internet e intenta de nuevo.');
            console.error('Chat error:', error);
        }
        
        this.isLoading = false;
        const send = this.getSendButton();
        if (send) send.disabled = false;
    },
    
    isCodeGenerationRequest(message) {
        const codeKeywords = [
            'crea', 'genera', 'construye', 'haz', 'diseña',
            'create', 'generate', 'build', 'make', 'design',
            'landing', 'página', 'page', 'form', 'formulario',
            'html', 'css', 'javascript', 'website', 'sitio',
            'app', 'aplicación', 'proyecto', 'project'
        ];
        const lowerMessage = message.toLowerCase();
        return codeKeywords.some(kw => lowerMessage.includes(kw));
    },
    
    async sendConstructorMessage(message) {
        this.showTyping();
        
        try {
            const response = await fetch('/api/ai-constructor/process', {
                method: 'POST',
                headers: this.getApiHeaders(),
                body: JSON.stringify({
                    message: message,
                    currentFiles: this.files,
                    projectName: 'BUNK3R Project'
                })
            });
            
            const data = await response.json();
            this.hideTyping();
            this.hidePhaseProgress();
            
            if (data.success) {
                this.handleConstructorResponse(data);
            } else {
                if (response.status === 403) {
                    this.appendMessage('assistant', 'Esta funcion es solo para el propietario. Necesitas permisos de owner para usar el constructor de IA.');
                } else {
                    this.appendMessage('assistant', data.error || 'Error al procesar. Intenta de nuevo.');
                }
            }
        } catch (error) {
            this.hideTyping();
            this.hidePhaseProgress();
            this.appendMessage('assistant', 'Error de conexion. Verifica tu internet e intenta de nuevo.');
            console.error('AI Constructor error:', error);
        }
        
        this.isLoading = false;
        const send = this.getSendButton();
        if (send) send.disabled = false;
    },
    
    handleConstructorResponse(data) {
        if (data.fase && data.fase_nombre) {
            this.currentPhase = data.fase;
            this.appendPhaseIndicator(data.fase, data.fase_nombre, false);
        }
        
        if (data.session) {
            this.currentSession = data.session;
            this.esperandoConfirmacion = data.session.esperando_confirmacion || false;
            this.esperandoClarificacion = data.session.esperando_clarificacion || false;
        }
        
        if (data.response) {
            this.appendMessage('assistant', data.response);
        }
        
        if (data.plan && data.esperando_input) {
            this.appendConfirmationButtons(data.plan);
        }
        
        if (data.files) {
            this.processFiles(data.files);
        }
        
        if (data.verification) {
            this.showVerificationResult(data.verification);
        }
        
        const indicator = this.getProviderIndicator();
        if (indicator && data.fase_nombre) {
            indicator.innerHTML = `<span class="provider-label">Fase: ${this.escapeHtml(data.fase_nombre)}</span>`;
        }
    },
    
    showVerificationResult(verification) {
        const container = this.getMessagesContainer();
        if (!container) return;
        
        const score = verification.puntuacion || 0;
        const scoreClass = score >= 80 ? 'good' : (score >= 50 ? 'warning' : 'error');
        
        const verificationDiv = document.createElement('div');
        verificationDiv.className = 'ai-verification-result';
        
        let errorsHtml = '';
        if (verification.errores && verification.errores.length > 0) {
            errorsHtml = `<div class="verification-errors">
                <span class="error-label">Errores:</span>
                <ul>${verification.errores.map(e => `<li>${this.escapeHtml(e)}</li>`).join('')}</ul>
            </div>`;
        }
        
        let warningsHtml = '';
        if (verification.advertencias && verification.advertencias.length > 0) {
            warningsHtml = `<div class="verification-warnings">
                <span class="warning-label">Advertencias:</span>
                <ul>${verification.advertencias.map(w => `<li>${this.escapeHtml(w)}</li>`).join('')}</ul>
            </div>`;
        }
        
        verificationDiv.innerHTML = `
            <div class="verification-header">
                <span class="verification-title">Verificacion</span>
                <span class="verification-score ${scoreClass}">${score}/100</span>
            </div>
            <div class="verification-checks">
                <div class="check ${verification.sintaxis_valida ? 'passed' : 'failed'}">
                    <span class="check-icon">${verification.sintaxis_valida ? '✓' : '✗'}</span>
                    Sintaxis
                </div>
                <div class="check ${verification.completitud ? 'passed' : 'failed'}">
                    <span class="check-icon">${verification.completitud ? '✓' : '✗'}</span>
                    Completo
                </div>
                <div class="check ${verification.responsive ? 'passed' : 'failed'}">
                    <span class="check-icon">${verification.responsive ? '✓' : '✗'}</span>
                    Responsive
                </div>
            </div>
            ${errorsHtml}
            ${warningsHtml}
        `;
        
        container.appendChild(verificationDiv);
        container.scrollTop = container.scrollHeight;
    },
    
    processFiles(files) {
        this.devLog('AIChat processFiles - received files:', Object.keys(files));
        
        for (const [filename, content] of Object.entries(files)) {
            const isNew = !this.files[filename];
            this.files[filename] = content;
            this.devLog(`AIChat processFiles - ${isNew ? 'created' : 'updated'}: ${filename} (${content.length} chars)`);
            this.appendCodeAction(isNew ? 'create' : 'update', filename);
        }
        
        this.devLog('AIChat processFiles - all files now:', Object.keys(this.files));
        
        this.switchTab('preview');
        this.saveToStorage();
    },
    
    async resetSession() {
        try {
            const response = await fetch('/api/ai-constructor/reset', {
                method: 'POST',
                headers: this.getApiHeaders()
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentSession = null;
                this.currentPhase = 0;
                this.esperandoConfirmacion = false;
                this.esperandoClarificacion = false;
                this.appendMessage('assistant', 'Sesion reiniciada. Puedes empezar un nuevo proyecto.');
            }
        } catch (e) {
            console.error('Error resetting session:', e);
        }
    },
    
    async clearChat() {
        if (!confirm('Limpiar el proyecto actual?')) return;
        
        this.messages = [];
        this.files = {};
        localStorage.removeItem('bunkr_ai_project');
        
        await this.resetSession();
        
        const container = this.getMessagesContainer();
        if (container) {
            container.innerHTML = `
                <div class="ai-chat-welcome">
                    <div class="ai-avatar">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="32" height="32">
                            <path d="M12 2a4 4 0 0 1 4 4v1h1a3 3 0 0 1 3 3v2a3 3 0 0 1-3 3h-1v1a4 4 0 0 1-8 0v-1H7a3 3 0 0 1-3-3v-2a3 3 0 0 1 3-3h1V6a4 4 0 0 1 4-4z"></path>
                            <circle cx="9" cy="10" r="1" fill="currentColor"></circle>
                            <circle cx="15" cy="10" r="1" fill="currentColor"></circle>
                        </svg>
                    </div>
                    <h3>BUNK3R AI Builder</h3>
                    <p>Dime que quieres crear</p>
                    <div class="ai-quick-actions" id="ai-quick-actions">
                        <button class="ai-quick-btn" data-prompt="Crea una landing page moderna con hero, features y contacto">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                                <line x1="3" y1="9" x2="21" y2="9"></line>
                            </svg>
                            Landing Page
                        </button>
                        <button class="ai-quick-btn" data-prompt="Crea un formulario de contacto con validacion">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                <polyline points="14 2 14 8 20 8"></polyline>
                                <line x1="16" y1="13" x2="8" y2="13"></line>
                                <line x1="16" y1="17" x2="8" y2="17"></line>
                            </svg>
                            Formulario
                        </button>
                    </div>
                </div>
            `;
            this.bindQuickActions();
        }
        
        this.switchTab('preview');
    }
};

document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        AIChat.init();
        AIChat.hookNavigation();
        AIChat.initStreamingCleanup();
    }, 500);
});

AIChat.initStreamingCleanup = function() {
    window.addEventListener('beforeunload', () => {
        this.closeEventSource();
    });
    
    document.addEventListener('visibilitychange', () => {
        if (document.hidden && this.currentEventSource) {
            this.devLog('Page hidden, keeping connection alive');
        }
    });
};

AIChat.hookNavigation = function() {
    document.querySelectorAll('.bottom-nav-item[data-nav="ai-chat"]').forEach(btn => {
        btn.addEventListener('click', () => {
            setTimeout(() => {
                AIChat.isPageMode = true;
                AIChat.initPageMode();
            }, 100);
        });
    });
    
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.addEventListener('click', (e) => {
            const menuItem = e.target.closest('[data-screen="ai-chat"]');
            if (menuItem) {
                setTimeout(() => {
                    AIChat.isPageMode = true;
                    AIChat.initPageMode();
                }, 100);
            }
        });
    }
};

AIChat.streamingEnabled = true;
AIChat.currentEventSource = null;

AIChat.sendStreamingMessage = async function(message) {
    if (!this.streamingEnabled) {
        return this.sendConstructorMessage(message);
    }
    
    let container = this.getMessagesContainer();
    if (!container) {
        container = document.getElementById('ai-chat-messages');
        if (!container) {
            this.devLog('Streaming: No message container, falling back to constructor');
            return this.sendConstructorMessage(message);
        }
    }
    
    const msgDiv = document.createElement('div');
    msgDiv.className = 'ai-message ai-message-assistant ai-streaming';
    msgDiv.id = 'ai-streaming-response';
    msgDiv.innerHTML = `
        <div class="ai-avatar">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="20" height="20">
                <path d="M12 2a4 4 0 0 1 4 4v1h1a3 3 0 0 1 3 3v2a3 3 0 0 1-3 3h-1v1a4 4 0 0 1-8 0v-1H7a3 3 0 0 1-3-3v-2a3 3 0 0 1 3-3h1V6a4 4 0 0 1 4-4z"></path>
            </svg>
        </div>
        <div class="ai-bubble ai-streaming-content">
            <span class="ai-cursor"></span>
        </div>
    `;
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
    
    const contentEl = msgDiv.querySelector('.ai-streaming-content');
    let fullContent = '';
    
    try {
        const userId = 'anonymous';
        const url = `/api/ai/chat/stream?user_id=${encodeURIComponent(userId)}&message=${encodeURIComponent(message)}`;
        
        this.currentEventSource = new EventSource(url);
        
        this.currentEventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                switch(data.type) {
                    case 'start':
                        this.devLog('Streaming started:', data.metadata);
                        const indicator = this.getProviderIndicator();
                        if (indicator && data.metadata?.provider) {
                            indicator.innerHTML = `<span class="provider-label">${data.metadata.provider}</span>`;
                        }
                        break;
                        
                    case 'token':
                        fullContent += data.data;
                        contentEl.innerHTML = this.formatMessage(fullContent) + '<span class="ai-cursor"></span>';
                        container.scrollTop = container.scrollHeight;
                        break;
                        
                    case 'complete':
                        contentEl.innerHTML = this.formatMessage(fullContent);
                        msgDiv.classList.remove('ai-streaming');
                        msgDiv.id = '';
                        this.messages.push({ role: 'assistant', content: fullContent });
                        this.closeEventSource();
                        this.finishStreamingUI();
                        break;
                        
                    case 'error':
                        contentEl.innerHTML = `<span class="ai-error">Error: ${this.escapeHtml(data.data)}</span>`;
                        msgDiv.classList.remove('ai-streaming');
                        this.closeEventSource();
                        this.finishStreamingUI();
                        break;
                        
                    case 'metadata':
                        this.devLog('Streaming metadata:', data);
                        break;
                }
            } catch (e) {
                console.error('Error parsing SSE:', e);
            }
        };
        
        this.currentEventSource.onerror = (error) => {
            console.error('SSE error:', error);
            if (fullContent) {
                contentEl.innerHTML = this.formatMessage(fullContent);
                this.messages.push({ role: 'assistant', content: fullContent });
            } else {
                contentEl.innerHTML = '<span class="ai-error">Error de conexion</span>';
            }
            msgDiv.classList.remove('ai-streaming');
            this.closeEventSource();
            this.finishStreamingUI();
        };
        
    } catch (error) {
        console.error('Streaming error:', error);
        contentEl.innerHTML = `<span class="ai-error">Error: ${this.escapeHtml(error.message)}</span>`;
        msgDiv.classList.remove('ai-streaming');
        this.isLoading = false;
        const send = this.getSendButton();
        if (send) send.disabled = false;
    }
};

AIChat.closeEventSource = function() {
    if (this.currentEventSource) {
        this.currentEventSource.close();
        this.currentEventSource = null;
    }
};

AIChat.finishStreamingUI = function() {
    this.isLoading = false;
    
    const send = this.getSendButton();
    if (send) send.disabled = false;
    
    const input = this.getInput();
    if (input) {
        input.disabled = false;
        input.focus();
    }
    
    const indicator = this.getProviderIndicator();
    if (indicator) {
        indicator.innerHTML = '';
    }
    
    this.devLog('Streaming finished, UI reset');
};

AIChat.toggleStreaming = function(enabled) {
    this.streamingEnabled = enabled;
    this.devLog('Streaming', enabled ? 'enabled' : 'disabled');
};

AIChat.sendQuickStreamMessage = async function(message) {
    const input = this.getInput();
    const send = this.getSendButton();
    
    if (this.isLoading) return;
    
    this.isLoading = true;
    if (input) input.value = '';
    if (send) send.disabled = true;
    
    this.appendMessage('user', message);
    await this.sendStreamingMessage(message);
};
