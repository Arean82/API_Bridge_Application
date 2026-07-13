class ConnectionsManager {
    constructor() {
        this.connections = window.parsedConnsData || [];
        this.newConn = this.getEmptyConn();
        this.loading = false;
        
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
            connection_type: 'rest'
        };
    }
    
    cacheDOM() {
        this.modal = document.getElementById('addConnectionModal');
        this.backdrop = document.getElementById('addConnectionBackdrop');
        this.title = document.getElementById('addConnectionTitle');
        this.nameInput = document.getElementById('connName');
        this.typeRadios = document.querySelectorAll('.conn-type-radio');
        this.sourceTypeSection = document.getElementById('connSourceTypeSection');
        this.isLocalSelect = document.getElementById('connIsLocalFile');
        this.remoteSection = document.getElementById('connRemoteSection');
        this.localSection = document.getElementById('connLocalSection');
        this.urlLabel = document.getElementById('connUrlLabel');
        this.urlInput = document.getElementById('connUrl');
        this.baseUrlInput = document.getElementById('connBaseUrl');
        this.fileInput = document.getElementById('connFileInput');
        this.fileStatus = document.getElementById('connFileStatus');
        this.authTokenInput = document.getElementById('connAuthToken');
        this.syncScheduleSelect = document.getElementById('connSyncSchedule');
        this.environmentsInput = document.getElementById('connEnvironments');
        
        this.saveBtn = document.getElementById('saveConnectionBtn');
        this.saveText = document.getElementById('saveConnectionText');
        this.cancelBtn = document.getElementById('cancelConnectionBtn');
        this.newBtn = document.getElementById('newConnectionBtn');
        
        this.loadingModal = document.getElementById('loadingModal');
        this.loadingMessage = document.getElementById('loadingMessage');
    }
    
    bindEvents() {
        if (this.newBtn) {
            this.newBtn.addEventListener('click', () => {
                this.newConn = this.getEmptyConn();
                this.populateForm();
                this.openModal();
            });
        }
        
        if (this.cancelBtn) {
            this.cancelBtn.addEventListener('click', () => this.closeModal());
        }
        if (this.backdrop) {
            this.backdrop.addEventListener('click', () => this.closeModal());
        }
        
        if (this.isLocalSelect) {
            this.isLocalSelect.addEventListener('change', (e) => {
                this.newConn.is_local_file = e.target.value === 'true';
                this.toggleSourceType();
            });
        }
        
        if (this.typeRadios) {
            this.typeRadios.forEach(radio => {
                radio.addEventListener('change', (e) => {
                    this.newConn.connection_type = e.target.value;
                    this.toggleSourceType();
                });
            });
        }
        
        if (this.fileInput) {
            this.fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        }
        
        if (this.saveBtn) {
            this.saveBtn.addEventListener('click', () => this.saveConnection());
        }
        
        // Bind list events
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
    
    toggleSourceType() {
        if (this.newConn.connection_type === 'graphql') {
            if (this.sourceTypeSection) this.sourceTypeSection.style.display = 'none';
            if (this.localSection) this.localSection.style.display = 'none';
            if (this.remoteSection) this.remoteSection.style.display = 'block';
            if (this.urlLabel) this.urlLabel.textContent = 'GraphQL API Base URL';
            if (this.urlInput) this.urlInput.placeholder = 'https://api.github.com/graphql';
        } else {
            if (this.sourceTypeSection) this.sourceTypeSection.style.display = 'block';
            if (this.urlLabel) this.urlLabel.textContent = 'Swagger JSON URL';
            if (this.urlInput) this.urlInput.placeholder = 'https://api.partner.com/docs.json';
            
            if (this.newConn.is_local_file) {
                this.remoteSection.style.display = 'none';
                this.localSection.style.display = 'block';
            } else {
                this.remoteSection.style.display = 'block';
                this.localSection.style.display = 'none';
            }
        }
    }
    
    populateForm() {
        this.title.textContent = this.newConn.id ? 'Edit Connection' : 'Add Connection';
        this.nameInput.value = this.newConn.name || '';
        this.isLocalSelect.value = this.newConn.is_local_file ? 'true' : 'false';
        
        if (this.typeRadios) {
            this.typeRadios.forEach(r => r.checked = (r.value === (this.newConn.connection_type || 'rest')));
        }
        
        this.toggleSourceType();
        
        if (this.newConn.is_local_file) {
            this.baseUrlInput.value = this.newConn.url || '';
            this.fileStatus.textContent = this.newConn.local_file_path ? `File ready: ${this.newConn.local_file_path}` : '';
            this.urlInput.value = '';
        } else {
            this.urlInput.value = this.newConn.url || '';
            this.baseUrlInput.value = '';
            this.fileStatus.textContent = '';
        }
        
        this.authTokenInput.value = this.newConn.auth_token || '';
        this.syncScheduleSelect.value = this.newConn.sync_schedule || '';
        this.environmentsInput.value = this.newConn.environments || '';
    }
    
    readForm() {
        this.newConn.name = this.nameInput.value;
        this.newConn.connection_type = document.querySelector('.conn-type-radio:checked').value;
        this.newConn.is_local_file = this.isLocalSelect.value === 'true';
        if (this.newConn.is_local_file) {
            this.newConn.url = this.baseUrlInput.value;
        } else {
            this.newConn.url = this.urlInput.value;
        }
        this.newConn.auth_token = this.authTokenInput.value;
        this.newConn.sync_schedule = this.syncScheduleSelect.value;
        this.newConn.environments = this.environmentsInput.value;
    }
    
    handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        this.newConn.local_file_path = file.name;
        this.fileStatus.textContent = `File ready: ${file.name}`;
        const reader = new FileReader();
        reader.onload = (e) => {
            this.newConn.json_content = e.target.result;
        };
        reader.readAsText(file);
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
            connection_type: conn.connection_type || 'rest'
        };
        this.populateForm();
        this.openModal();
    }
    
    async refreshConnection(id) {
        this.showLoading("Refreshing connection...");
        try {
            const res = await fetch(`/api/connections/${id}/refresh`, {method: 'POST'});
            if (!res.ok) {
                const err = await res.json();
                alert(err.error || "Failed to refresh");
            } else {
                window.location.reload();
            }
        } catch(e) {
            alert("Error refreshing connection");
        }
        this.hideLoading();
    }
    
    async saveConnection() {
        this.readForm();
        
        if (!this.newConn.name) {
            alert("Name is required"); return;
        }
        
        if (!this.newConn.url) {
            alert("Base API URL is required to resolve paths correctly."); return;
        }
        
        this.loading = true;
        this.saveText.textContent = 'Saving...';
        this.showLoading("Saving connection and fetching Swagger JSON...");
        
        try {
            let url = '/api/connections';
            let method = 'POST';
            if (this.newConn.id) {
                url += '/' + this.newConn.id;
                method = 'PUT';
            }
            
            const res = await fetch(url, {
                method: method,
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(this.newConn)
            });
            
            if (!res.ok) {
                const err = await res.json();
                alert(err.error || "Failed to save connection");
            } else {
                const saved = await res.json();
                if (saved.warning) {
                    alert("Connection saved but disabled: " + saved.warning);
                }
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
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ is_active: targetState })
            });
            
            if (!res.ok) {
                const err = await res.json();
                alert(err.error || "Failed to toggle connection state");
                window.location.reload(); // Revert toggle UI
            } else {
                const updated = await res.json();
                // Update text
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
        if(!confirm("Are you sure you want to delete this connection?")) return;
        try {
            await fetch(`/api/connections/${id}`, {method: 'DELETE'});
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
