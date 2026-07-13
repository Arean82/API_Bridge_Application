class ConnectionsManager {
    constructor() {
        this.connections = window.parsedConnsData || [];
        this.newConn = this.getEmptyConn();
        this.loading = false;
        
        // Arrays to store custom headers locally before saving
        this.restCustomHeaders = [];
        this.graphqlCustomHeaders = [];

        this.cacheDOM();
        this.bindEvents();
    }

    getEmptyConn() {
        return {
            id: null,
            name: '',
            url: '',
            is_local_file: false,
            local_file_path: '',
            json_content: '',
            auth_token: '',
            sync_schedule: '',
            environments: '',
            connection_type: 'rest',
            custom_headers: []
        };
    }

    cacheDOM() {
        // Modal Wrapper
        this.modal = document.getElementById('addConnectionModal');
        this.backdrop = document.getElementById('addConnectionBackdrop');
        this.title = document.getElementById('addConnectionTitle');
        this.typeRadios = document.querySelectorAll('.conn-type-radio');
        this.saveBtn = document.getElementById('saveConnectionBtn');
        this.saveText = document.getElementById('saveConnectionText');
        this.cancelBtn = document.getElementById('cancelConnectionBtn');
        this.newBtn = document.getElementById('newConnectionBtn');
        
        // Loading
        this.loadingModal = document.getElementById('loadingModal');
        this.loadingMessage = document.getElementById('loadingMessage');

        // Main Blocks
        this.restBlock = document.getElementById('restConnBlock');
        this.graphqlBlock = document.getElementById('graphqlConnBlock');

        // REST Elements
        this.restName = document.getElementById('restConnName');
        this.restIsLocalFile = document.getElementById('restConnIsLocalFile');
        this.restUrlSection = document.getElementById('restConnUrlSection');
        this.restUrl = document.getElementById('restConnUrl');
        this.restLocalSection = document.getElementById('restConnLocalSection');
        this.restFileInput = document.getElementById('restConnFileInput');
        this.restFileStatus = document.getElementById('restConnFileStatus');
        this.restPasteSection = document.getElementById('restConnPasteSection');
        this.restPastedSpec = document.getElementById('restConnPastedSpec');
        this.restBaseUrlSection = document.getElementById('restConnBaseUrlSection');
        this.restBaseUrl = document.getElementById('restConnBaseUrl');
        
        this.restSameAuth = document.getElementById('restConnSameAuth');
        this.restAuthType = document.getElementById('restConnAuthType');
        this.restAuthBearerSection = document.getElementById('restConnAuthBearerSection');
        this.restAuthApiKeySection = document.getElementById('restConnAuthApiKeySection');
        this.restAuthBasicSection = document.getElementById('restConnAuthBasicSection');
        this.restAuthBearerToken = document.getElementById('restConnAuthBearerToken');
        this.restAuthApiKeyName = document.getElementById('restConnAuthApiKeyName');
        this.restAuthApiKeyValue = document.getElementById('restConnAuthApiKeyValue');
        this.restAuthBasicUsername = document.getElementById('restConnAuthBasicUsername');
        this.restAuthBasicPassword = document.getElementById('restConnAuthBasicPassword');

        this.restSpecAuthBlock = document.getElementById('restConnSpecAuthBlock');
        this.restSpecAuthType = document.getElementById('restConnSpecAuthType');
        this.restSpecAuthBearerSection = document.getElementById('restConnSpecAuthBearerSection');
        this.restSpecAuthApiKeySection = document.getElementById('restConnSpecAuthApiKeySection');
        this.restSpecAuthBasicSection = document.getElementById('restConnSpecAuthBasicSection');
        this.restSpecAuthBearerToken = document.getElementById('restConnSpecAuthBearerToken');
        this.restSpecAuthApiKeyName = document.getElementById('restConnSpecAuthApiKeyName');
        this.restSpecAuthApiKeyValue = document.getElementById('restConnSpecAuthApiKeyValue');
        this.restSpecAuthBasicUsername = document.getElementById('restConnSpecAuthBasicUsername');
        this.restSpecAuthBasicPassword = document.getElementById('restConnSpecAuthBasicPassword');
        
        this.restAddHeaderBtn = document.getElementById('restConnAddHeaderBtn');
        this.restCustomHeadersContainer = document.getElementById('restConnCustomHeadersContainer');
        this.restSyncSchedule = document.getElementById('restConnSyncSchedule');
        this.restValidateBtn = document.getElementById('restConnValidateBtn');
        this.restValidationResult = document.getElementById('restConnValidationResult');

        // GraphQL Elements
        this.graphqlName = document.getElementById('graphqlConnName');
        this.graphqlUrl = document.getElementById('graphqlConnUrl');
        this.graphqlSchemaSource = document.getElementById('graphqlConnSchemaSource');
        this.graphqlSdlSection = document.getElementById('graphqlConnSdlSection');
        this.graphqlSdlText = document.getElementById('graphqlConnSdlText');
        this.graphqlFileSection = document.getElementById('graphqlConnFileSection');
        this.graphqlFileInput = document.getElementById('graphqlConnFileInput');
        this.graphqlFileStatus = document.getElementById('graphqlConnFileStatus');

        this.graphqlAuthType = document.getElementById('graphqlConnAuthType');
        this.graphqlAuthBearerSection = document.getElementById('graphqlAuthBearerSection');
        this.graphqlAuthApiKeySection = document.getElementById('graphqlAuthApiKeySection');
        this.graphqlAuthBasicSection = document.getElementById('graphqlAuthBasicSection');
        this.graphqlAuthBearerToken = document.getElementById('graphqlConnAuthBearerToken');
        this.graphqlAuthApiKeyName = document.getElementById('graphqlConnAuthApiKeyName');
        this.graphqlAuthApiKeyValue = document.getElementById('graphqlConnAuthApiKeyValue');
        this.graphqlAuthBasicUsername = document.getElementById('graphqlConnAuthBasicUsername');
        this.graphqlAuthBasicPassword = document.getElementById('graphqlConnAuthBasicPassword');

        this.graphqlAddHeaderBtn = document.getElementById('graphqlConnAddHeaderBtn');
        this.graphqlCustomHeadersContainer = document.getElementById('graphqlConnCustomHeadersContainer');
        this.graphqlSyncSchedule = document.getElementById('graphqlConnSyncSchedule');
        this.graphqlValidationResult = document.getElementById('graphqlConnValidationResult');
    }

    bindEvents() {
        if (this.newBtn) {
            this.newBtn.addEventListener('click', () => {
                this.newConn = this.getEmptyConn();
                this.populateForm();
                this.openModal();
            });
        }

        if (this.cancelBtn) this.cancelBtn.addEventListener('click', () => this.closeModal());
        if (this.backdrop) this.backdrop.addEventListener('click', () => this.closeModal());
        if (this.saveBtn) this.saveBtn.addEventListener('click', () => this.saveConnection());

        // Top level type toggle
        if (this.typeRadios) {
            this.typeRadios.forEach(radio => {
                radio.addEventListener('change', (e) => {
                    this.newConn.connection_type = e.target.value;
                    this.toggleMainBlocks();
                });
            });
        }

        // REST Events
        if (this.restIsLocalFile) {
            this.restIsLocalFile.addEventListener('change', (e) => {
                this.toggleRestSourceSections(e.target.value);
            });
        }
        if (this.restFileInput) this.restFileInput.addEventListener('change', (e) => this.handleRestFileUpload(e));
        if (this.restSameAuth) this.restSameAuth.addEventListener('change', () => this.toggleRestAuth());
        if (this.restAuthType) this.restAuthType.addEventListener('change', () => this.toggleRestAuth());
        if (this.restSpecAuthType) this.restSpecAuthType.addEventListener('change', () => this.toggleRestAuth());
        if (this.restAddHeaderBtn) this.restAddHeaderBtn.addEventListener('click', () => this.addCustomHeaderRow('rest'));
        if (this.restValidateBtn) this.restValidateBtn.addEventListener('click', () => this.validateRestConnection());

        // GraphQL Events
        if (this.graphqlSchemaSource) {
            this.graphqlSchemaSource.addEventListener('change', (e) => {
                this.toggleGraphqlSourceSections(e.target.value);
            });
        }
        if (this.graphqlFileInput) this.graphqlFileInput.addEventListener('change', (e) => this.handleGraphqlFileUpload(e));
        if (this.graphqlAuthType) this.graphqlAuthType.addEventListener('change', () => this.toggleGraphqlAuth());
        if (this.graphqlAddHeaderBtn) this.graphqlAddHeaderBtn.addEventListener('click', () => this.addCustomHeaderRow('graphql'));

        // List Events
        document.querySelectorAll('.edit-connection-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.editConnection(e.currentTarget.dataset.id));
        });
        document.querySelectorAll('.delete-connection-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.deleteConnection(e.currentTarget.dataset.id));
        });
        document.querySelectorAll('.refresh-connection-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.refreshConnection(e.currentTarget.dataset.id));
        });
        document.querySelectorAll('.toggle-connection-btn').forEach(btn => {
            btn.addEventListener('change', (e) => this.toggleConnection(e.currentTarget.dataset.id, e.target.checked));
        });
    }

    openModal() {
        if (this.modal) this.modal.style.display = 'flex';
        document.documentElement.style.overflow = 'hidden';
        document.body.style.overflow = 'hidden';
    }

    closeModal() {
        if (this.modal) this.modal.style.display = 'none';
        document.documentElement.style.overflow = '';
        document.body.style.overflow = '';
    }

    showLoading(message) {
        if (this.loadingMessage) this.loadingMessage.textContent = message;
        if (this.loadingModal) this.loadingModal.style.display = 'flex';
    }

    hideLoading() {
        if (this.loadingModal) this.loadingModal.style.display = 'none';
    }

    toggleMainBlocks() {
        const isGraphql = this.newConn.connection_type === 'graphql';
        if (isGraphql) {
            if (this.restBlock) this.restBlock.style.display = 'none';
            if (this.graphqlBlock) this.graphqlBlock.style.display = 'block';
        } else {
            if (this.graphqlBlock) this.graphqlBlock.style.display = 'none';
            if (this.restBlock) this.restBlock.style.display = 'block';
        }
    }

    toggleRestSourceSections(sourceType) {
        if (!this.restUrlSection) return;
        this.restUrlSection.style.display = 'none';
        this.restLocalSection.style.display = 'none';
        this.restPasteSection.style.display = 'none';
        this.restBaseUrlSection.style.display = 'none';
        if (this.restValidateBtn) this.restValidateBtn.style.display = 'none';

        if (sourceType === 'false') {
            this.restUrlSection.style.display = 'block';
            if (this.restValidateBtn) this.restValidateBtn.style.display = 'inline-flex';
            if (this.restSyncSchedule) this.restSyncSchedule.disabled = false;
        } else if (sourceType === 'true') {
            this.restLocalSection.style.display = 'block';
            this.restBaseUrlSection.style.display = 'block';
            if (this.restValidateBtn) this.restValidateBtn.style.display = 'inline-flex';
            if (this.restSyncSchedule) {
                this.restSyncSchedule.value = '';
                this.restSyncSchedule.disabled = true;
            }
        } else if (sourceType === 'paste') {
            this.restPasteSection.style.display = 'block';
            this.restBaseUrlSection.style.display = 'block';
            if (this.restValidateBtn) this.restValidateBtn.style.display = 'inline-flex';
            if (this.restSyncSchedule) {
                this.restSyncSchedule.value = '';
                this.restSyncSchedule.disabled = true;
            }
        }
    }

    toggleRestAuth() {
        if (!this.restSpecAuthBlock) return;
        
        // Upstream Auth
        this.restAuthBearerSection.style.display = this.restAuthType.value === 'bearer' ? 'block' : 'none';
        this.restAuthApiKeySection.style.display = this.restAuthType.value === 'api_key' ? 'grid' : 'none';
        this.restAuthBasicSection.style.display = this.restAuthType.value === 'basic' ? 'grid' : 'none';

        // Spec Auth
        if (this.restSameAuth.checked) {
            this.restSpecAuthBlock.style.display = 'none';
        } else {
            this.restSpecAuthBlock.style.display = 'block';
            this.restSpecAuthBearerSection.style.display = this.restSpecAuthType.value === 'bearer' ? 'block' : 'none';
            this.restSpecAuthApiKeySection.style.display = this.restSpecAuthType.value === 'api_key' ? 'grid' : 'none';
            this.restSpecAuthBasicSection.style.display = this.restSpecAuthType.value === 'basic' ? 'grid' : 'none';
        }
    }

    toggleGraphqlSourceSections(sourceType) {
        if (!this.graphqlSdlSection) return;
        this.graphqlSdlSection.style.display = 'none';
        this.graphqlFileSection.style.display = 'none';

        if (sourceType === 'sdl') {
            this.graphqlSdlSection.style.display = 'block';
            if (this.graphqlSyncSchedule) {
                this.graphqlSyncSchedule.value = '';
                this.graphqlSyncSchedule.disabled = true;
            }
        } else if (sourceType === 'file') {
            this.graphqlFileSection.style.display = 'block';
            if (this.graphqlSyncSchedule) {
                this.graphqlSyncSchedule.value = '';
                this.graphqlSyncSchedule.disabled = true;
            }
        } else {
            // Introspection
            if (this.graphqlSyncSchedule) this.graphqlSyncSchedule.disabled = false;
        }
    }

    toggleGraphqlAuth() {
        if (!this.graphqlAuthType) return;
        this.graphqlAuthBearerSection.style.display = this.graphqlAuthType.value === 'bearer' ? 'block' : 'none';
        this.graphqlAuthApiKeySection.style.display = this.graphqlAuthType.value === 'api_key' ? 'grid' : 'none';
        this.graphqlAuthBasicSection.style.display = this.graphqlAuthType.value === 'basic' ? 'grid' : 'none';
    }

    handleRestFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        this.newConn.local_file_path = file.name;
        if (this.restFileStatus) this.restFileStatus.textContent = `File ready: ${file.name}`;
        const reader = new FileReader();
        reader.onload = (e) => { this.newConn.json_content = e.target.result; };
        reader.readAsText(file);
    }

    handleGraphqlFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        this.newConn.local_file_path = file.name;
        if (this.graphqlFileStatus) this.graphqlFileStatus.textContent = `File ready: ${file.name}`;
        const reader = new FileReader();
        reader.onload = (e) => { this.newConn.json_content = e.target.result; };
        reader.readAsText(file);
    }

    // Custom Headers Logic
    addCustomHeaderRow(type) {
        const headers = type === 'rest' ? this.restCustomHeaders : this.graphqlCustomHeaders;
        headers.push({ name: '', value: '' });
        this.renderCustomHeaders(type);
    }

    removeCustomHeaderRow(type, index) {
        const headers = type === 'rest' ? this.restCustomHeaders : this.graphqlCustomHeaders;
        headers.splice(index, 1);
        this.renderCustomHeaders(type);
    }

    updateCustomHeader(type, index, field, value) {
        const headers = type === 'rest' ? this.restCustomHeaders : this.graphqlCustomHeaders;
        if (headers[index]) {
            headers[index][field] = value;
        }
    }

    renderCustomHeaders(type) {
        const container = type === 'rest' ? this.restCustomHeadersContainer : this.graphqlCustomHeadersContainer;
        const headers = type === 'rest' ? this.restCustomHeaders : this.graphqlCustomHeaders;
        if (!container) return;
        
        container.innerHTML = '';
        headers.forEach((header, index) => {
            const row = document.createElement('div');
            row.className = 'flex gap-2 items-center';
            row.innerHTML = `
                <input type="text" class="theme-input w-1/2 p-1.5 text-xs" placeholder="Header Name" value="${header.name}">
                <input type="text" class="theme-input w-1/2 p-1.5 text-xs" placeholder="Value" value="${header.value}">
                <button type="button" class="text-red-500 hover:text-red-700 p-1 rounded hover:bg-red-50 dark:hover:bg-red-900/30">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
            `;
            
            const inputs = row.querySelectorAll('input');
            inputs[0].addEventListener('input', (e) => this.updateCustomHeader(type, index, 'name', e.target.value));
            inputs[1].addEventListener('input', (e) => this.updateCustomHeader(type, index, 'value', e.target.value));
            
            const btn = row.querySelector('button');
            btn.addEventListener('click', () => this.removeCustomHeaderRow(type, index));
            
            container.appendChild(row);
        });
    }

    populateForm() {
        if (this.title) this.title.textContent = this.newConn.id ? 'Edit Connection' : 'Add Connection';

        if (this.typeRadios) {
            this.typeRadios.forEach(r => r.checked = (r.value === (this.newConn.connection_type || 'rest')));
        }
        this.toggleMainBlocks();

        // Clear existing header arrays
        this.restCustomHeaders = [];
        this.graphqlCustomHeaders = [];
        if (this.newConn.custom_headers) {
            const obj = this.newConn.custom_headers;
            for (const key in obj) {
                if (this.newConn.connection_type === 'rest') {
                    this.restCustomHeaders.push({ name: key, value: obj[key] });
                } else {
                    this.graphqlCustomHeaders.push({ name: key, value: obj[key] });
                }
            }
        }

        if (this.newConn.connection_type === 'rest') {
            if (this.restName) this.restName.value = this.newConn.name || '';
            if (this.restIsLocalFile) {
                if (this.newConn.is_local_file === 'paste' || this.newConn.json_content && !this.newConn.local_file_path) {
                    this.restIsLocalFile.value = 'paste';
                } else {
                    this.restIsLocalFile.value = this.newConn.is_local_file ? 'true' : 'false';
                }
                this.toggleRestSourceSections(this.restIsLocalFile.value);
            }
            
            if (this.restIsLocalFile && this.restIsLocalFile.value === 'false') {
                if (this.restUrl) this.restUrl.value = this.newConn.url || '';
                if (this.restBaseUrl) this.restBaseUrl.value = '';
            } else if (this.restIsLocalFile && this.restIsLocalFile.value === 'true') {
                if (this.restBaseUrl) this.restBaseUrl.value = this.newConn.url || '';
                if (this.restUrl) this.restUrl.value = '';
                if (this.restFileStatus) this.restFileStatus.textContent = this.newConn.local_file_path ? `File ready: ${this.newConn.local_file_path}` : '';
            } else if (this.restIsLocalFile && this.restIsLocalFile.value === 'paste') {
                if (this.restBaseUrl) this.restBaseUrl.value = this.newConn.url || '';
                if (this.restPastedSpec) this.restPastedSpec.value = this.newConn.json_content || '';
                if (this.restUrl) this.restUrl.value = '';
            }

            if (this.restSyncSchedule) this.restSyncSchedule.value = this.newConn.sync_schedule || '';
            this.renderCustomHeaders('rest');

            // Populate Auth here if necessary (simplifying for now)
        } else {
            if (this.graphqlName) this.graphqlName.value = this.newConn.name || '';
            if (this.graphqlUrl) this.graphqlUrl.value = this.newConn.url || '';
            if (this.graphqlSyncSchedule) this.graphqlSyncSchedule.value = this.newConn.sync_schedule || '';
            this.renderCustomHeaders('graphql');
        }
    }

    readForm() {
        const type = document.querySelector('.conn-type-radio:checked').value;
        this.newConn.connection_type = type;

        const builtHeaders = {};
        const headersArray = type === 'rest' ? this.restCustomHeaders : this.graphqlCustomHeaders;
        headersArray.forEach(h => {
            if (h.name.trim() !== '') builtHeaders[h.name.trim()] = h.value;
        });
        this.newConn.custom_headers = builtHeaders;

        if (type === 'rest') {
            this.newConn.name = this.restName ? this.restName.value : '';
            const source = this.restIsLocalFile ? this.restIsLocalFile.value : 'false';
            this.newConn.is_local_file = source === 'true';

            if (source === 'false') {
                this.newConn.url = this.restUrl ? this.restUrl.value : '';
            } else if (source === 'true') {
                this.newConn.url = this.restBaseUrl ? this.restBaseUrl.value : '';
            } else if (source === 'paste') {
                this.newConn.url = this.restBaseUrl ? this.restBaseUrl.value : '';
                this.newConn.json_content = this.restPastedSpec ? this.restPastedSpec.value : '';
            }
            
            this.newConn.sync_schedule = this.restSyncSchedule ? this.restSyncSchedule.value : '';
        } else {
            this.newConn.name = this.graphqlName ? this.graphqlName.value : '';
            this.newConn.url = this.graphqlUrl ? this.graphqlUrl.value : '';
            this.newConn.sync_schedule = this.graphqlSyncSchedule ? this.graphqlSyncSchedule.value : '';
            
            const schemaSource = this.graphqlSchemaSource ? this.graphqlSchemaSource.value : 'introspection';
            if (schemaSource === 'sdl') {
                this.newConn.json_content = this.graphqlSdlText ? this.graphqlSdlText.value : '';
            }
        }
    }

    editConnection(id) {
        const conn = this.connections.find(c => c.id == id);
        if (!conn) return;

        let envs_str = '';
        if (conn.environments && conn.environments.length > 0) {
            envs_str = JSON.stringify(conn.environments);
        }

        this.newConn = {
            id: conn.id,
            name: conn.name,
            url: conn.url,
            is_local_file: conn.is_local_file,
            local_file_path: conn.local_file_path,
            json_content: conn.json_content,
            auth_token: conn.auth_token || '',
            sync_schedule: conn.sync_schedule || '',
            environments: envs_str,
            connection_type: conn.connection_type || 'rest',
            custom_headers: conn.custom_headers || {}
        };
        this.populateForm();
        this.openModal();
    }

    async refreshConnection(id) {
        this.showLoading("Refreshing connection...");
        try {
            const res = await fetch(`/api/connections/${id}/refresh`, { method: 'POST' });
            if (!res.ok) {
                const err = await res.json();
                alert(err.error || "Failed to refresh");
            } else {
                window.location.reload();
            }
        } catch (e) {
            alert("Error refreshing connection");
        }
        this.hideLoading();
    }

    async validateRestConnection() {
        this.readForm();
        if (!this.restValidationResult) return;
        this.restValidationResult.style.display = 'block';
        this.restValidationResult.className = 'p-3 rounded-md text-sm border bg-blue-50 border-blue-200 text-blue-700';
        this.restValidationResult.innerHTML = '<span class="animate-pulse">Validating specification...</span>';
        
        try {
            const payload = {
                connection_type: 'rest',
                source_type: this.restIsLocalFile.value === 'false' ? 'url' : (this.restIsLocalFile.value === 'true' ? 'file' : 'paste'),
                url: this.newConn.url,
                content: this.newConn.json_content
            };
            
            const response = await fetch('/api/connections/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            
            if (result.success) {
                this.restValidationResult.className = 'p-3 rounded-md text-sm border bg-green-50 border-green-200 text-green-700';
                this.restValidationResult.innerHTML = `
                    <div class="font-bold mb-1">✓ Connection successful</div>
                    <div class="font-medium mb-2">✓ Valid ${result.spec_version} specification</div>
                    <div class="font-mono text-xs">
                        API: ${result.title}<br>
                        Version: ${result.api_version}<br>
                        Operations: ${result.operation_count}<br>
                        Schemas: ${result.schema_count}
                    </div>
                `;
            } else {
                this.restValidationResult.className = 'p-3 rounded-md text-sm border bg-red-50 border-red-200 text-red-700';
                this.restValidationResult.innerHTML = `<div class="font-bold mb-1">✕ Validation failed</div><div class="text-xs mt-1">${result.error || 'Unknown error'}</div>`;
            }
        } catch (error) {
            this.restValidationResult.className = 'p-3 rounded-md text-sm border bg-red-50 border-red-200 text-red-700';
            this.restValidationResult.innerHTML = `<div class="font-bold mb-1">✕ Validation failed</div><div class="text-xs mt-1">${error.message}</div>`;
        }
    }
    
    async saveConnection() {
        this.readForm();

        if (!this.newConn.name) {
            alert("Name is required"); return;
        }

        if (!this.newConn.url) {
            alert("API URL is required."); return;
        }

        this.loading = true;
        this.saveText.textContent = 'Saving...';
        this.showLoading("Saving connection...");

        try {
            let url = '/api/connections';
            let method = 'POST';
            if (this.newConn.id) {
                url += '/' + this.newConn.id;
                method = 'PUT';
            }

            const res = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.newConn)
            });

            if (!res.ok) {
                const err = await res.json();
                alert(err.error || "Failed to save connection");
            } else {
                const saved = await res.json();
                if (saved.warning) alert("Connection saved but disabled: " + saved.warning);
                window.location.reload();
            }
        } catch (e) {
            alert("Error saving connection");
        }

        this.loading = false;
        this.saveText.textContent = 'Save Connection';
        this.hideLoading();
    }

    async toggleConnection(id, targetState) {
        this.showLoading(targetState ? "Verifying and enabling connection..." : "Disabling connection...");

        try {
            const res = await fetch(`/api/connections/${id}/toggle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_active: targetState })
            });

            if (!res.ok) {
                const err = await res.json();
                alert(err.error || "Failed to toggle connection state");
                window.location.reload();
            } else {
                const updated = await res.json();
                const item = document.querySelector(`.connection-item[data-id="${id}"]`);
                if (item) {
                    const text = item.querySelector('.toggle-status-text');
                    if (text) text.textContent = updated.is_active ? 'Active' : 'Inactive';
                }
            }
        } catch (e) {
            alert("Error toggling connection");
            window.location.reload();
        }
        this.hideLoading();
    }

    async deleteConnection(id) {
        if (!confirm("Are you sure you want to delete this connection?")) return;
        try {
            await fetch(`/api/connections/${id}`, { method: 'DELETE' });
            window.location.reload();
        } catch (e) {
            alert("Error deleting connection");
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    try {
        const connsDataEl = document.getElementById('conns-data');
        if (connsDataEl) {
            window.parsedConnsData = JSON.parse(connsDataEl.textContent);
        }
    } catch (e) {
        window.parsedConnsData = [];
    }
    window.connectionsManager = new ConnectionsManager();
});
