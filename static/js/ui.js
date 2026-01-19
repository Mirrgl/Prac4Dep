function setContainerState(container, state, message = '') {
    if (!container) return;
    
    if (state === 'loading') {
        container.innerHTML = '<div class="flex justify-center py-4"><div class="loading-spinner" role="status" aria-label="Загрузка"></div></div>';
    } else {
        const isError = state === 'error';
        container.innerHTML = `<p class="${isError ? 'text-red-500' : 'text-gray-500'} text-sm text-center py-4" ${isError ? 'role="alert"' : ''}>${message || (isError ? 'Ошибка загрузки данных' : 'Нет данных')}</p>`;
    }
}

const showLoading = c => setContainerState(c, 'loading');
const showError = (c, msg) => setContainerState(c, 'error', msg);
const showEmpty = (c, msg) => setContainerState(c, 'empty', msg);

function downloadFile(data, filename, mimeType) {
    let url = null;
    try {
        url = URL.createObjectURL(new Blob([data], { type: mimeType }));
        Object.assign(document.createElement('a'), { href: url, download: filename }).click();
        return true;
    } catch (e) {
        console.error('Ошибка загрузки:', e);
        showNotification(`Ошибка загрузки: ${e.message}`, 'error');
        return false;
    } finally {
        if (url) URL.revokeObjectURL(url);
    }
}

function renderListWidget(container, items, emptyMsg, itemRenderer) {
    if (!container) return;
    container.innerHTML = items.length
        ? `<ul class="space-y-2 text-sm max-h-80 overflow-y-auto">${items.map(itemRenderer).join('')}</ul>`
        : `<p class="text-gray-500 text-sm text-center py-4">${emptyMsg}</p>`;
}

function renderRankedList(container, items, emptyMsg, nameKey, countKey, badgeColor) {
    renderListWidget(container, items, emptyMsg, (item, idx) => `
        <li class="flex justify-between items-center">
            <span><span class="text-gray-400">#${idx + 1}</span><span class="font-medium ml-2">${escapeHtml(item[nameKey])}</span></span>
            <span class="${badgeColor} px-2 py-0.5 rounded text-xs">${formatNumber(item[countKey])}</span>
        </li>`);
}
