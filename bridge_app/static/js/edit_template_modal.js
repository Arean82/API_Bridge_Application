class TemplateModalController {
    constructor() {
        this.mode = 'edit';
        this.templateId = null;
        this.templateName = '';
        this.sources = [];
        this.editSource = false;
        this.clientUrl = '';
        this.clientAuthType = 'none';
        this.clientAuthToken = '';
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
        this.clientUrlInput = document.getElementById('clientUrl');
        this.clientAuthTypeSelect = document.getElementById('clientAuthType');
        this.clientAuthTokenContainer = document.getElementById('clientAuthTokenWrapper');
        this.clientAuthTokenInput = document.getElementById('clientAuthToken');
        this.addFieldBtn = document.getElementById('addFieldRowBtn');
        this.mappingContainer = document.getElementById('mappedFieldsContainer');
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
        this.addFieldBtn.addEventListener('click', () => this.addFieldRow());
        this.templateNameInput.addEventListener('input', (e) => this.templateName = e.target.value);
        this.clientUrlInput.addEventListener('input', (e) => this.clientUrl = e.target.value);
        this.clientAuthTypeSelect.addEventListener('change', (e) => {
            this.clientAuthType = e.target.value;
            this.clientAuthTokenContainer.style.display = this.clientAuthType === 'bearer' ? 'block' : 'none';
        });
        this.clientAuthTokenInput.addEventListener('input', (e) => this.clientAuthToken = e.target.value);
        this.editSourceCheckbox.addEventListener('change', (e) => {
            this.editSource = e.target.checked;
            this.renderSources();
        });
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
        this.clientUrl = '';
        this.clientAuthType = 'none';
        this.clientAuthToken = '';
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

        if (t.field_mapping) {
            try {
                if (Array.isArray(t.field_mapping)) {
                    this.mappedFields = t.field_mapping.map((m, i) => ({
                        id: Date.now() + i,
                        source_field: m.source.startsWith('source_') ? m.source : `source_0.${m.source}`,
                        client_name: m.target,
                        value_mapping: m.value_mapping || []
                    }));
                } else {
                    this.mappedFields = Object.keys(t.field_mapping).map((k, i) => {
                        let sf = k.startsWith('source_') ? k : `source_0.${k}`;
                        return { id: Date.now() + i, source_field: sf, client_name: t.field_mapping[k], value_mapping: [] };
                    });
                }
            } catch (e) {
                this.mappedFields = [];
            }
        } else {
            this.mappedFields = [];
        }

        this.clientUrl = t.client_url || '';
        this.clientAuthType = t.client_auth_type || 'none';
        if (t.client_credentials_json) {
            try {
                const creds = JSON.parse(t.client_credentials_json);
                this.clientAuthToken = creds.token || '';
            } catch (e) { }
        } else if (t.client_credentials) {
            this.clientAuthToken = t.client_credentials.token || '';
        }
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
        this.mappedFields.push({ id: Date.now(), source_field: '', client_name: '', value_mapping: [] });
        this.renderFields();
    }

    removeFieldRow(index) {
        this.mappedFields.splice(index, 1);
        this.renderFields();
    }

    autoFillName(index) {
        let row = this.mappedFields[index];
        if (!row.client_name && row.source_field) {
            let parts = row.source_field.split('.');
            row.client_name = parts[parts.length - 1].replace(/\[\d+\]/g, '');
            this.renderFields();
        }
    }

    renderAll() {
        this.modalTitle.textContent = this.mode === 'edit' ? 'Edit Template' : 'Clone Template';
        this.templateNameInput.value = this.templateName;
        this.editSourceWrapper.style.display = this.mode === 'clone' ? 'flex' : 'none';
        this.editSourceCheckbox.checked = this.editSource;
        this.addEndpointBtn.style.display = this.editSource ? 'inline-block' : 'none';
        
        this.clientUrlInput.value = this.clientUrl;
        this.clientAuthTypeSelect.value = this.clientAuthType;
        this.clientAuthTokenContainer.style.display = this.clientAuthType === 'bearer' ? 'block' : 'none';
        this.clientAuthTokenInput.value = this.clientAuthToken;
        
        this.renderSources();
        this.renderFields();
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
            div.querySelector('.src-conn-sel').addEventListener('change', (e) => {
                this.sources[idx].connectionId = e.target.value;
                this.fetchApiDocs(idx);
            });
            div.querySelector('.src-api-sel').addEventListener('change', (e) => {
                this.sources[idx].selectedApi = e.target.value;
                if (e.target.value) this.sources[idx].url = e.target.value;
                this.renderSources();
            });
            div.querySelector('.src-url-in').addEventListener('input', (e) => this.sources[idx].url = e.target.value);
            div.querySelector('.src-auth-in').addEventListener('input', (e) => this.sources[idx].auth_token = e.target.value);
            
            this.sourcesContainer.appendChild(div);
        });
    }

    renderFields() {
        this.mappingContainer.innerHTML = '';
        if (this.mappedFields.length === 0) {
            this.mappingContainer.innerHTML = '<div class="text-center py-6 text-sm theme-text-muted bg-gray-50 rounded-lg border border-black/10 border-dashed">No fields mapped.</div>';
            return;
        }
        const availableFields = this.currentApiFields;
        
        this.mappedFields.forEach((row, idx) => {
            const div = document.createElement('div');
            div.className = 'flex items-center gap-3 bg-gray-50 p-3 rounded-lg border border-black/10 mb-2';
            div.innerHTML = `
                <div class="flex-1">
                    <select class="theme-input w-full p-2 text-sm field-src-sel" data-idx="${idx}">
                        <option value="">-- Source Field --</option>
                        ${availableFields.map(opt => `<option value="${opt}" ${row.source_field === opt ? 'selected' : ''}>${opt}</option>`).join('')}
                    </select>
                </div>
                <div class="flex-none theme-text-muted"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg></div>
                <div class="flex-1">
                    <input type="text" class="theme-input w-full p-2 text-sm field-tgt-in" data-idx="${idx}" value="${row.client_name}" placeholder="Target Field">
                </div>
                <button class="text-red-500 hover:text-red-700 p-1 field-rm-btn" data-idx="${idx}">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                </button>
            `;
            
            div.querySelector('.field-src-sel').addEventListener('change', (e) => {
                this.mappedFields[idx].source_field = e.target.value;
                this.autoFillName(idx);
            });
            div.querySelector('.field-tgt-in').addEventListener('input', (e) => {
                this.mappedFields[idx].client_name = e.target.value;
            });
            div.querySelector('.field-rm-btn').addEventListener('click', (e) => {
                e.preventDefault();
                this.removeFieldRow(parseInt(e.currentTarget.dataset.idx));
            });
            this.mappingContainer.appendChild(div);
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

        const mappingArray = this.mappedFields.map(f => ({
            source: f.source_field,
            target: f.client_name,
            value_mapping: f.value_mapping || []
        })).filter(f => f.source && f.target);

        const payload = {
            name: this.templateName,
            sources: this.sources.map(s => ({ connectionId: s.connectionId, selectedApi: s.selectedApi, url: s.url, auth_token: s.auth_token })),
            client_url: this.clientUrl,
            client_auth_type: this.clientAuthType,
            client_credentials: { token: this.clientAuthToken, timeout: 30, retries: 3 },
            field_mapping: mappingArray
        };

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
