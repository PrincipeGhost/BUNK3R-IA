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

    async init() {
        this.devLog('Initializing AIChat...');
        this.startBrainMonitor();
        // ... rest of init logic if any ...
    },

    async startBrainMonitor() {
        const updateUI = (data) => {
            const dot = document.getElementById('brain-status-dot');
            const text = document.getElementById('brain-status-text');
            if (!dot || !text) return;

            if (data.ollama_url && data.ollama_url !== 'Not configured') {
                dot.style.background = '#00ff00'; // Green
                dot.style.boxShadow = '0 0 5px #00ff00';
                text.innerText = 'Cerebro Local Activo';
                text.style.color = '#00ff00';
            } else if (data.available_providers && data.available_providers.length > 0) {
                dot.style.background = '#f0b90b'; // Yellow
                dot.style.boxShadow = '0 0 5px #f0b90b';
                text.innerText = 'BUNK3R Cloud Activo';
                text.style.color = '#f0b90b';
            } else {
                dot.style.background = '#ff4444'; // Red
                dot.style.boxShadow = '0 0 5px #ff4444';
                text.innerText = 'Cerebro Desconectado';
                text.style.color = '#ff4444';
            }
        };

        const check = async () => {
            try {
                const resp = await fetch('/api/system/status');
                const data = await resp.json();
                updateUI(data);
            } catch (e) {
                updateUI({ status: 'error' });
            }
        };

        check();
        setInterval(check, 20000); // Check every 20s
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
    activeTabId: 'console',

    renderTabs() {
        const container = document.getElementById('ai-tabs-container');
        if (!container) return;

        container.innerHTML = '';
        this.openTabs.forEach(tab => {
            const tabEl = document.createElement('div');
            tabEl.className = `ai-tab-item ${this.activeTabId === tab.id ? 'active' : ''}`;
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
                e.stopPropagation();
                console.log('[AI-LOG] Click en pestaña:', tab.id);
                this.switchTab(tab.id);
            };

            container.appendChild(tabEl);
        });
    },

    init() {
        // --- COMMAND PROCESSING LOGIC ---
        this.processAICommands = function (content) {
            // Regex for [CLONE=owner/repo]
            const cloneMatch = content.match(/\[CLONE=(.*?)\]/);
            if (cloneMatch && cloneMatch[1]) {
                const repoName = cloneMatch[1].trim();
                console.log('[AI-COMMAND] CLONE detected for:', repoName);
                this.executeClone(repoName);
                return content.replace(cloneMatch[0], `<i>(Clonando repositorio: ${repoName}...)</i>`);
            }
            return content;
        };

        this.executeClone = async function (repoName) {
            const token = localStorage.getItem('github_token');
            if (!token) {
                this.appendMessage('assistant', '⚠️ Necesito tu Token de GitHub para clonar. Configúralo en la pestaña de Proyectos.');
                return;
            }

            const listContainer = document.getElementById('ai-projects-list');
            if (listContainer) listContainer.innerHTML = '<div class="ai-project-loading">Clonando repositorio...</div>';

            try {
                const response = await fetch('/api/repo/clone', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        repo: repoName,
                        token: token
                    })
                });

                const data = await response.json();
                if (data.success) {
                    this.appendMessage('assistant', `✅ Repositorio <b>${repoName}</b> clonado y listo para trabajar.`);
                    // Reload repos and file tree
                    if (window.loadGitHubRepos) window.loadGitHubRepos();
                    // Load file tree for this repo immediately
                    if (window.renderFileTree && data.path) {
                        // Try to auto-load file tree if possible, or just refresh projects
                    }
                } else {
                    this.appendMessage('assistant', `❌ Error al clonar: ${data.error}`);
                }
            } catch (e) {
                this.appendMessage('assistant', `❌ Error de conexión al clonar: ${e.message}`);
            }
        };

        console.log('[AI-LOG] AIChat init()');

        // Detectar si estamos en modo página completa
        const pageContainer = document.getElementById('ai-chat-screen');
        if (pageContainer && !pageContainer.classList.contains('hidden')) {
            this.isPageMode = true;
            this.initPageMode();
        } else {
            this.isPageMode = false;
            this.initWidgetMode();
        }

        this.loadSession();

        // Fetch Real GitHub Token for Extension & Clone
        fetch('/auth/token').then(r => r.json()).then(data => {
            if (data.token) {
                console.log('[Auth] Token real sincronizado.');
                localStorage.setItem('github_token', data.token);
            }
        }).catch(e => console.log('Auth check skipped'));

        this.initExtensionHandshake(); // Auto-configure Extension
        this.initModelSelector(); // Initialize Model Selector

        // Sincronizar estado inicial

        // Sincronizar estado inicial
        setTimeout(() => {
            this.switchTab(this.activeTabId);
        }, 300);

        // Auto-load GitHub repos if token exists
        setTimeout(() => {
            const token = localStorage.getItem('github_token');
            // Check if function exists before calling, or call directly if method of this object
            if (token && this.loadGitHubRepos) {
                console.log('[AI-LOG] Auto-loading GitHub repos...');
                this.loadGitHubRepos();
            }
        }, 1000);
    },

    async loadGitHubRepos() {
        const token = localStorage.getItem('github_token');
        const listContainer = document.getElementById('ai-projects-list');

        if (!token) return;
        if (!listContainer) return;

        listContainer.innerHTML = '<div class="ai-project-loading">Sincronizando repositorios...</div>';

        try {
            const response = await fetch(`/api/github/repos?token=${token}`);
            const data = await response.json();

            if (data.repos) {
                this.renderRemoteRepos(data.repos, listContainer);
            } else {
                listContainer.innerHTML = '<div class="error">No repos found or token invalid</div>';
            }
        } catch (e) {
            console.error('[AI-LOG] Error loading repos:', e);
            listContainer.innerHTML = '<div class="error">Connection Error</div>';
        }
    },

    initExtensionHandshake() {
        // Attempt to auto-configure the extension if present
        const handshake = () => {
            const apiUrl = window.location.origin;
            const token = localStorage.getItem('github_token') || 'demo-token'; // Or use proper auth token

            console.log('[AIChat] Sending Handshake to Extension...', apiUrl);
            window.postMessage({
                type: 'BUNK3R_HANDSHAKE',
                config: {
                    apiUrl: apiUrl,
                    token: token,
                    userId: 'current'
                }
            }, '*');
        };

        // Try immediately and a few times shortly after load
        // Aggressive Retry Strategy for Localhost
        handshake(); // 0ms
        setTimeout(handshake, 500); // 500ms
        setTimeout(handshake, 1500); // 1.5s
        setTimeout(handshake, 3000); // 3s
        setTimeout(handshake, 6000); // 6s

        // Expose debug helper globally
        window.retryHandshake = handshake;

        // Listen for success
        window.addEventListener('message', (e) => {
            if (e.data.type === 'BUNK3R_HANDSHAKE_SUCCESS') {
                console.log('✅ Extension Connected & Configured!');
                this.extensionConnected = true;

                // Show visual indicator if possible
                const status = document.getElementById('ai-brain-status');
                if (status) status.classList.add('connected');
            }
        });
    },

    async initModelSelector() {
        const btn = document.getElementById('ai-model-selector-btn');
        const dropdown = document.getElementById('ai-model-dropdown');
        const list = document.getElementById('ai-model-list');
        const currentName = document.getElementById('current-model-name');

        if (!btn || !dropdown || !list) return;

        // Toggle Dropdown
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdown.classList.toggle('hidden');
            dropdown.style.display = dropdown.classList.contains('hidden') ? 'none' : 'block';
        });

        // Close on click outside
        document.addEventListener('click', () => {
            dropdown.classList.add('hidden');
            dropdown.style.display = 'none';
        });

        // Load saved model
        const savedModel = localStorage.getItem('bunkr_selected_model');
        if (savedModel) {
            currentName.textContent = savedModel;
        }

        // Fetch Models with Fallback
        const fallbackModels = [
            { name: "GPT-4o", provider: "OpenAI", id: "gpt-4o" },
            { name: "Gemini 1.5 Pro", provider: "Google", id: "gemini-1.5-pro" },
            { name: "Claude 3.5 Sonnet", provider: "Anthropic", id: "claude-3-5-sonnet" },
            { name: "DeepSeek Coder", provider: "DeepSeek", id: "deepseek-coder" },
            { name: "BUNK3R-V1", provider: "BUNK3R", id: "bunk3r-preview" }
        ];

        const renderModels = (providers) => {
            list.innerHTML = '';
            if (!providers || providers.length === 0) providers = fallbackModels;

            providers.forEach(p => {
                const li = document.createElement('li');
                li.style.padding = '8px 12px';
                li.style.cursor = 'pointer';
                li.style.color = '#c9d1d9';
                li.style.fontSize = '12px';
                li.style.borderBottom = '1px solid #21262d';
                li.style.display = 'flex';
                li.style.justifyContent = 'space-between';
                li.style.alignItems = 'center';

                li.innerHTML = `
                    <span style="font-weight:500;">${this.escapeHtml(p.name)}</span>
                    <span style="color: #58a6ff; font-size: 10px; background: rgba(56,139,253,0.15); padding: 2px 6px; border-radius: 4px;">${this.escapeHtml(p.provider)}</span>
                `;

                li.addEventListener('mouseover', () => li.style.background = '#21262d');
                li.addEventListener('mouseout', () => li.style.background = 'transparent');

                li.addEventListener('click', () => {
                    const modelId = p.id || p.name;
                    currentName.textContent = p.name;
                    localStorage.setItem('bunkr_selected_model', p.name);
                    localStorage.setItem('bunkr_selected_model_id', modelId);
                    dropdown.classList.add('hidden');
                    dropdown.style.display = 'none';
                });

                list.appendChild(li);
            });
        };

        try {
            const response = await fetch('/api/ai-providers');
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.providers && data.providers.length > 0) {
                    renderModels(data.providers);
                } else {
                    renderModels(fallbackModels);
                }
            } else {
                renderModels(fallbackModels);
            }
        } catch (e) {
            console.error("Error fetching models, utilizing fallback:", e);
            renderModels(fallbackModels);
        }
    },

    renderRemoteRepos(repos, container) {
        container.innerHTML = '';
        const title = document.createElement('div');
        title.className = 'ai-sidebar-subtitle';
        title.innerHTML = `MIS REPOSITORIOS (${repos.length})`;
        title.style.cssText = 'padding: 10px; font-size: 11px; font-weight: 600; color: #6b7280; letter-spacing: 0.05em; margin-top: 10px;';
        container.appendChild(title);

        if (repos.length === 0) {
            container.innerHTML += '<div style="padding:15px; text-align:center; color:#6b7280; font-size:12px;">No repositories found.</div>';
            return;
        }

        repos.forEach(repo => {
            const item = document.createElement('div');
            item.className = 'file-item repo-item';
            item.style.cssText = 'padding: 8px 15px; cursor: pointer; color: #c9d1d9; font-size: 13px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.03);';

            const nameSpan = document.createElement('span');
            nameSpan.innerHTML = `
                <svg viewBox="0 0 16 16" width="14" height="14" fill="#c9d1d9" style="margin-right:8px; vertical-align:text-bottom;">
                    <path fill-rule="evenodd" d="M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm1.5 0v9c0 .356.094.687.257.975a2.49 2.49 0 01-.007.025h8.75v-9H3.5zM4 14.5a.5.5 0 100-1 .5.5 0 000 1z"></path>
                </svg>
                ${repo.name}
            `;

            const actionBtn = document.createElement('button');
            actionBtn.innerText = 'CLONAR';
            actionBtn.style.cssText = 'background: #238636; border: none; color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px; cursor: pointer; display: none;';

            item.addEventListener('mouseenter', () => actionBtn.style.display = 'block');
            item.addEventListener('mouseleave', () => actionBtn.style.display = 'none');

            item.onclick = () => {
                if (confirm(`¿Quieres clonar y trabajar en ${repo.name}?`)) {
                    this.executeClone(repo.full_name);
                }
            };

            item.appendChild(nameSpan);
            item.appendChild(actionBtn);
            container.appendChild(item);
        });
    },

    switchTab(tabId) {
        console.log('[AI-LOG] switchTab ->', tabId);
        this.activeTabId = tabId;
        this.activeTab = tabId; // Sincronizar ambos nombres de propiedad
        this.renderTabs();

        const consolePanel = document.getElementById('ai-console');
        const editorWrapper = document.getElementById('editor-wrapper');
        const previewPanel = document.getElementById('ai-preview-panel');
        const toolbar = document.getElementById('editor-toolbar');
        const emptyState = document.getElementById('ai-preview-empty');

        // Ocultar todos los paneles forzando con !important
        const allPanels = [consolePanel, editorWrapper, previewPanel, toolbar, emptyState];
        allPanels.forEach(p => {
            if (p) {
                p.classList.remove('active-panel');
                p.style.setProperty('display', 'none', 'important');
                p.style.setProperty('visibility', 'hidden', 'important');
                p.classList.add('hidden-panel');
            }
        });

        if (tabId === 'console') {
            if (consolePanel) {
                consolePanel.classList.add('active-panel');
                consolePanel.style.setProperty('display', 'flex', 'important');
                consolePanel.style.setProperty('visibility', 'visible', 'important');
                consolePanel.style.setProperty('z-index', '2147483647', 'important');
                consolePanel.classList.remove('hidden-panel');

                const output = document.getElementById('ai-console-output');
                if (output) {
                    output.style.setProperty('display', 'block', 'important');
                }

                setTimeout(() => {
                    const input = document.getElementById('ai-console-input');
                    if (input) input.focus();
                }, 100);
            }
        } else if (tabId === 'preview') {
            if (previewPanel) {
                previewPanel.classList.add('active-panel');
                previewPanel.style.setProperty('display', 'flex', 'important');
                previewPanel.style.setProperty('visibility', 'visible', 'important');
                previewPanel.style.setProperty('z-index', '2147483647', 'important');
                previewPanel.classList.remove('hidden-panel');
                this.updatePreview();
            }
        } else {
            // Caso de archivo (file-...) o tabs antiguas (html, css, js)
            if (editorWrapper) {
                editorWrapper.classList.add('active-panel');
                editorWrapper.style.setProperty('display', 'block', 'important');
                editorWrapper.style.setProperty('visibility', 'visible', 'important');
                editorWrapper.style.setProperty('z-index', '2147483647', 'important');
                editorWrapper.classList.remove('hidden-panel');
                if (toolbar) toolbar.style.setProperty('display', 'flex', 'important');

                const tab = this.openTabs.find(t => t.id === tabId);
                const editor = document.getElementById('ai-real-editor');
                if (tab && editor) {
                    editor.value = tab.content || '';
                }
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
        console.log('[AI-LOG] openFile INICIO -> path:', path, 'name:', name);

        // Normalización para Replit: quitar ./ si existe
        let cleanPath = path;
        if (path.startsWith('./')) cleanPath = path.substring(2);

        const tabId = `file-${cleanPath.replace(/\//g, '-')}`;
        console.log('[AI-LOG] openFile -> tabId:', tabId);

        const existingTab = this.openTabs.find(t => t.id === tabId);
        if (existingTab) {
            console.log('[AI-LOG] openFile -> Tab ya existe, activando...');
            this.switchTab(tabId);
            return;
        }

        console.log('[AI-LOG] openFile -> Cargando contenido desde API...');
        try {
            const url = `/api/projects/file/content?path=${encodeURIComponent(cleanPath)}`;
            console.log('[AI-LOG] openFile -> URL:', url);

            const response = await fetch(url);
            console.log('[AI-LOG] openFile -> Status API:', response.status);

            const data = await response.json();
            console.log('[AI-LOG] openFile -> Datos recibidos:', data);

            if (data.success) {
                console.log('[AI-LOG] openFile -> ÉXITO, contenido recibido, length:', data.content ? data.content.length : 0);
                const newTab = {
                    id: tabId,
                    name: name || cleanPath.split('/').pop(),
                    type: 'file',
                    path: cleanPath,
                    content: data.content
                };
                this.openTabs.push(newTab);
                this.activeTabId = tabId;

                this.renderTabs();
                this.switchTab(tabId);
            } else {
                console.error('[AI-LOG] openFile -> ERROR API:', data.error);
                // Si falla, reintentar con el nombre de archivo solamente
                const filename = cleanPath.split('/').pop();
                if (filename !== cleanPath) {
                    console.log('[AI-LOG] openFile -> Reintentando solo con nombre de archivo:', filename);
                    return this.openFile(filename, name);
                }
                alert('Error al cargar archivo: ' + data.error);
            }
        } catch (e) {
            console.error('[AI-LOG] openFile -> EXCEPCIÓN FETCH:', e);
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

    initPageMode() {
        const input = document.getElementById('ai-chat-input');
        const send = document.getElementById('ai-chat-send');
        const sendArrow = document.getElementById('ai-chat-send-arrow');

        if (!input) return;

        input.removeEventListener('input', this.handleInputChange);
        input.removeEventListener('keydown', this.handleKeyDown);

        this.handleInputChange = () => {
            if (send) send.disabled = !input.value.trim();
            if (sendArrow) sendArrow.disabled = !input.value.trim();
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

        if (send) send.addEventListener('click', this.handleSendClick);
        if (sendArrow) sendArrow.addEventListener('click', this.handleSendClick);

        this.bindQuickActions();
        this.bindFileTabs();
        this.bindRefreshButton();
        this.bindCodeEditor();
        this.bindConsole();
        this.bindSidebarToggle();
        this.bindResizer();

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

    // escapeHtml consolidated at line 870


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

    // switchTab anterior eliminada por duplicación ,

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

    bindResizer() {
        const resizer = document.getElementById('main-resizer');
        const leftPanel = document.getElementById('panel-chat');
        if (!resizer || !leftPanel) return;

        let isResizing = false;

        resizer.addEventListener('mousedown', (e) => {
            isResizing = true;
            document.body.style.cursor = 'col-resize';
            resizer.classList.add('resizing');
            document.body.style.userSelect = 'none';
            e.preventDefault();

            // Inyectar overlay para evitar que el iframe capture eventos
            const overlay = document.createElement('div');
            overlay.id = 'resizer-overlay';
            overlay.style.position = 'fixed';
            overlay.style.top = '0';
            overlay.style.left = '0';
            overlay.style.right = '0';
            overlay.style.bottom = '0';
            overlay.style.zIndex = '99998';
            overlay.style.cursor = 'col-resize';
            document.body.appendChild(overlay);
        });

        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;

            const activityBar = document.querySelector('.activity-bar');
            const offset = activityBar ? activityBar.offsetWidth : 50;
            const newWidth = e.clientX - offset;

            if (newWidth >= 100 && newWidth <= window.innerWidth * 0.8) {
                console.log('[RESIZER] Aplicando ancho:', newWidth);

                // Aplicar a ambos para asegurar compatibilidad
                leftPanel.style.setProperty('width', newWidth + 'px', 'important');
                leftPanel.style.setProperty('flex', '0 0 ' + newWidth + 'px', 'important');
                leftPanel.style.setProperty('min-width', newWidth + 'px', 'important');
                leftPanel.style.setProperty('max-width', newWidth + 'px', 'important');
            }
        });

        document.addEventListener('mouseup', () => {
            if (isResizing) {
                isResizing = false;
                document.body.style.cursor = 'default';
                resizer.classList.remove('resizing');
                document.body.style.userSelect = 'auto';

                const overlay = document.getElementById('resizer-overlay');
                if (overlay) overlay.remove();
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
                <div class="ai-bubble">${this.formatMessage(this.processAICommands ? this.processAICommands(content) : content)}</div>
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

    async runConsoleCommand(command) {
        console.log('[CONSOLE] Running command:', command);
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
        loadingLine.textContent = '... ejecutando comando ...';
        output.appendChild(loadingLine);
        output.scrollTop = output.scrollHeight;

        try {
            // Robust auth headers
            let headers = { 'Content-Type': 'application/json' };
            if (typeof App !== 'undefined' && App.getAuthHeaders) {
                headers = { ...headers, ...App.getAuthHeaders() };
            }

            console.log('[CONSOLE-FETCH] Sending request to /api/projects/command/run');
            const response = await fetch('/api/projects/command/run', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ command, timeout: 30 })
            });

            console.log('[CONSOLE-FETCH] Response received:', response.status, response.statusText);
            if (!response.ok) {
                const errorText = await response.text();
                console.error('[CONSOLE-FETCH] Error response text:', errorText);
                throw new Error(`HTTP ${response.status}: ${errorText.substring(0, 100)}`);
            }

            const data = await response.json();
            console.log('[CONSOLE-FETCH] Data:', data);

            loadingLine.remove();

            if (data.success) {
                if (data.stdout) {
                    const outLine = document.createElement('div');
                    outLine.className = 'console-line output';
                    outLine.style.whiteSpace = 'pre-wrap';
                    outLine.textContent = data.stdout;
                    output.appendChild(outLine);
                }
                if (data.stderr) {
                    const errLine = document.createElement('div');
                    errLine.className = 'console-line error';
                    errLine.style.color = '#ff6b6b';
                    errLine.textContent = data.stderr;
                    output.appendChild(errLine);
                }
                if (!data.stdout && !data.stderr) {
                    const okLine = document.createElement('div');
                    okLine.className = 'console-line success';
                    okLine.style.color = '#51cf66';
                    okLine.textContent = '✓ Ejecutado.';
                    output.appendChild(okLine);
                }
            } else {
                const errLine = document.createElement('div');
                errLine.className = 'console-line error';
                errLine.textContent = 'FALLO: ' + (data.error || 'Error desconocido');
                output.appendChild(errLine);
            }
        } catch (error) {
            if (loadingLine) loadingLine.remove();
            console.error('[CONSOLE-ERROR]', error);
            const errLine = document.createElement('div');
            errLine.className = 'console-line error';
            errLine.textContent = `CRITICAL: ${error.message}`;
            output.appendChild(errLine);
        }
        output.scrollTop = output.scrollHeight;
    },

    escapeHtml(text) {
        if (!text) return "";
        const div = document.createElement('div');
        div.textContent = String(text);
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

        const hasFiles = Object.keys(this.files).length > 0;
        if (hasFiles) {
            iframe.style.display = 'block';
            if (emptyState) emptyState.style.display = 'none';
        } else {
            iframe.style.display = 'none';
            if (emptyState) emptyState.style.display = 'flex';
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
            console.log('[AI-LOG] Sending simple chat request...');
            const response = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: this.getApiHeaders(),
                body: JSON.stringify({
                    message: message,
                    user_id: 'demo_user'
                })
            });

            const data = await response.json();
            console.log('[AI-LOG] Simple chat response:', data);
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

                // Refresh Preview Iframe
                const previewFrame = document.getElementById('ai-preview-iframe');
                if (previewFrame) {
                    const userId = "demo_user"; // TODO: Get dynamic user ID if available
                    // Use new preview route
                    previewFrame.src = `/api/preview/${userId}/`;
                    previewFrame.style.display = 'block';
                    document.getElementById('ai-preview-empty').style.display = 'none';

                    // Tell extension to wake up and allow connection
                    if (chrome && chrome.runtime) {
                        try {
                            // We can't directly talk to extension background from here easily without exact ID.
                            // But we can rely on the Extension Content Script picking up an event or specialized message.
                            window.postMessage({ type: 'BUNK3R_CONNECT_BRAIN', url: previewFrame.src }, '*');
                        } catch (e) { console.warn("Extension connect failed", e); }
                    }
                }

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

AIChat.initStreamingCleanup = function () {
    window.addEventListener('beforeunload', () => {
        this.closeEventSource();
    });

    document.addEventListener('visibilitychange', () => {
        if (document.hidden && this.currentEventSource) {
            this.devLog('Page hidden, keeping connection alive');
        }
    });
};

AIChat.hookNavigation = function () {
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

AIChat.sendStreamingMessage = async function (message) {
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

                switch (data.type) {
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

AIChat.closeEventSource = function () {
    if (this.currentEventSource) {
        this.currentEventSource.close();
        this.currentEventSource = null;
    }
};

AIChat.finishStreamingUI = function () {
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

AIChat.toggleStreaming = function (enabled) {
    this.streamingEnabled = enabled;
    this.devLog('Streaming', enabled ? 'enabled' : 'disabled');
};

AIChat.sendQuickStreamMessage = async function (message) {
    const input = this.getInput();
    const send = this.getSendButton();

    if (this.isLoading) return;

    this.isLoading = true;
    if (input) input.value = '';
    if (send) send.disabled = true;

    this.appendMessage('user', message);
    await this.sendStreamingMessage(message);
};
// Exportar para que sea accesible desde otros scripts
if (typeof window !== 'undefined') {
    window.AIChat = AIChat;
    console.log('[AI-LOG] AIChat exported to window');
}
