const parseDate = ts => ts ? new Date(ts) : null;
const isValidDate = d => d && !isNaN(d.getTime());

const formatTimestamp = ts => { 
    const d = parseDate(ts); 
    return isValidDate(d) ? d.toLocaleString('ru-RU') : (ts || '-'); 
};

const formatTime = ts => { 
    const d = parseDate(ts); 
    return isValidDate(d) ? d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }) : '--'; 
};

const formatNumber = num => (num == null || isNaN(num)) ? '0' : Number(num).toLocaleString('ru-RU');

function escapeHtml(text) {
    if (text == null) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}