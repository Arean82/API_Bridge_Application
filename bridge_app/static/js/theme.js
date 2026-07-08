document.addEventListener('alpine:init', () => {
    Alpine.data('themeManager', (initialConfig) => {
        let config = { theme: 'default', colorMode: 'auto' };
        if (initialConfig) {
            try {
                config = JSON.parse(initialConfig);
            } catch (e) {}
        }
        
        return {
            currentTheme: config.theme || 'default',
            colorMode: config.colorMode || 'auto',
            
            toggleMode() {
                const modes = ['auto', 'light', 'dark'];
                let idx = modes.indexOf(this.colorMode);
                this.colorMode = modes[(idx + 1) % modes.length];
                this.saveTheme();
            },
            
            saveTheme() {
                // Apply color mode and Tailwind dark class
                let isDark = false;
                if (this.colorMode === 'auto') {
                    isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                    document.body.setAttribute('data-color-mode', isDark ? 'dark' : 'light');
                } else {
                    isDark = (this.colorMode === 'dark');
                    document.body.setAttribute('data-color-mode', this.colorMode);
                }
                
                if (isDark) {
                    document.documentElement.classList.add('dark');
                } else {
                    document.documentElement.classList.remove('dark');
                }

                // Apply theme
                document.body.setAttribute('data-theme', this.currentTheme);

                // Save to server config
                fetch('/api/config/theme', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ theme: this.currentTheme, colorMode: this.colorMode })
                });
            },
            
            init() {
                this.saveTheme(); // Apply immediately on load
            }
        };
    });
});
