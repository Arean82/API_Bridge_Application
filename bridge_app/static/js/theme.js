class ThemeManager {
    constructor() {
        const body = document.body;
        let initialConfig = body.getAttribute('data-initial-theme');
        let config = { theme: 'default', colorMode: 'auto' };
        
        if (initialConfig) {
            try {
                // Flask passes `{"theme": "glass", "colorMode": "dark"}` as string
                // Need to unescape HTML entities if Jinja escaped it, but JSON.parse usually works
                // Handle single quotes if necessary, but Jinja tojson gives double quotes
                initialConfig = initialConfig.replace(/'/g, '"');
                let parsed = JSON.parse(initialConfig);
                if (typeof parsed === 'string') {
                    parsed = JSON.parse(parsed); // Double parse in case it was dumped twice
                }
                config = { ...config, ...parsed };
            } catch (e) {
                console.warn("Failed to parse initial theme config", e);
            }
        }
        
        this.currentTheme = config.theme || 'default';
        this.colorMode = config.colorMode || 'auto';
        
        this.initDOM();
        this.applyTheme();
    }

    initDOM() {
        this.themeSelector = document.getElementById('themeSelector');
        this.modeToggleBtn = document.getElementById('modeToggleBtn');
        this.iconAuto = document.getElementById('modeIconAuto');
        this.iconLight = document.getElementById('modeIconLight');
        this.iconDark = document.getElementById('modeIconDark');

        if (this.themeSelector) {
            this.themeSelector.value = this.currentTheme;
            this.themeSelector.addEventListener('change', (e) => {
                this.currentTheme = e.target.value;
                this.saveTheme();
            });
        }

        if (this.modeToggleBtn) {
            this.modeToggleBtn.addEventListener('click', () => this.toggleMode());
        }
    }

    toggleMode() {
        const modes = ['auto', 'light', 'dark'];
        let idx = modes.indexOf(this.colorMode);
        this.colorMode = modes[(idx + 1) % modes.length];
        this.saveTheme();
    }

    updateIcons() {
        if (!this.iconAuto) return;
        this.iconAuto.style.display = this.colorMode === 'auto' ? 'inline' : 'none';
        this.iconLight.style.display = this.colorMode === 'light' ? 'inline' : 'none';
        this.iconDark.style.display = this.colorMode === 'dark' ? 'inline' : 'none';
    }

    applyTheme() {
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

        document.body.setAttribute('data-theme', this.currentTheme);
        this.updateIcons();
    }

    saveTheme() {
        this.applyTheme();
        fetch('/api/config/theme', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ theme: this.currentTheme, colorMode: this.colorMode })
        }).catch(err => console.error("Failed to save theme", err));
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    window.themeManagerInstance = new ThemeManager();
});
