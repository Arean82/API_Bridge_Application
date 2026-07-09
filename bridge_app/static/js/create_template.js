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
        
        this.sources = [];
        this.clientUrl = '';
        this.executionMode = 'push';
        this.clientAuthType = 'none';
        this.clientAuthToken = '';
        this.clientTimeout = 30;
        this.clientRetries = 3;
        this.mappedFields = [];
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
        this.clientUrlInput = document.getElementById('clientUrl');
        this.executionModeSelect = document.getElementById('executionMode');
        this.clientUrlWrapper = document.getElementById('clientUrlWrapper');
        this.pullEndpointWrapper = document.getElementById('pullEndpointWrapper');
        this.pullEndpointUrl = document.getElementById('pullEndpointUrl');
        this.scheduleIntervalWrapper = document.getElementById('scheduleInterval')?.parentElement;
        this.clientAuthTypeSelect = document.getElementById('clientAuthType');
        this.clientAuthTokenWrapper = document.getElementById('clientAuthTokenWrapper');
        this.clientAuthTokenInput = document.getElementById('clientAuthToken');
        
        this.addFieldRowBtn = document.getElementById('addFieldRowBtn');
        this.mappingList = document.getElementById('mappingList');
        
        this.scheduleIntervalInput = document.getElementById('scheduleInterval');
        this.clientTimeoutInput = document.getElementById('clientTimeout');
        this.clientRetriesInput = document.getElementById('clientRetries');

        // Value Mapping Modal
        this.valueMappingModal = document.getElementById('valueMappingModal');
        this.valueMappingFieldName = document.getElementById('valueMappingFieldName');
        this.closeValueMappingBtn = document.getElementById('closeValueMappingBtn');
        this.doneValueMappingBtn = document.getElementById('doneValueMappingBtn');
        this.valueMappingRowsContainer = document.getElementById('valueMappingRowsContainer');
        this.addValueMappingRowBtn = document.getElementById('addValueMappingRowBtn');

        this.bindEvents();
    }

    bindEvents() {
        this.clientNameInput.addEventListener('input', (e) => { this.clientName = e.target.value; this.validateForm(); });
        this.templateNameInput.addEventListener('input', (e) => { 
            this.templateName = e.target.value; 
            this.pageTitle.textContent = this.templateName ? 'Edit ' + this.templateName : 'Create New Template';
            this.validateForm();
        });
        this.scheduleImmediatelyInput.addEventListener('change', (e) => { this.scheduleImmediately = e.target.checked; });
        
        this.testMappingBtn.addEventListener('click', () => this.testMapping());
        this.saveBtn.addEventListener('click', () => this.submitForm());
        this.closeTestModalBtn.addEventListener('click', () => this.testModal.style.display = 'none');
        
        this.addSourceBtn.addEventListener('click', () => this.addSource());
        this.toggleLeftFullBtn.addEventListener('click', () => { this.fullLeft = !this.fullLeft; this.renderPanes(); });
        this.toggleRightFullBtn.addEventListener('click', () => { this.fullRight = !this.fullRight; this.renderPanes(); });
        this.fullPaneBackdrop.addEventListener('click', () => { this.fullLeft = false; this.fullRight = false; this.renderPanes(); });

        this.clientUrlInput.addEventListener('input', (e) => { this.clientUrl = e.target.value; });
        if(this.executionModeSelect) this.executionModeSelect.addEventListener('change', (e) => { this.executionMode = e.target.value; this.renderMode(); });
        this.clientAuthTypeSelect.addEventListener('change', (e) => { 
            this.clientAuthType = e.target.value;
            this.clientAuthTokenWrapper.style.display = this.clientAuthType === 'bearer' ? 'block' : 'none';
        });
        this.clientAuthTokenInput.addEventListener('input', (e) => { this.clientAuthToken = e.target.value; });
        
        this.scheduleIntervalInput.addEventListener('input', (e) => { this.scheduleInterval = Math.max(1, parseInt(e.target.value) || 60); });
        this.clientTimeoutInput.addEventListener('input', (e) => { this.clientTimeout = parseInt(e.target.value) || 30; });
        this.clientRetriesInput.addEventListener('input', (e) => { this.clientRetries = parseInt(e.target.value) || 3; });

        this.addFieldRowBtn.addEventListener('click', () => this.addFieldRow());
        
        this.closeValueMappingBtn.addEventListener('click', () => this.valueMappingModal.style.display = 'none');
        this.doneValueMappingBtn.addEventListener('click', () => this.valueMappingModal.style.display = 'none');
        this.addValueMappingRowBtn.addEventListener('click', () => this.addValueMappingRow());
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

    async loadData() {
        if (this.cloneData) {
            let cloneData = this.cloneData;
            this.templateNameInput.value = this.templateName = cloneData.name ? cloneData.name + ' (Copy)' : '';
            this.clientNameInput.value = this.clientName = cloneData.client_name || '';
            this.clientUrlInput.value = this.clientUrl = cloneData.client_url || '';
            this.clientAuthTypeSelect.value = this.clientAuthType = cloneData.client_auth_type || 'none';
            this.clientAuthTokenWrapper.style.display = this.clientAuthType === 'bearer' ? 'block' : 'none';

            if (cloneData.client_credentials_json) {
                try {
                    const creds = JSON.parse(cloneData.client_credentials_json);
                    this.clientAuthTokenInput.value = this.clientAuthToken = creds.token || '';
                    this.clientTimeoutInput.value = this.clientTimeout = creds.timeout || 30;
                    this.clientRetriesInput.value = this.clientRetries = creds.retries !== undefined ? creds.retries : 3;
                } catch(e) {}
            } else if (cloneData.client_credentials) {
                this.clientAuthTokenInput.value = this.clientAuthToken = cloneData.client_credentials.token || '';
                this.clientTimeoutInput.value = this.clientTimeout = cloneData.client_credentials.timeout || 30;
                this.clientRetriesInput.value = this.clientRetries = cloneData.client_credentials.retries !== undefined ? cloneData.client_credentials.retries : 3;
            }

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

            if (cloneData.field_mapping) {
                if (Array.isArray(cloneData.field_mapping)) {
                    cloneData.field_mapping.forEach((mapping, i) => {
                        this.mappedFields.push({
                            id: Date.now() + i,
                            source_field: mapping.source || '',
                            client_name: mapping.target || '',
                            value_mapping: mapping.value_mapping || []
                        });
                    });
                } else {
                    Object.entries(cloneData.field_mapping).forEach(([source_field, client_name], i) => {
                        let sf = source_field;
                        if (!sf.startsWith('source_')) sf = `source_0.${sf}`;
                        this.mappedFields.push({ id: Date.now() + i, source_field: sf, client_name: client_name, value_mapping: [] });
                    });
                }
            }
        }

        if (this.sources.length === 0) {
            this.sources.push({ id: Date.now(), connectionId: '', selectedApi: '', url: '', auth_token: '', availableApis: [] });
        }

        for (let i = 0; i < this.sources.length; i++) {
            await this.fetchApiDocs(i, false);
        }

        this.pageTitle.textContent = this.templateName ? 'Edit ' + this.templateName : 'Create New Template';
        this.validateForm();
        this.renderSources();
        this.renderFields();
        
        setTimeout(() => {
            if (window.Sortable) {
                Sortable.create(this.mappingList, {
                    handle: '.cursor-move',
                    animation: 150,
                    onEnd: (evt) => {
                        const item = this.mappedFields.splice(evt.oldIndex, 1)[0];
                        this.mappedFields.splice(evt.newIndex, 0, item);
                        this.renderFields();
                    }
                });
            }
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
                this.renderFields();
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
        this.renderFields();
    }

    addFieldRow() {
        this.mappedFields.push({ id: Date.now() + Math.random().toString(), source_field: '', client_name: '', value_mapping: [] });
        this.renderFields();
    }

    removeFieldRow(index) {
        this.mappedFields.splice(index, 1);
        this.renderFields();
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
        this.mappedFields.forEach(m => {
            if (m.source_field && !allFields.includes(m.source_field)) {
                allFields.push(m.source_field);
            }
        });
        return allFields;
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
                        <label class="block text-sm font-medium mb-1">Swagger Connection</label>
                        <select class="theme-input w-full p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 src-conn-sel" data-idx="${idx}">
                            <option value="">-- Select Connection --</option>
                            ${this.swaggerConnections.map(c => `<option value="${c.id}" ${src.connectionId == c.id ? 'selected' : ''}>${c.name}</option>`).join('')}
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1">Select API Endpoint</label>
                        <select class="theme-input w-full p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 src-api-sel" data-idx="${idx}" ${!src.availableApis || src.availableApis.length === 0 ? 'disabled' : ''}>
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
            div.querySelector('.src-conn-sel').addEventListener('change', (e) => { this.sources[idx].connectionId = e.target.value; this.fetchApiDocs(idx); });
            div.querySelector('.src-api-sel').addEventListener('change', (e) => { 
                this.sources[idx].selectedApi = e.target.value; 
                let conn = this.swaggerConnections.find(c => c.id == this.sources[idx].connectionId);
                let base = conn && conn.url ? new URL(conn.url).origin : '';
                if (base && base.endsWith('/')) base = base.slice(0, -1);
                if (e.target.value) this.sources[idx].url = base + e.target.value;
                this.renderSources();
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
            div.querySelector('.field-rm-btn').addEventListener('click', (e) => { e.preventDefault(); this.removeFieldRow(idx); });
            div.querySelector('.field-val-map-btn').addEventListener('click', (e) => { e.preventDefault(); this.openValueMapping(idx); });

            this.mappingList.appendChild(div);
        });
    }

    openValueMapping(index) {
        this.activeMappingIndex = index;
        if (!this.mappedFields[index].value_mapping) this.mappedFields[index].value_mapping = [];
        this.valueMappingFieldName.textContent = this.mappedFields[index].source_field || 'Field';
        this.renderValueMappingRows();
        this.valueMappingModal.style.display = 'flex';
    }

    renderValueMappingRows() {
        this.valueMappingRowsContainer.innerHTML = '';
        let mappings = this.mappedFields[this.activeMappingIndex].value_mapping;
        mappings.forEach((vm, vmIdx) => {
            const div = document.createElement('div');
            div.className = 'grid grid-cols-12 gap-2 items-center bg-black/5 p-2 rounded mb-2';
            div.innerHTML = `
                <div class="col-span-3"><input type="text" class="theme-input w-full p-1.5 text-sm focus:outline-none vm-src-val" value="${vm.source_val}" placeholder="on"></div>
                <div class="col-span-2">
                    <select class="theme-input w-full p-1.5 text-xs focus:outline-none vm-src-type">
                        <option value="string" ${vm.source_type === 'string' ? 'selected' : ''}>String</option>
                        <option value="int" ${vm.source_type === 'int' ? 'selected' : ''}>Integer</option>
                    </select>
                </div>
                <div class="col-span-1 text-center font-bold theme-text-muted">&rarr;</div>
                <div class="col-span-3"><input type="text" class="theme-input w-full p-1.5 text-sm focus:outline-none vm-tgt-val" value="${vm.target_val}" placeholder="1"></div>
                <div class="col-span-2">
                    <select class="theme-input w-full p-1.5 text-xs focus:outline-none vm-tgt-type">
                        <option value="string" ${vm.target_type === 'string' ? 'selected' : ''}>String</option>
                        <option value="int" ${vm.target_type === 'int' ? 'selected' : ''}>Integer</option>
                    </select>
                </div>
                <div class="col-span-1 text-center">
                    <button class="text-red-500 hover:text-red-700 text-lg font-bold vm-rm-btn">&times;</button>
                </div>
            `;
            
            div.querySelector('.vm-src-val').addEventListener('input', (e) => vm.source_val = e.target.value);
            div.querySelector('.vm-src-type').addEventListener('change', (e) => vm.source_type = e.target.value);
            div.querySelector('.vm-tgt-val').addEventListener('input', (e) => vm.target_val = e.target.value);
            div.querySelector('.vm-tgt-type').addEventListener('change', (e) => vm.target_type = e.target.value);
            div.querySelector('.vm-rm-btn').addEventListener('click', () => { mappings.splice(vmIdx, 1); this.renderValueMappingRows(); });
            
            this.valueMappingRowsContainer.appendChild(div);
        });
    }

    addValueMappingRow() {
        if (this.activeMappingIndex !== null) {
            this.mappedFields[this.activeMappingIndex].value_mapping.push({ source_val: '', source_type: 'string', target_val: '', target_type: 'string' });
            this.renderValueMappingRows();
        }
    }

    testMapping() {
        const samplePayload = {};
        this.mappedFields.forEach(f => {
            if (f.source_field && f.client_name) {
                samplePayload[f.client_name] = `[Sample value from ${f.source_field}]`;
            }
        });

        this.testPayloadPre.textContent = Object.keys(samplePayload).length ? JSON.stringify(samplePayload, null, 2) : '{\n  "message": "No fields mapped yet."\n}';
        this.testModal.style.display = 'flex';
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
                    url: s.url,
                    auth_token: s.auth_token
                })),
                client_url: this.clientUrl,
            execution_mode: this.executionMode,
                client_auth_type: this.clientAuthType,
                client_credentials: {
                    token: this.clientAuthType === 'bearer' ? this.clientAuthToken : null,
                    timeout: parseInt(this.clientTimeout) || 30,
                    retries: parseInt(this.clientRetries) || 3
                },
                field_mapping: this.mappedFields.map(f => ({
                    source: f.source_field,
                    target: f.client_name,
                    value_mapping: f.value_mapping || []
                })).filter(f => f.source && f.target)
            };

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
