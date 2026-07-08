document.addEventListener('alpine:init', () => {
    Alpine.data('themeManager', () => ({
        currentTheme: localStorage.getItem('app_theme') || 'default',
        saveTheme() {
            localStorage.setItem('app_theme', this.currentTheme);
        }
    }));
});
