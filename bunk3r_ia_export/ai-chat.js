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
            
            const response = await fetch('/api/ai-toolkit/command/run', {
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
        
        await this.sendConstructorMessage(message);
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
    }, 500);
});

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
