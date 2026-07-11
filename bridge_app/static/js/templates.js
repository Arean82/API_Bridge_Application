class TemplateManager {
    constructor() {
        this.templates = window.parsedTemplatesData || [];
        this.connsLookup = window.parsedConnsData || {};
        
        // Ensure Modal controller is available
        this.modalController = window.templateModalController || null;
        
        this.bindEvents();
    }
    
    bindEvents() {
        document.querySelectorAll('.edit-template-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = parseInt(e.currentTarget.dataset.id);
                if (this.modalController) this.modalController.openEdit(id);
            });
        });
        
        document.querySelectorAll('.clone-template-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = parseInt(e.currentTarget.dataset.id);
                if (this.modalController) this.modalController.openClone(id);
            });
        });
        
        document.querySelectorAll('.delete-template-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                this.deleteTemplate(id);
            });
        });
    }
    
    async deleteTemplate(id) {
        if (!confirm("Are you sure you want to delete this template?")) return;
        try {
            const res = await fetch(`/api/templates/${id}`, { method: 'DELETE' });
            if (res.ok) {
                window.location.reload();
            } else {
                alert("Failed to delete template");
            }
        } catch (e) {
            alert("Error deleting template");
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.templateManager = new TemplateManager();
});
