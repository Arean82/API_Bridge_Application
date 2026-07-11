class PullRestHandler {
    constructor(containerId, addBtnId) {
        this.containerId = containerId;
        this.addBtnId = addBtnId;
        this.container = document.getElementById(this.containerId);
        this.addBtn = document.getElementById(this.addBtnId);
        this.destinations = [];
        this.availableFields = [];
        this.templateName = '';

        if (this.addBtn) {
            this.addBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.addDestination();
            });
        }
    }

    setAvailableFields(fields) {
        this.availableFields = fields || [];
        this.render();
    }

    loadData(destinationsList) {
        this.destinations = (destinationsList || []).map(d => ({
            ...d,
            name: d.name || 'Client',
            method: d.method || 'GET',
            field_mapping: d.field_mapping || []
        }));
        this.render();
    }

    setEndpointUrl(templateName) {
        this.templateName = templateName || '';
        this.render();
    }
    
    generateEndpointUrl(destName) {
        let tSlug = this.templateName ? this.templateName.toLowerCase().replace(/[^a-z0-9]/g, '_') : 'untitled_template';
        let dSlug = (destName || 'client').toLowerCase().replace(/[^a-z0-9]/g, '_');
        return `/api/bridge/pull/${tSlug}/${dSlug}`;
    }

    addDestination() {
        this.destinations.push({
            id: Date.now() + Math.random(),
            name: 'Client Endpoint ' + (this.destinations.length + 1),
            method: 'GET',
            field_mapping: []
        });
        this.render();
    }

    removeDestination(idx) {
        this.destinations.splice(idx, 1);
        this.render();
    }

    addFieldRow(destIdx) {
        this.destinations[destIdx].field_mapping.push({
            id: Date.now(),
            source_field: '',
            client_name: '',
            value_mapping: []
        });
        this.render();
    }

    removeFieldRow(destIdx, fieldIdx) {
        this.destinations[destIdx].field_mapping.splice(fieldIdx, 1);
        this.render();
    }

    autoFillName(destIdx, fieldIdx) {
        let row = this.destinations[destIdx].field_mapping[fieldIdx];
        if (!row.client_name && row.source_field) {
            let parts = row.source_field.split('.');
            row.client_name = parts[parts.length - 1].replace(/\[\d+\]/g, '');
            this.render();
        }
    }

    render() {
        if (!this.container) return;
        this.container.innerHTML = '';
        if (this.destinations.length === 0) {
            this.container.innerHTML = `
                <div class="text-center py-6 text-sm theme-text-muted bg-black/5 rounded border border-black/10 border-dashed">
                    No REST endpoints added. Click "+ Add Endpoint" to expose a pull URL.
                </div>
            `;
            return;
        }

        this.destinations.forEach((dest, idx) => {
            const div = document.createElement('div');
            div.className = "bg-white dark:bg-[#202124] p-4 rounded-lg border border-black/10 shadow-sm relative mb-4";
            
            let url = this.generateEndpointUrl(dest.name);
            
            // Build the field mapping HTML
            let fieldMappingHtml = `
                <div class="mt-6 pt-4 border-t border-black/10">
                    <div class="flex justify-between items-center mb-3">
                        <h6 class="text-xs font-bold text-gray-700 dark:text-gray-300">Field Mapping for <span class="dest-name-preview">${dest.name}</span></h6>
                        <button class="theme-btn px-2 py-1 text-xs flex items-center gap-1 add-field-btn" data-idx="${idx}">
                            + Add Field
                        </button>
                    </div>
                    <div class="space-y-2">
            `;
            
            if (dest.field_mapping.length === 0) {
                fieldMappingHtml += `<div class="text-center py-4 text-xs theme-text-muted bg-black/5 rounded border border-black/10 border-dashed">No fields mapped for this endpoint.</div>`;
            } else {
                dest.field_mapping.forEach((field, fIdx) => {
                    fieldMappingHtml += `
                        <div class="flex items-center gap-2 bg-gray-50 dark:bg-black/20 p-2 rounded border border-black/5">
                            <div class="flex-1">
                                <select class="theme-input w-full p-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 src-field" data-didx="${idx}" data-fidx="${fIdx}">
                                    <option value="">-- Select Source Field --</option>
                                    ${this.availableFields.map(opt => `<option value="${opt}" ${field.source_field === opt ? 'selected' : ''}>${opt}</option>`).join('')}
                                </select>
                            </div>
                            <div class="theme-text-muted">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                            </div>
                            <div class="flex-1">
                                <input type="text" class="theme-input w-full p-1.5 text-xs target-field" data-didx="${idx}" data-fidx="${fIdx}" value="${field.client_name}" placeholder="e.g. order_id">
                            </div>
                            <button class="text-red-500 hover:text-red-700 p-1 rm-field-btn" data-didx="${idx}" data-fidx="${fIdx}" title="Remove Field">
                                &times;
                            </button>
                        </div>
                    `;
                });
            }
            fieldMappingHtml += `</div></div>`;

            div.innerHTML = `
                <div class="absolute top-2 right-2 flex space-x-2">
                    <button class="text-red-500 hover:text-red-700 p-1 dest-rm-btn" data-idx="${idx}" title="Remove Endpoint">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                    </button>
                </div>
                
                <h5 class="text-sm font-bold mb-3 text-gray-700 dark:text-gray-300">Endpoint ${idx + 1}</h5>
                <div class="mt-4 grid grid-cols-2 gap-4">
                    <div class="col-span-2 md:col-span-1">
                        <label class="block text-xs font-medium mb-1">Destination Name (URL Slug)</label>
                        <input type="text" class="theme-input w-full p-2 text-sm dest-name-in" data-idx="${idx}" value="${dest.name}">
                    </div>
                    <div class="col-span-2 md:col-span-1">
                        <label class="block text-xs font-medium mb-1">Pull Method</label>
                        <select class="theme-input w-full p-2 text-sm dest-method-sel" data-idx="${idx}">
                            <option value="GET" ${dest.method === 'GET' ? 'selected' : ''}>GET</option>
                            <option value="POST" ${dest.method === 'POST' ? 'selected' : ''}>POST</option>
                            <option value="PUT" ${dest.method === 'PUT' ? 'selected' : ''}>PUT</option>
                            <option value="DELETE" ${dest.method === 'DELETE' ? 'selected' : ''}>DELETE</option>
                            <option value="PATCH" ${dest.method === 'PATCH' ? 'selected' : ''}>PATCH</option>
                        </select>
                    </div>
                    <div class="col-span-2">
                        <div class="bg-black/5 p-3 rounded border border-black/10">
                            <div class="mb-2">
                                <span class="text-xs font-bold text-gray-700 dark:text-gray-300">Base URL:</span>
                                <span class="text-xs font-mono ml-2 theme-text-muted">${window.location.origin}</span>
                            </div>
                            <div>
                                <span class="text-xs font-bold text-gray-700 dark:text-gray-300">Endpoint Path:</span>
                                <span class="text-xs font-mono ml-2">
                                    <span class="font-bold text-indigo-500 method-preview">${dest.method || 'GET'}</span> 
                                    <span class="theme-text-muted url-preview">${url}</span>
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
                ${fieldMappingHtml}
            `;
            
            div.querySelector('.dest-name-in').addEventListener('input', (e) => {
                this.destinations[idx].name = e.target.value;
                const urlPreview = div.querySelector('.url-preview');
                if (urlPreview) urlPreview.textContent = this.generateEndpointUrl(e.target.value);
                const namePreview = div.querySelector('.dest-name-preview');
                if (namePreview) namePreview.textContent = e.target.value;
            });
            div.querySelector('.dest-method-sel').addEventListener('change', (e) => {
                this.destinations[idx].method = e.target.value;
                const preview = div.querySelector('.method-preview');
                if (preview) preview.textContent = e.target.value;
            });
            div.querySelector('.dest-rm-btn').addEventListener('click', (e) => { e.preventDefault(); this.removeDestination(idx); });

            // Event listeners for field mapping
            const addFieldBtn = div.querySelector('.add-field-btn');
            if(addFieldBtn) addFieldBtn.addEventListener('click', (e) => { e.preventDefault(); this.addFieldRow(idx); });

            div.querySelectorAll('.src-field').forEach(inp => {
                inp.addEventListener('input', (e) => { 
                    this.destinations[idx].field_mapping[e.target.dataset.fidx].source_field = e.target.value; 
                });
                inp.addEventListener('blur', (e) => {
                    this.autoFillName(idx, e.target.dataset.fidx);
                });
            });
            
            div.querySelectorAll('.target-field').forEach(inp => {
                inp.addEventListener('input', (e) => { 
                    this.destinations[idx].field_mapping[e.target.dataset.fidx].client_name = e.target.value; 
                });
            });

            div.querySelectorAll('.rm-field-btn').forEach(btn => {
                btn.addEventListener('click', (e) => { 
                    e.preventDefault(); 
                    this.removeFieldRow(idx, e.target.dataset.fidx); 
                });
            });

            this.container.appendChild(div);
        });
    }

    getPayload() {
        return {
            destinations: this.destinations.map(d => ({
                name: d.name,
                method: d.method,
                url: this.generateEndpointUrl(d.name),
                field_mapping: d.field_mapping.filter(f => f.source_field && f.client_name).map(f => ({
                    source: f.source_field,
                    target: f.client_name,
                    value_mapping: f.value_mapping || []
                }))
            }))
        };
    }
}
window.PullRestHandler = PullRestHandler;
