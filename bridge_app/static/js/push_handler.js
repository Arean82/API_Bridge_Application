class PushHandler {
    constructor(containerId, addBtnId) {
        this.containerId = containerId;
        this.addBtnId = addBtnId;
        this.destinations = [];
        this.availableFields = [];
        this.container = document.getElementById(this.containerId);
        this.addBtn = document.getElementById(this.addBtnId);
        
        if (this.addBtn) {
            this.addBtn.addEventListener('click', () => this.addDestination());
        }
    }

    setAvailableFields(fields) {
        this.availableFields = fields || [];
        this.render();
    }

    loadDestinations(destinationsList) {
        this.destinations = (destinationsList || []).map(d => ({
            ...d,
            field_mapping: d.field_mapping || []
        }));
        this.render();
    }

    addDestination() {
        this.destinations.push({
            id: Date.now() + Math.random(),
            url: '',
            method: 'POST',
            auth_type: 'none',
            auth_token: '',
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
                    No destinations added. Click "+ Add Destination" to send data.
                </div>
            `;
            return;
        }

        this.destinations.forEach((dest, idx) => {
            const div = document.createElement('div');
            div.className = "bg-white dark:bg-[#202124] p-4 rounded-lg border border-black/10 shadow-sm relative mb-4";
            
            // Build the field mapping HTML
            let fieldMappingHtml = `
                <div class="mt-6 pt-4 border-t border-black/10">
                    <div class="flex justify-between items-center mb-3">
                        <h6 class="text-xs font-bold text-gray-700 dark:text-gray-300">Field Mapping for Destination ${idx + 1}</h6>
                        <button class="theme-btn px-2 py-1 text-xs flex items-center gap-1 add-field-btn" data-idx="${idx}">
                            + Add Field
                        </button>
                    </div>
                    <div class="space-y-2">
            `;
            
            if (dest.field_mapping.length === 0) {
                fieldMappingHtml += `<div class="text-center py-4 text-xs theme-text-muted bg-black/5 rounded border border-black/10 border-dashed">No fields mapped for this destination.</div>`;
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
                    <button class="text-red-500 hover:text-red-700 p-1 dest-rm-btn" data-idx="${idx}" title="Remove Destination">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                    </button>
                </div>
                
                <h5 class="text-sm font-bold mb-3 text-gray-700 dark:text-gray-300">Destination ${idx + 1}</h5>
                <div class="mb-3">
                    <label class="block text-xs font-medium mb-1">Destination URL</label>
                    <input type="text" class="theme-input w-full p-2 text-sm dest-url" data-idx="${idx}" value="${dest.url}" placeholder="https://api.client.com/ingest">
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-medium mb-1">Auth Type</label>
                        <select class="theme-input w-full p-2 text-sm dest-auth-type" data-idx="${idx}">
                            <option value="none" ${dest.auth_type === 'none' ? 'selected' : ''}>None</option>
                            <option value="bearer" ${dest.auth_type === 'bearer' ? 'selected' : ''}>Bearer Token</option>
                        </select>
                    </div>
                    <div class="dest-auth-token-wrapper" style="display: ${dest.auth_type === 'bearer' ? 'block' : 'none'};">
                        <label class="block text-xs font-medium mb-1">Auth Token</label>
                        <input type="password" class="theme-input w-full p-2 text-sm dest-auth-token" data-idx="${idx}" value="${dest.auth_token}">
                    </div>
                </div>
                ${fieldMappingHtml}
            `;
            
            div.querySelector('.dest-url').addEventListener('input', (e) => { this.destinations[idx].url = e.target.value; });
            div.querySelector('.dest-auth-type').addEventListener('change', (e) => { 
                this.destinations[idx].auth_type = e.target.value; 
                div.querySelector('.dest-auth-token-wrapper').style.display = e.target.value === 'bearer' ? 'block' : 'none';
            });
            div.querySelector('.dest-auth-token').addEventListener('input', (e) => { this.destinations[idx].auth_token = e.target.value; });
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
        return this.destinations.map(d => ({
            url: d.url,
            method: d.method,
            auth_type: d.auth_type,
            auth_token: d.auth_token,
            field_mapping: d.field_mapping.filter(f => f.source_field && f.client_name).map(f => ({
                source: f.source_field,
                target: f.client_name,
                value_mapping: f.value_mapping || []
            }))
        }));
    }
}
window.PushHandler = PushHandler;
