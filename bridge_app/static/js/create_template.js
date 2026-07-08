document.addEventListener('alpine:init', () => {
    Alpine.data('createTemplate', (cloneData) => ({
        clientName: '',
        templateName: '',
        scheduleImmediately: false,

        showTestModal: false,
        testPayloadJSON: '',

        fullLeft: false,
        fullRight: false,

        availableApis: [],

        sources: [
            { id: Date.now(), selectedApi: '', url: '', auth_token: '' }
        ],

        get currentApiFields() {
            let allFields = [];
            this.sources.forEach((src, idx) => {
                let api = this.availableApis.find(a => a.path === src.selectedApi);
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
            this.sources.push({ id: Date.now(), selectedApi: '', url: '', auth_token: '' });
        },

        removeSource(index) {
            this.sources.splice(index, 1);
        },

        clientUrl: '',
        clientAuthType: 'none',
        clientAuthToken: '',

        mappedFields: [],
        scheduleInterval: 60,

        isSubmitting: false,
        message: '',
        isError: false,

        async init() {
            await this.fetchApiDocs();
            if (cloneData) {
                this.templateName = cloneData.name ? cloneData.name + ' (Copy)' : '';
                this.clientName = cloneData.client_name || '';
                this.clientUrl = cloneData.client_url || '';
                this.clientAuthType = cloneData.client_auth_type || 'none';
                
                if (cloneData.client_credentials_json) {
                    try {
                        const creds = JSON.parse(cloneData.client_credentials_json);
                        this.clientAuthToken = creds.token || '';
                    } catch(e) {}
                } else if (cloneData.client_credentials) {
                    this.clientAuthToken = cloneData.client_credentials.token || '';
                }
                if (cloneData.sources && cloneData.sources.length > 0) {
                    this.sources = cloneData.sources.map(s => ({
                        id: Date.now() + Math.random(),
                        selectedApi: '',
                        url: s.url || '',
                        auth_token: s.auth_token || ''
                    }));
                } else if (cloneData.partner_url) {
                    this.sources = [{
                        id: Date.now(),
                        selectedApi: '',
                        url: cloneData.partner_url,
                        auth_token: cloneData.partner_auth_token || ''
                    }];
                }

                if (cloneData.field_mapping) {
                    this.$nextTick(() => {
                        Object.entries(cloneData.field_mapping).forEach(([source_field, client_name], i) => {
                            let sf = source_field;
                            if (!sf.startsWith('source_')) {
                                sf = `source_0.${sf}`;
                            }
                            this.mappedFields.push({
                                id: Date.now() + i,
                                source_field: sf,
                                client_name: client_name
                            });
                        });
                    });
                }
            }
            this.$nextTick(() => {
                let el = document.getElementById('mapping-list');
                if (el) {
                    Sortable.create(el, {
                        handle: '.cursor-move',
                        animation: 150,
                        onEnd: (evt) => {
                            const item = this.mappedFields.splice(evt.oldIndex, 1)[0];
                            this.mappedFields.splice(evt.newIndex, 0, item);
                        }
                    });
                }
            });
        },

        async fetchApiDocs() {
            try {
                let res = await fetch('/api/docs');
                this.availableApis = await res.json();

                // Match selected APIs based on URLs for cloned data
                this.sources.forEach(src => {
                    const match = this.availableApis.find(a => src.url.includes(a.path));
                    if (match) {
                        src.selectedApi = match.path;
                    }
                });
            } catch (e) {
                console.error("Failed to load API docs", e);
            }
        },

        addFieldRow() {
            this.mappedFields.push({
                id: Date.now() + Math.random().toString(),
                source_field: '',
                client_name: ''
            });
        },

        removeFieldRow(index) {
            this.mappedFields.splice(index, 1);
        },

        autoFillName(index) {
            let row = this.mappedFields[index];
            if (!row.client_name && row.source_field) {
                let parts = row.source_field.split('.');
                row.client_name = parts[parts.length - 1].replace(/\[\d+\]/g, '');
            }
        },

        testMapping() {
            // Generate a fake payload based on the mapping
            const samplePayload = {};
            this.mappedFields.forEach(f => {
                if (f.source_field && f.client_name) {
                    // Just put a dummy value for the test
                    samplePayload[f.client_name] = `[Sample value from ${f.source_field}]`;
                }
            });

            this.testPayloadJSON = JSON.stringify(samplePayload, null, 2);
            if (this.testPayloadJSON === '{}') {
                this.testPayloadJSON = '{\n  "message": "No fields mapped yet."\n}';
            }

            this.showTestModal = true;
        },

        async submitForm() {
            if (!this.templateName || !this.clientName) {
                this.isError = true;
                this.message = "Client Name and Template Name are required";
                return;
            }

            this.isSubmitting = true;
            this.message = '';

            try {
                const payload = {
                    client_name: this.clientName,
                    name: this.templateName,
                    schedule_immediately: this.scheduleImmediately,
                    schedule_interval: parseInt(this.scheduleInterval),
                    sources: this.sources.map(s => ({
                        url: s.url,
                        auth_token: s.auth_token
                    })),
                    client_url: this.clientUrl,
                    client_auth_type: this.clientAuthType,
                    client_credentials: this.clientAuthType === 'bearer' ? { token: this.clientAuthToken } : {},
                    field_mapping: this.mappedFields.reduce((acc, f) => {
                        if (f.source_field && f.client_name) {
                            acc[f.client_name] = f.source_field;
                        }
                        return acc;
                    }, {})
                };

                const response = await fetch('/api/templates', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    this.message = 'Template created successfully!';
                    this.isError = false;

                    setTimeout(() => {
                        if (this.scheduleImmediately) {
                            window.location.href = '/'; // Go to schedule dashboard
                        } else {
                            window.location.href = '/templates';
                        }
                    }, 1500);
                } else {
                    const error = await response.json();
                    throw new Error(error.message || 'Failed to save template');
                }
            } catch (error) {
                this.isError = true;
                this.message = error.message;
            } finally {
                this.isSubmitting = false;
            }
        }
    }));
});
