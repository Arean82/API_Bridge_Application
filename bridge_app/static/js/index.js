document.addEventListener('alpine:init', () => {
    Alpine.data('scheduleDashboard', () => ({
        activeJobs: [],
        
        init() {
            this.fetchJobs();
            // Refresh every 10 seconds
            setInterval(() => { this.fetchJobs(); }, 10000);
        },
        
        async fetchJobs() {
            try {
                let res = await fetch('/api/jobs');
                let data = await res.json();
                this.activeJobs = data || [];
            } catch (e) {
                console.error("Failed to fetch jobs", e);
            }
        },
        
        async toggleJob(job) {
            try {
                let res = await fetch(`/api/jobs/${job.id}/toggle`, { method: 'POST' });
                if (res.ok) {
                    this.fetchJobs();
                } else {
                    alert('Failed to toggle job status.');
                }
            } catch (e) {
                console.error(e);
                alert('Error toggling job.');
            }
        },
        
        async deleteJob(id) {
            if (!confirm('Are you sure you want to delete this schedule?')) return;
            try {
                let res = await fetch(`/api/jobs/${id}`, { method: 'DELETE' });
                if (res.ok) {
                    this.fetchJobs();
                } else {
                    alert('Failed to delete job.');
                }
            } catch (e) {
                console.error(e);
                alert('Error deleting job.');
            }
        }
    }));
});
