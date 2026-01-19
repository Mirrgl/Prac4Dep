const SIEM = {
    REFRESH_INTERVAL: 30000,
    NOTIFICATION_DURATION: 3000,
    DEBOUNCE_DELAY: 300,
    API_BASE: '/api',
    state: { 
        isAuthenticated: false, 
        lastRefresh: null, 
        refreshTimer: null 
    },
    _activeNotifications: new Set()
};

const SEVERITY_CLASSES = { 
    low: 'severity-low', 
    medium: 'severity-medium', 
    high: 'severity-high', 
    critical: 'severity-critical' 
};

const CHART_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
const SEVERITY_COLORS = ['#10b981', '#f59e0b', '#ef4444', '#7c3aed'];

const DOUGHNUT_OPTIONS = {
    responsive: true, 
    maintainAspectRatio: false,
    plugins: { 
        legend: { 
            position: 'bottom', 
            labels: { 
                boxWidth: 12, 
                font: { size: 10 }, 
                padding: 8 
            } 
        } 
    }
};
