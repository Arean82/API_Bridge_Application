class TemplateModalController {
    constructor() {
        this.mode = 'edit';
        this.templateId = null;
        this.templateName = '';
        this.sources = [];
        this.editSource = false;
        this.executionMode = 'push';
        this.mappedFields = [];
        this.connsLookup = window.parsedConnsData || {};
        this.templates = window.parsedTemplatesData || [];

        // Defer DOM init until modal is requested
    }

    initDOM() {
        if (this.isInitialized) return;
        this.modal = document.getElementById('editTemplateModal');
        if (!this.modal) return;
        
        this.modalBackdrop = document.getElementById('editModalBackdrop');
        this.modalTitle = document.getElementById('templateModalTitle');
        this.templateNameInput = document.getElementById('templateName');
        this.editSourceWrapper = document.getElementById('editSourceWrapper');
        this.editSourceCheckbox = document.getElementById('editSourceCheckbox');
        this.addEndpointBtn = document.getElementById('addSourceBtn');
        this.sourcesContainer = document.getElementById('sourcesContainer');
        // Mode & Pull Fields in Modal
        this.executionModeSelect = document.getElementById('executionModeModal');
        this.globalTokenWrapperModal = document.getElementById('globalTokenWrapperModal');
        this.globalSecurityTokenModal = document.getElementById('globalSecurityTokenModal');
        this.toggleGlobalTokenBtnModal = document.getElementById('toggleGlobalTokenBtnModal');
        
        this.pushConfigBlockModal = document.getElementById('pushConfigBlockModal');
        this.pullRestConfigBlockModal = document.getElementById('pullRestConfigBlockModal');
        this.pullGraphqlConfigBlockModal = document.getElementById('pullGraphqlConfigBlockModal');
        
        this.pushHandler = new window.PushHandler('destinationsContainerModal', 'addDestinationBtnModal');
        this.pullRestHandler = new window.PullRestHandler('restEndpointsContainerModal', 'addRestEndpointBtnModal');
        this.pullGraphqlHandler = new window.PullGraphqlHandler('graphqlEndpointsContainerModal', 'addGraphqlEndpointBtnModal');
        
        this.scheduleIntervalWrapper = document.getElementById('scheduleInterval')?.parentElement;
        this.saveBtn = document.getElementById('saveTemplateBtn');
        
        this.cancelBtns = [
            document.getElementById('closeEditModalBtn'),
            document.getElementById('cancelEditModalBtn'),
            this.modalBackdrop
        ].filter(Boolean);
        
        this.bindEvents();
        this.isInitialized = true;
    }

    bindEvents() {
        this.cancelBtns.forEach(btn => btn.addEventListener('click', () => this.closeModal()));
        this.saveBtn.addEventListener('click', () => this.saveTemplate());
        this.addEndpointBtn.addEventListener('click', () => this.addSource());
        this.templateNameInput.addEventListener('input', (e) => {
            this.templateName = e.target.value;
            this.modalTitle.textContent = this.templateName ? (this.mode === 'edit' ? 'Edit ' : 'Clone ') + this.templateName : (this.mode === 'edit' ? 'Edit Template' : 'Clone Template');
            if (this.pullRestHandler) this.pullRestHandler.setEndpointUrl(this.templateName);
            if (this.pullGraphqlHandler) this.pullGraphqlHandler.setEndpointUrl(this.templateName);
        });
        if(this.executionModeSelect) this.executionModeSelect.addEventListener('change', (e) => { this.executionMode = e.target.value; this.renderMode(); });
        this.editSourceCheckbox.addEventListener('change', (e) => {
            this.editSource = e.target.checked;
            this.addEndpointBtn.style.display = this.editSource ? 'inline-block' : 'none';
            this.renderSources();
        });

        if (this.toggleGlobalTokenBtnModal && this.globalSecurityTokenModal) {
            this.toggleGlobalTokenBtnModal.addEventListener('click', () => {
                const type = this.globalSecurityTokenModal.getAttribute('type') === 'password' ? 'text' : 'password';
                this.globalSecurityTokenModal.setAttribute('type', type);
                this.toggleGlobalTokenBtnModal.innerHTML = type === 'password' ? 
                    `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path></svg>` : 
                    `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"></path></svg>`;
            });
        }
    }

    get currentApiFields() {
        let allFields = [];
        this.sources.forEach((src, idx) => {
            let api = src.availableApis && src.availableApis.find(a => a.path === src.selectedApi);
            if (api && api.fields) {
                api.fields.forEach(f => {
                    allFields.push(`source_${idx}.${f}`);
                });
            }
        });
        return allFields;
    }

    renderMode() {
        if (!this.isInitialized) return;
        this.executionMode = this.executionModeSelect.value;
        
        this.pushConfigBlockModal.style.display = 'none';
        this.pullRestConfigBlockModal.style.display = 'none';
        this.pullGraphqlConfigBlockModal.style.display = 'none';
        if(this.scheduleIntervalWrapper) this.scheduleIntervalWrapper.style.display = 'none';
        if(this.globalTokenWrapperModal) this.globalTokenWrapperModal.style.display = 'none';
        
        if (this.executionMode === 'push') {
            this.pushConfigBlockModal.style.display = 'block';
            if(this.scheduleIntervalWrapper) this.scheduleIntervalWrapper.style.display = 'block';
        } else {
            if(this.globalTokenWrapperModal) this.globalTokenWrapperModal.style.display = 'block';
            if (this.executionMode === 'pull_rest') {
                this.pullRestConfigBlockModal.style.display = 'block';
                this.pullRestHandler.setEndpointUrl(this.templateName);
            } else if (this.executionMode === 'pull_graphql') {
                this.pullGraphqlConfigBlockModal.style.display = 'block';
                this.pullGraphqlHandler.setEndpointUrl(this.templateName);
            }
        }
    }

    async openEdit(templateId) {
        this.initDOM();
        this.mode = 'edit';
        this.editSource = true;
        await this.populateForm(templateId);
        this.renderAll();
        this.showModal();
    }

    async openClone(templateId) {
        this.initDOM();
        this.mode = 'clone';
        this.editSource = false;
        await this.populateForm(templateId);
        this.templateName = this.templateName ? this.templateName + " (Copy)" : "New Clone";
        this.templateId = null;
        this.executionMode = 'push';
        this.renderAll();
        this.showModal();
    }

    async populateForm(id) {
        const t = this.templates.find(t => t.id === id);
        if (!t) return;

        this.templateId = t.id;
        this.templateName = t.name || '';

        if (t.sources && t.sources.length > 0) {
            this.sources = t.sources.map(s => ({
                id: Date.now() + Math.random(),
                connectionId: s.connectionId ? String(s.connectionId) : '',
                selectedApi: s.selectedApi || '',
                url: s.url || '',
                auth_token: s.auth_token || '',
                availableApis: []
            }));
        } else if (t.partner_url) {
            this.sources = [{ id: Date.now(), connectionId: '', selectedApi: '', url: t.partner_url, auth_token: t.partner_auth_token || '', availableApis: [] }];
        } else {
            this.sources = [{ id: Date.now(), connectionId: '', selectedApi: '', url: '', auth_token: '', availableApis: [] }];
        }

        for (let i = 0; i < this.sources.length; i++) {
            let savedApi = this.sources[i].selectedApi;
            await this.fetchApiDocs(i, false);
            this.sources[i].selectedApi = savedApi; 
        }
        
        this.updateDestinationFields();


        if (t.execution_mode === 'pull') {
            this.executionMode = t.pull_method === 'GRAPHQL' ? 'pull_graphql' : 'pull_rest';
        } else {
            this.executionMode = t.execution_mode || 'push';
        }
        
        let dests = [];
        if (t.destinations && t.destinations.length > 0) {
            dests = t.destinations;
        } else if (t.client_url) {
            let oldAuthType = t.client_auth_type || 'none';
            let oldAuthToken = t.client_credentials?.token || '';
            try {
                let cc = JSON.parse(t.client_credentials_json);
                if (this.globalSecurityTokenModal) this.globalSecurityTokenModal.value = cc.token || '';
            } catch(e){}
            dests = [{
                id: Date.now(),
                url: t.client_url,
                method: 'POST',
                auth_type: oldAuthType,
                auth_token: oldAuthToken
            }];
        } else if (t.client_credentials) {
            if (this.globalSecurityTokenModal) this.globalSecurityTokenModal.value = t.client_credentials.token || '';
        }
        this.pushHandler.loadDestinations(dests);
        this.pullRestHandler.setEndpointUrl(this.templateName);
        this.pullRestHandler.loadData(dests);
        this.pullGraphqlHandler.setEndpointUrl(this.templateName);
        this.pullGraphqlHandler.loadData(dests);
    }

    async fetchApiDocs(idx, reRender = true) {
        let src = this.sources[idx];
        let url = '/api/docs';
        if (src.connectionId) {
            url += `?connection_id=${src.connectionId}`;
        }
        try {
            let res = await fetch(url);
            src.availableApis = await res.json();
            
            if (!src.selectedApi && src.url) {
                const match = src.availableApis.find(a => src.url.includes(a.path));
                if (match) src.selectedApi = match.path;
            }
            if (reRender) {
                this.renderSources();
                this.updateDestinationFields();
            }
        } catch (e) {
            console.error("Failed to load API docs", e);
        }
    }

    addSource() {
        this.sources.push({ id: Date.now(), connectionId: '', selectedApi: '', url: '', auth_token: '', availableApis: [] });
        this.fetchApiDocs(this.sources.length - 1);
    }

    removeSource(index) {
        this.sources.splice(index, 1);
        this.renderSources();
        this.renderSources();
    }



    renderAll() {
        this.modalTitle.textContent = this.mode === 'edit' ? 'Edit Template' : 'Clone Template';
        this.templateNameInput.value = this.templateName;
        this.editSourceWrapper.style.display = 'flex';
        this.editSource = this.mode === 'clone';
        this.editSourceCheckbox.checked = this.editSource;
        this.addEndpointBtn.style.display = this.editSource ? 'inline-block' : 'none';
        
        if(this.executionModeSelect) this.executionModeSelect.value = this.executionMode;
        
        this.renderMode();
    }

    updateDestinationFields() {
        let fields = this.currentApiFields;
        if (this.pushHandler) this.pushHandler.setAvailableFields(fields);
        if (this.pullRestHandler) this.pullRestHandler.setAvailableFields(fields);
        if (this.pullGraphqlHandler) this.pullGraphqlHandler.setAvailableFields(fields);
    }

    renderSources() {
        this.sourcesContainer.innerHTML = '';
        this.sources.forEach((src, idx) => {
            const div = document.createElement('div');
            div.className = `relative p-5 border border-black/10 rounded-lg bg-gray-50/50 shadow-sm ${!this.editSource ? 'opacity-50' : ''}`;
            
            let html = `
                ${this.editSource && this.sources.length > 1 ? `<button class="absolute top-3 right-3 text-red-400 hover:text-red-600 remove-src-btn" data-idx="${idx}"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg></button>` : ''}
                <h4 class="font-bold text-sm mb-4 theme-text-muted">ENDPOINT <span>${idx + 1}</span></h4>
                <div class="grid grid-cols-2 gap-4">
                    <div class="col-span-2">
                        <label class="block text-sm font-medium mb-1">Swagger Connection</label>
                        <select class="theme-input w-full p-2.5 text-sm src-conn-sel" data-idx="${idx}" ${!this.editSource ? 'disabled' : ''}>
                            <option value="">-- Select Connection --</option>
                            ${Object.entries(this.connsLookup).map(([id, name]) => `<option value="${id}" ${src.connectionId === id ? 'selected' : ''}>${name}</option>`).join('')}
                        </select>
                    </div>
                    <div class="col-span-2">
                        <label class="block text-sm font-medium mb-1">Select API Endpoint</label>
                        <select class="theme-input w-full p-2.5 text-sm src-api-sel" data-idx="${idx}" ${!this.editSource || !src.availableApis.length ? 'disabled' : ''}>
                            <option value="">-- Choose API --</option>
                            ${src.availableApis.map(api => `<option value="${api.path}" ${src.selectedApi === api.path ? 'selected' : ''}>${api.name} (${api.path})</option>`).join('')}
                        </select>
                    </div>
                    <div class="col-span-2">
                        <label class="block text-sm font-medium mb-1">Source URL</label>
                        <input type="text" class="theme-input w-full p-2.5 text-sm src-url-in" data-idx="${idx}" value="${src.url}" ${!this.editSource ? 'disabled' : ''}>
                    </div>
                    <div class="col-span-2">
                        <label class="block text-sm font-medium mb-1">Source Auth Key (Bearer)</label>
                        <input type="password" class="theme-input w-full p-2.5 text-sm src-auth-in" data-idx="${idx}" value="${src.auth_token}" ${!this.editSource ? 'disabled' : ''} placeholder="Optional">
                    </div>
                </div>
            `;
            div.innerHTML = html;
            
            if (this.editSource && this.sources.length > 1) {
                div.querySelector('.remove-src-btn').addEventListener('click', (e) => {
                    e.preventDefault();
                    this.removeSource(parseInt(e.currentTarget.dataset.idx));
                });
            }
            if (this.editSource) {
                div.querySelector('.src-conn-sel').addEventListener('change', (e) => { this.sources[idx].connectionId = e.target.value; this.fetchApiDocs(idx); });
                div.querySelector('.src-api-sel').addEventListener('change', (e) => { 
                    let path = e.target.value;
                    this.sources[idx].selectedApi = path || ''; 
                    let conn = window.appState.connections.find(c => c.id == this.sources[idx].connectionId);
                    let base = conn && conn.url ? new URL(conn.url).origin : '';
                    if (base && base.endsWith('/')) base = base.slice(0, -1);
                    if (path) this.sources[idx].url = base + path;
                    this.renderSources();
                    this.updateDestinationFields();
                });
                div.querySelector('.src-url-in').addEventListener('input', (e) => this.sources[idx].url = e.target.value);
                div.querySelector('.src-auth-in').addEventListener('input', (e) => this.sources[idx].auth_token = e.target.value);
            }
            
            this.sourcesContainer.appendChild(div);
        });
    }

    showModal() {
        if (this.modal) {
            this.modal.style.display = 'flex';
            document.documentElement.style.overflow = 'hidden';
            document.body.style.overflow = 'hidden';
        }
    }

    closeModal() {
        if (this.modal) {
            this.modal.style.display = 'none';
            document.documentElement.style.overflow = '';
            document.body.style.overflow = '';
        }
    }

    async saveTemplate() {
        if (!this.templateName) { alert("Template name is required."); return; }

        const payload = {
            name: this.templateName,
            sources: this.sources.map(s => ({
                connectionId: s.connectionId,
                selectedApi: s.selectedApi,
                method: s.method,
                url: s.url,
                auth_token: s.auth_token
            })),
            client_credentials: {
                token: this.globalSecurityTokenModal ? this.globalSecurityTokenModal.value : ''
            },
            execution_mode: this.executionMode,
        };
        
        if (this.executionMode === 'push') {
            payload.destinations = this.pushHandler.getPayload();
        } else if (this.executionMode === 'pull_rest') {
            let restPayload = this.pullRestHandler.getPayload();
            payload.pull_method = restPayload.pull_method;
            payload.destinations = restPayload.destinations;
        } else if (this.executionMode === 'pull_graphql') {
            let gqlPayload = this.pullGraphqlHandler.getPayload();
            payload.destinations = gqlPayload.destinations;
            payload.is_graphql = true;
        }

        try {
            let url = '/api/templates';
            let method = 'POST';
            if (this.templateId && this.mode === 'edit') {
                url = `/api/templates/${this.templateId}`;
                method = 'PUT';
            }
            const res = await fetch(url, { method: method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
            if (res.ok) window.location.reload();
            else alert("Failed to save template");
        } catch (e) {
            alert("Error saving template");
        }
    }
}

window.templateModalController = new TemplateModalController();
