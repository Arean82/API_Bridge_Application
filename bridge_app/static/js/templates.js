document.addEventListener('alpine:init', () => {
Alpine.data('templateManager', (templatesData, connsLookupData) => ({
    templates: templatesData || [],
    connsLookup: connsLookupData || {},
    showModal: false,
    mode: 'edit',
        
        templateId: null,
        templateName: '',
        
        sources: [
            { id: Date.now(), connectionId: '', selectedApi: '', url: '', auth_token: '', availableApis: [] }
        ],
        editSource: false,
        
        clientUrl: '',
        clientAuthType: 'none',
        clientAuthToken: '',
        
        mappedFields: [],
        
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
            // Ensure previously saved mapping values are always available as options
            this.mappedFields.forEach(m => {
                if (m.source_field && !allFields.includes(m.source_field)) {
                    allFields.push(m.source_field);
                }
            });
            return allFields;
        },
        
        addSource() {
            this.sources.push({ id: Date.now(), connectionId: '', selectedApi: '', url: '', auth_token: '', availableApis: [] });
            this.fetchApiDocs(this.sources.length - 1);
        },
        
        removeSource(index) {
            this.sources.splice(index, 1);
        },
        
        updateSourceUrl(idx) {
            let src = this.sources[idx];
            if (!src.selectedApi) {
                src.url = '';
                return;
            }
            // Just populate the path. The user can type the origin if needed.
            src.url = src.selectedApi;
        },
        
        async openEdit(templateId) {
            this.mode = 'edit';
            this.editSource = true;
            await this.populateForm(templateId);
            this.showModal = true;
        },
        
        async openClone(templateId) {
            this.mode = 'clone';
            this.editSource = false;
            await this.populateForm(templateId);
            this.templateName = this.templateName ? this.templateName + " (Copy)" : "New Clone";
            this.templateId = null;
            
            // Blank out client details for clone
            this.clientUrl = '';
            this.clientAuthType = 'none';
            this.clientAuthToken = '';
            
            this.showModal = true;
        },
        
        async populateForm(id) {
            const t = this.templates.find(t => t.id === id);
            if (!t) return;
            
            this.templateId = t.id;
            this.templateName = t.name || '';
            
            if (t.sources && t.sources.length > 0) {
                this.sources = t.sources.map(s => ({
                    id: Date.now() + Math.random(),
                    connectionId: s.connectionId || '',
                    selectedApi: s.selectedApi || '',
                    url: s.url || '',
                    auth_token: s.auth_token || '',
                    availableApis: []
                }));
            } else if (t.partner_url) {
                this.sources = [{
                    id: Date.now(),
                    connectionId: '',
                    selectedApi: '',
                    url: t.partner_url,
                    auth_token: t.partner_auth_token || '',
                    availableApis: []
                }];
            } else {
                this.sources = [{ id: Date.now(), connectionId: '', selectedApi: '', url: '', auth_token: '', availableApis: [] }];
            }
            
            for (let i = 0; i < this.sources.length; i++) {
                await this.fetchApiDocs(i);
            }
            
            this.$nextTick(() => {
                if (t.field_mapping) {
                    try {
                        this.mappedFields = Object.keys(t.field_mapping).map((k, i) => {
                            let sourceField = k;
                            if (!sourceField.startsWith('source_')) {
                                sourceField = `source_0.${sourceField}`;
                            }
                            return {
                                id: Date.now() + i,
                                source_field: sourceField,
                                client_name: t.field_mapping[k]
                            };
                        });
                    } catch(e) {
                        this.mappedFields = [];
                    }
                } else {
                    this.mappedFields = [];
                }
            });
            
            this.clientUrl = t.client_url || '';
            this.clientAuthType = t.client_auth_type || 'none';
            if (t.client_credentials_json) {
                try {
                    const creds = JSON.parse(t.client_credentials_json);
                    this.clientAuthToken = creds.token || '';
                } catch(e) {}
            } else {
                this.clientAuthToken = '';
            }
        },
        
        async fetchApiDocs(idx) {
            let src = this.sources[idx];
            let url = '/api/docs';
            if (src.connectionId) {
                url += `?connection_id=${src.connectionId}`;
            }
            try {
                let res = await fetch(url);
                src.availableApis = await res.json();
                
                // Match selected APIs based on URLs for cloned data if not already set
                if (!src.selectedApi && src.url) {
                    const match = src.availableApis.find(a => src.url.includes(a.path));
                    if (match) {
                        src.selectedApi = match.path;
                    }
                }
            } catch (e) {
                console.error("Failed to load API docs", e);
            }
        },
        
        closeModal() {
            this.showModal = false;
        },
        
        async deleteTemplate(id) {
            if (!confirm("Are you sure you want to delete this template?")) return;
            try {
                const res = await fetch(`/api/templates/${id}`, { method: 'DELETE' });
                if (res.ok) {
                    window.location.reload();
                } else {
                    alert('Error deleting template');
                }
            } catch (err) {
                console.error(err);
                alert('Error deleting template');
            }
        },
        
        addFieldRow() {
            this.mappedFields.push({ id: Date.now(), source_field: '', client_name: '' });
        },
        
        removeFieldRow(index) {
            this.mappedFields.splice(index, 1);
        },
        
        autoFillName(index) {
            if (!this.mappedFields[index].client_name) {
                let row = this.mappedFields[index];
                if (row.source_field) {
                    let parts = row.source_field.split('.');
                    row.client_name = parts[parts.length - 1].replace(/\[\d+\]/g, '');
                }
            }
        },
        
        async saveTemplate() {
            const mappingObj = {};
            this.mappedFields.forEach(f => {
                if (f.source_field && f.client_name) {
                    mappingObj[f.source_field] = f.client_name;
                }
            });
            
            const payload = {
                name: this.templateName,
                sources: this.sources.map(s => ({
                    url: s.url,
                    auth_token: s.auth_token,
                    connectionId: s.connectionId,
                    selectedApi: s.selectedApi
                })),
                field_mapping: mappingObj,
                client_url: this.clientUrl,
                client_auth_type: this.clientAuthType,
                client_credentials: { token: this.clientAuthToken }
            };
            
            let url = '/api/templates';
            let method = 'POST';
            
            if (this.mode === 'edit' && this.templateId) {
                url = `/api/templates/${this.templateId}`;
                method = 'PUT';
            }
            
            try {
                const res = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (res.ok) {
                    window.location.reload();
                } else {
                    alert('Error saving template');
                }
            } catch (err) {
                console.error(err);
                alert('Error saving template');
            }
        }
    }));
});
