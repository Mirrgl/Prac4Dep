async function apiRequest(endpoint, options = {}) {
    const url = endpoint.startsWith('/') ? endpoint : `${SIEM.API_BASE}/${endpoint}`;
    try {
        const response = await fetch(url, { 
            headers: { 'Content-Type': 'application/json' }, 
            credentials: 'include', 
            ...options 
        });
        
        if (response.status === 401) {
            SIEM.state.isAuthenticated = false;
            window.location.href = '/login';
            throw new Error('Требуется аутентификация');
        }
        
        if (response.ok) { 
            SIEM.state.isAuthenticated = true; 
            SIEM.state.lastRefresh = new Date(); 
        }
        
        return response;
    } catch (error) {
        if (error.name !== 'AbortError' && error.message !== 'Требуется аутентификация') {
            console.error('Ошибка API запроса:', error);
        }
        throw error;
    }
}

function showNotification(message, type = 'info') {
    const colors = { 
        success: 'bg-green-500', 
        error: 'bg-red-500', 
        warning: 'bg-yellow-500', 
        info: 'bg-blue-500' 
    };
    
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transition-opacity duration-300 ${colors[type] || colors.info} text-white`;
    notification.textContent = message;
    notification.setAttribute('role', 'alert');
    
    SIEM._activeNotifications.add(notification);
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => { 
            notification.remove(); 
            SIEM._activeNotifications.delete(notification); 
        }, 300);
    }, SIEM.NOTIFICATION_DURATION);
}

function clearAllNotifications() {
    SIEM._activeNotifications.forEach(n => n.remove());
    SIEM._activeNotifications.clear();
}

function startAutoRefresh(callback, interval = SIEM.REFRESH_INTERVAL) {
    stopAutoRefresh();
    if (typeof callback !== 'function') return;
    SIEM.state.refreshTimer = setInterval(() => { 
        callback(); 
        SIEM.state.lastRefresh = new Date(); 
    }, interval);
}

function stopAutoRefresh() {
    if (SIEM.state.refreshTimer) { 
        clearInterval(SIEM.state.refreshTimer); 
        SIEM.state.refreshTimer = null; 
    }
}
