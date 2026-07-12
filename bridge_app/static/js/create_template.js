class CreateTemplateController {
    constructor() {
        this.container = document.getElementById('createTemplateContainer');
        if (!this.container) return;

        let cloneDataRaw = this.container.getAttribute('data-clone');
        let connsRaw = this.container.getAttribute('data-conns');
        
        try { this.cloneData = cloneDataRaw && cloneDataRaw !== 'null' ? JSON.parse(cloneDataRaw) : null; } catch(e) { this.cloneData = null; }
        try { this.swaggerConnections = connsRaw ? JSON.parse(connsRaw) : []; } catch(e) { this.swaggerConnections = []; }

        this.clientName = '';
        this.templateName = '';
        this.scheduleImmediately = false;
        
        this.executionMode = 'push';
        this.clientTimeout = 30;
        this.clientRetries = 3;
        this.scheduleInterval = 60;

        this.fullLeft = false;
        this.fullRight = false;

        this.initDOM();
        this.loadData();
    }

    initDOM() {
        this.pageTitle = document.getElementById('pageTitle');
        this.clientNameInput = document.getElementById('clientName');
        this.templateNameInput = document.getElementById('templateName');
        this.scheduleImmediatelyInput = document.getElementById('scheduleImmediately');
        this.testMappingBtn = document.getElementById('testMappingBtn');
        this.saveBtn = document.getElementById('saveBtn');
        this.saveBtnText = document.getElementById('saveBtnText');
        this.statusMessage = document.getElementById('statusMessage');

        this.testModal = document.getElementById('testModal');
        this.closeTestModalBtn = document.getElementById('closeTestModalBtn');
        this.testPayloadPre = document.getElementById('testPayloadPre');

        this.fullPaneBackdrop = document.getElementById('fullPaneBackdrop');

        // Partner Pane
        this.partnerPane = document.getElementById('partnerPane');
        this.addSourceBtn = document.getElementById('addSourceBtn');
        this.toggleLeftFullBtn = document.getElementById('toggleLeftFullBtn');
        this.sourcesContainer = document.getElementById('sourcesContainer');

        // Client Pane
        this.clientPane = document.getElementById('clientPane');
        this.toggleRightFullBtn = document.getElementById('toggleRightFullBtn');
        
        // Execution Mode & JS Handlers
        this.executionModeSelect = document.getElementById('executionMode');
        
        this.pushHandler = new window.PushHandler('destinationsContainer', 'addDestinationBtn');
        this.pullRestHandler = new window.PullRestHandler('restEndpointsContainer', 'addRestEndpointBtn');
        this.pullGraphqlHandler = new window.PullGraphqlHandler('graphqlEndpointsContainer', 'addGraphqlEndpointBtn');
        
        this.scheduleIntervalWrapper = document.getElementById('scheduleInterval')?.parentElement;
        

        
        this.scheduleIntervalInput = document.getElementById('scheduleInterval');
        this.clientTimeoutInput = document.getElementById('clientTimeout');
        this.clientRetriesInput = document.getElementById('clientRetries');
        
        this.globalTokenWrapper = document.getElementById('globalTokenWrapper');
        this.globalSecurityToken = document.getElementById('globalSecurityToken');
        this.toggleGlobalTokenBtn = document.getElementById('toggleGlobalTokenBtn');

        // Value Mapping Modal


        this.bindEvents();
    }

    bindEvents() {
        this.clientNameInput.addEventListener('input', (e) => { this.clientName = e.target.value; this.validateForm(); });
        this.templateNameInput.addEventListener('input', (e) => { 
            this.templateName = e.target.value; 
            this.pageTitle.textContent = this.templateName ? 'Edit ' + this.templateName : 'Create New Template';
            if (this.pullRestHandler) this.pullRestHandler.setEndpointUrl(this.templateName);
            if (this.pullGraphqlHandler) this.pullGraphqlHandler.setEndpointUrl(this.templateName);
            this.validateForm();
        });
        this.scheduleImmediatelyInput.addEventListener('change', (e) => { this.scheduleImmediately = e.target.checked; });
        
        if (this.toggleGlobalTokenBtn && this.globalSecurityToken) {
            this.toggleGlobalTokenBtn.addEventListener('click', () => {
                const type = this.globalSecurityToken.getAttribute('type') === 'password' ? 'text' : 'password';
                this.globalSecurityToken.setAttribute('type', type);
                this.toggleGlobalTokenBtn.innerHTML = type === 'password' ? 
                    `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path></svg>` : 
                    `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"></path></svg>`;
            });
        }
        
        this.testMappingBtn.addEventListener('click', () => this.testMapping());
        this.saveBtn.addEventListener('click', () => this.submitForm());
        this.closeTestModalBtn.addEventListener('click', () => this.testModal.style.display = 'none');
        this.addSourceBtn.addEventListener('click', () => this.addSource());
        this.toggleLeftFullBtn.addEventListener('click', () => { this.fullLeft = !this.fullLeft; this.renderPanes(); });
        this.toggleRightFullBtn.addEventListener('click', () => { this.fullRight = !this.fullRight; this.renderPanes(); });
        this.fullPaneBackdrop.addEventListener('click', () => { this.fullLeft = false; this.fullRight = false; this.renderPanes(); });

        if(this.executionModeSelect) this.executionModeSelect.addEventListener('change', (e) => { this.executionMode = e.target.value; this.renderMode(); });
        
        
        this.scheduleIntervalInput.addEventListener('input', (e) => { this.scheduleInterval = Math.max(1, parseInt(e.target.value) || 60); });
        this.clientTimeoutInput.addEventListener('input', (e) => { this.clientTimeout = parseInt(e.target.value) || 30; });
        this.clientRetriesInput.addEventListener('input', (e) => { this.clientRetries = parseInt(e.target.value) || 3; });


    }

    validateForm() {
        this.saveBtn.disabled = !this.templateName || !this.clientName;
    }

    renderPanes() {
        this.partnerPane.className = `theme-panel flex flex-col ${this.fullLeft ? 'fixed inset-4 z-50' : ''}`;
        this.clientPane.className = `theme-panel flex flex-col ${this.fullRight ? 'fixed inset-4 z-50' : 'w-2/3'}`;
        this.fullPaneBackdrop.style.display = (this.fullLeft || this.fullRight) ? 'block' : 'none';
        
        if (this.fullLeft || this.fullRight) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }
    }

    renderMode() {
        const blocks = [document.getElementById('pushConfigBlock'), document.getElementById('pullRestConfigBlock'), document.getElementById('pullGraphqlConfigBlock')];
        blocks.forEach(b => { if(b) b.style.display = 'none'; });
        
        if (this.executionMode === 'push') {
            document.getElementById('pushConfigBlock').style.display = 'block';
            if (this.scheduleIntervalWrapper) this.scheduleIntervalWrapper.style.display = 'block';
            if (this.scheduleImmediatelyInput) this.scheduleImmediatelyInput.parentElement.style.display = 'flex';
            if (this.globalTokenWrapper) this.globalTokenWrapper.style.display = 'none';
        } else {
            if (this.scheduleIntervalWrapper) this.scheduleIntervalWrapper.style.display = 'none';
            if (this.scheduleImmediatelyInput) this.scheduleImmediatelyInput.parentElement.style.display = 'none';
            if (this.globalTokenWrapper) this.globalTokenWrapper.style.display = 'block';
            
            if (this.executionMode === 'pull_rest') {
                document.getElementById('pullRestConfigBlock').style.display = 'block';
            } else if (this.executionMode === 'pull_graphql') {
                document.getElementById('pullGraphqlConfigBlock').style.display = 'block';
            }
        }
    }

    async loadData() {
        if (this.cloneData) {
            let cloneData = this.cloneData;
            this.templateNameInput.value = this.templateName = cloneData.name ? cloneData.name + ' (Copy)' : '';
            this.executionMode = cloneData.execution_mode || 'push';

            if (cloneData.client_credentials_json) {
                try {
                    const creds = JSON.parse(cloneData.client_credentials_json);
                    this.clientTimeoutInput.value = this.clientTimeout = creds.timeout || 30;
                    this.clientRetriesInput.value = this.clientRetries = creds.retries !== undefined ? creds.retries : 3;
                    if (this.globalSecurityToken) this.globalSecurityToken.value = creds.token || '';
                } catch(e) {}
            } else if (cloneData.client_credentials) {
                this.clientTimeoutInput.value = this.clientTimeout = cloneData.client_credentials.timeout || 30;
                this.clientRetriesInput.value = this.clientRetries = cloneData.client_credentials.retries !== undefined ? cloneData.client_credentials.retries : 3;
                if (this.globalSecurityToken) this.globalSecurityToken.value = cloneData.client_credentials.token || '';
            }

            this.pushHandler.loadDestinations(cloneData.destinations || []);
            this.pullRestHandler.setEndpointUrl(this.templateName);
            this.pullRestHandler.loadData(cloneData.destinations || []);
            this.pullGraphqlHandler.setEndpointUrl(this.templateName);
            this.pullGraphqlHandler.loadData(cloneData.destinations || []);

            if (cloneData.sources && cloneData.sources.length > 0) {
                this.sources = cloneData.sources.map(s => ({
                    id: Date.now() + Math.random(),
                    connectionId: s.connectionId ? parseInt(s.connectionId) : '',
                    selectedApi: s.selectedApi || '',
                    url: s.url || '',
                    auth_token: s.auth_token || '',
                    availableApis: []
                }));
            } else if (cloneData.partner_url) {
                this.sources = [{ id: Date.now(), connectionId: '', selectedApi: '', url: cloneData.partner_url, auth_token: cloneData.partner_auth_token || '', availableApis: [] }];
            }

        }

        if (!this.sources || this.sources.length === 0) {
            this.sources = [{ id: Date.now(), connectionId: '', selectedApi: '', url: '', auth_token: '', availableApis: [] }];
        }

        for (let i = 0; i < this.sources.length; i++) {
            await this.fetchApiDocs(i, false);
        }

        this.pageTitle.textContent = this.templateName ? 'Edit ' + this.templateName : 'Create New Template';
        
        if (this.executionModeSelect) this.executionModeSelect.value = this.executionMode;
        this.renderMode();
        this.validateForm();
        this.renderSources();
        this.updateDestinationFields();
        
        setTimeout(() => {
        }, 500);
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

    removeSource(idx) {
        this.sources.splice(idx, 1);
        this.renderSources();
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
            div.className = 'relative p-5 border border-black/10 rounded-lg bg-black/5 shadow-sm';
            
            let html = `
                ${this.sources.length > 1 ? `<button class="absolute top-3 right-3 text-red-400 hover:text-red-600 remove-src-btn" data-idx="${idx}"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg></button>` : ''}
                <h4 class="font-bold text-sm mb-4 theme-text-muted">ENDPOINT <span>${idx + 1}</span></h4>
                <div class="space-y-4">
                    <div>
                        <div class="flex justify-between items-center mb-1">
                            <label class="block text-sm font-medium">Swagger Connection</label>
                            <button class="text-indigo-600 hover:text-indigo-800 text-xs font-semibold new-conn-btn" type="button">+ New Connection (JSON/URL)</button>
                        </div>
                        <select class="theme-input w-full p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 src-conn-sel" data-idx="${idx}">
                            <option value="">-- Select Connection --</option>
                            ${this.swaggerConnections.map(c => `<option value="${c.id}" ${src.connectionId == c.id ? 'selected' : ''}>${c.name}</option>`).join('')}
                        </select>
                    </div>
                    <div class="col-span-2">
                        <label class="block text-sm font-medium mb-1">Select API Endpoint</label>
                        <select class="theme-input w-full p-2.5 text-sm src-api-sel" data-idx="${idx}" ${!src.availableApis || src.availableApis.length === 0 ? 'disabled' : ''}>
                            <option value="">-- Choose API --</option>
                            ${(src.availableApis || []).map(api => `<option value="${api.path}" ${src.selectedApi === api.path ? 'selected' : ''}>${api.name} (${api.path})</option>`).join('')}
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1">Source URL</label>
                        <input type="text" class="theme-input w-full p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 src-url-in" data-idx="${idx}" value="${src.url}" placeholder="https://api.partner.com/v1/data">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1">Source Auth Key (Bearer)</label>
                        <input type="password" class="theme-input w-full p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 src-auth-in" data-idx="${idx}" value="${src.auth_token}" placeholder="Optional">
                    </div>
                </div>
            `;
            div.innerHTML = html;
            
            if (this.sources.length > 1) {
                div.querySelector('.remove-src-btn').addEventListener('click', (e) => { e.preventDefault(); this.removeSource(parseInt(e.currentTarget.dataset.idx)); });
            }
            div.querySelector('.new-conn-btn').addEventListener('click', (e) => { 
                e.preventDefault();
                if(window.connectionsManager) {
                    window.connectionsManager.newConn = window.connectionsManager.getEmptyConn();
                    window.connectionsManager.populateForm();
                    window.connectionsManager.openModal();
                } else {
                    alert("Connections manager not loaded.");
                }
            });
            div.querySelector('.src-conn-sel').addEventListener('change', (e) => { this.sources[idx].connectionId = e.target.value; this.fetchApiDocs(idx); });
            div.querySelector('.src-api-sel').addEventListener('change', (e) => { 
                let path = e.target.value;
                this.sources[idx].selectedApi = path || ''; 
                let conn = this.swaggerConnections.find(c => c.id == this.sources[idx].connectionId);
                let base = conn && conn.url ? new URL(conn.url).origin : '';
                if (base && base.endsWith('/')) base = base.slice(0, -1);
                if (path) this.sources[idx].url = base + path;
                this.renderSources();
                this.updateDestinationFields();
            });
            div.querySelector('.src-url-in').addEventListener('input', (e) => this.sources[idx].url = e.target.value);
            div.querySelector('.src-auth-in').addEventListener('input', (e) => this.sources[idx].auth_token = e.target.value);
            
            this.sourcesContainer.appendChild(div);
        });
    }

    renderFields() {
        this.mappingList.innerHTML = '';
        if (this.mappedFields.length === 0) {
            this.mappingList.innerHTML = '<div class="text-center py-8 text-sm theme-text-muted">Click "+ Add Field" to start mapping.</div>';
            return;
        }

        const availableFields = this.currentApiFields;
        this.mappedFields.forEach((row, idx) => {
            const div = document.createElement('div');
            div.className = 'mapping-row flex items-center gap-3 theme-panel p-3 rounded';
            div.style.boxShadow = '0 1px 2px rgba(0,0,0,0.05)';
            div.dataset.id = row.id;
            
            div.innerHTML = `
                <div class="cursor-move theme-text-muted hover:opacity-100 px-1">
                    <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"></path></svg>
                </div>
                <div class="flex-1">
                    <select class="theme-input w-full p-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 field-src-sel" data-idx="${idx}">
                        <option value="">-- Select Source Field --</option>
                        ${availableFields.map(opt => `<option value="${opt}" ${row.source_field === opt ? 'selected' : ''}>${opt}</option>`).join('')}
                    </select>
                </div>
                <div class="flex-none theme-text-muted">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                </div>
                <div class="flex-1">
                    <input type="text" class="theme-input w-full p-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 field-tgt-in" data-idx="${idx}" value="${row.client_name}" placeholder="Target Field Name">
                </div>
                <button class="text-blue-500 hover:text-blue-700 text-sm font-medium px-2 py-1 border border-blue-200 rounded whitespace-nowrap bg-blue-50 dark:bg-blue-900/30 dark:border-blue-800 field-val-map-btn" data-idx="${idx}" title="Map Values">{=}</button>
                <button class="text-red-500 hover:text-red-700 p-1 field-rm-btn" data-idx="${idx}">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                </button>
            `;
            
            div.querySelector('.field-src-sel').addEventListener('change', (e) => {
                this.mappedFields[idx].source_field = e.target.value;
                if (!this.mappedFields[idx].client_name && e.target.value) {
                    let parts = e.target.value.split('.');
                    this.mappedFields[idx].client_name = parts[parts.length - 1].replace(/\[\d+\]/g, '');
                    this.renderFields();
                }
            });
            div.querySelector('.field-tgt-in').addEventListener('input', (e) => { this.mappedFields[idx].client_name = e.target.value; });
            div.querySelector('.field-rm-btn').addEventListener('click', (e) => { e.preventDefault(); this.mappedFields.splice(idx, 1); this.renderFields(); });
            div.querySelector('.field-val-map-btn').addEventListener('click', (e) => { e.preventDefault(); this.openValueMapping(idx); });

            this.mappingList.appendChild(div);
        });
    }



    async testMapping() {
        this.testMappingBtn.disabled = true;
        this.testMappingBtn.textContent = 'Testing...';
        
        try {
            let mapping = [];
            if (this.executionMode === 'push') {
                const destinations = this.pushHandler.getPayload();
                if (destinations && destinations.length > 0) {
                    mapping = destinations[0].field_mapping || [];
                }
            } else if (this.executionMode === 'pull_rest') {
                const destinations = this.pullRestHandler.getPayload().destinations;
                if (destinations && destinations.length > 0) {
                    mapping = destinations[0].field_mapping || [];
                }
            } else if (this.executionMode === 'pull_graphql') {
                const destinations = this.pullGraphqlHandler.getPayload().destinations;
                if (destinations && destinations.length > 0) {
                    mapping = destinations[0].field_mapping || [];
                }
            }

            const response = await fetch('/api/test_mapping', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mapping: mapping })
            });

            if (response.ok) {
                const data = await response.json();
                this.testPayloadPre.textContent = JSON.stringify(data, null, 2);
                this.testModal.style.display = 'flex';
            } else {
                this.showStatus('Failed to generate sample mapping', true);
            }
        } catch (error) {
            this.showStatus('Error testing mapping: ' + error.message, true);
        } finally {
            this.testMappingBtn.disabled = false;
            this.testMappingBtn.textContent = 'Test Mapping';
        }
    }

    showStatus(msg, isError) {
        this.statusMessage.style.display = 'block';
        this.statusMessage.className = `mb-4 p-4 rounded ${isError ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`;
        this.statusMessage.textContent = msg;
    }

    async submitForm() {
        if (!this.templateName || !this.clientName) {
            this.showStatus("Client Name and Template Name are required", true);
            return;
        }

        this.saveBtn.disabled = true;
        this.saveBtnText.textContent = 'Saving...';
        this.statusMessage.style.display = 'none';

        try {
            const payload = {
                client_name: this.clientName,
                name: this.templateName,
                schedule_immediately: this.scheduleImmediately,
                schedule_interval: parseInt(this.scheduleInterval),
                sources: this.sources.map(s => ({
                    connectionId: s.connectionId,
                    selectedApi: s.selectedApi,
                    method: s.method,
                    url: s.url,
                    auth_token: s.auth_token
                })),
                execution_mode: this.executionMode,
                client_credentials: {
                    timeout: parseInt(this.clientTimeout) || 30,
                    retries: parseInt(this.clientRetries) || 3,
                    token: this.globalSecurityToken ? this.globalSecurityToken.value : ''
                }
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

            const response = await fetch('/api/templates', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                this.showStatus('Template created successfully!', false);
                setTimeout(() => {
                    window.location.href = this.scheduleImmediately ? '/' : '/templates';
                }, 1500);
            } else {
                const error = await response.json();
                throw new Error(error.message || 'Failed to save template');
            }
        } catch (error) {
            this.showStatus(error.message, true);
            this.saveBtn.disabled = false;
            this.saveBtnText.textContent = 'Save';
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.createTemplateController = new CreateTemplateController();
});
