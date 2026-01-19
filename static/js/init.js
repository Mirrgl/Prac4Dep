document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') {
            const modal = document.querySelector('.modal-overlay:not(.hidden)');
            if (modal) { 
                modal.classList.add('hidden'); 
                const trigger = document.getElementById(modal.dataset.trigger);
                if (trigger) trigger.focus();
            }
        }
    });
    
    window.addEventListener('beforeunload', () => { 
        stopAutoRefresh(); 
        clearAllNotifications(); 
        if (typeof DashboardController !== 'undefined') {
            DashboardController.destroy(); 
        }
    });
    
    if (document.querySelector('[data-widget]')) {
        if (typeof DashboardController !== 'undefined') {
            DashboardController.init();
        }
    }
});
