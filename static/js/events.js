let currentPage = 1;
let pageSize = 50;
let totalEvents = 0;
let currentFilters = {};
let currentEvents = [];
let isLoading = false;

document.addEventListener('DOMContentLoaded', function() {
    loadEvents();
    
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            currentPage = 1;
            loadEvents();
        });
    }
    
    const searchInput = document.getElementById('search-query');
    if (searchInput) {
        let searchTimeout = null;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(function() {
                currentPage = 1;
                loadEvents();
            }, 500);
        });
    }
    
    const clearFiltersBtn = document.getElementById('clear-filters');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', function() {
            const form = document.getElementById('search-form');
            if (form) form.reset();
            currentPage = 1;
            currentFilters = {};
            loadEvents();
        });
    }
    
    const pageSizeSelect = document.getElementById('page-size');
    if (pageSizeSelect) {
        pageSizeSelect.addEventListener('change', function() {
            pageSize = parseInt(this.value);
            currentPage = 1;
            loadEvents();
        });
    }
    
    const exportJsonBtn = document.getElementById('export-json');
    const exportCsvBtn = document.getElementById('export-csv');
    if (exportJsonBtn) exportJsonBtn.addEventListener('click', () => exportData('json'));
    if (exportCsvBtn) exportCsvBtn.addEventListener('click', () => exportData('csv'));
    
    const closeModalBtn = document.getElementById('close-modal');
    const eventModal = document.getElementById('event-modal');
    if (closeModalBtn) closeModalBtn.addEventListener('click', closeModal);
    if (eventModal) {
        eventModal.addEventListener('click', function(e) {
            if (e.target === this) closeModal();
        });
    }
    
    const tableBody = document.getElementById('events-table-body');
    if (tableBody) {
        tableBody.addEventListener('click', function(e) {
            const row = e.target.closest('.event-row');
            if (row && row.dataset.eventId) {
                const event = currentEvents.find(evt => evt._id === Number(row.dataset.eventId));
                if (event) {
                    showEventDetail(event);
                }
            }
        });
    }
    
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') closeModal();
    });
});

function getFilters() {
    return {
        query: document.getElementById('search-query')?.value || undefined,
        hostname: document.getElementById('search-hostname')?.value || undefined,
        start_date: document.getElementById('search-start-date')?.value || undefined,
        end_date: document.getElementById('search-end-date')?.value || undefined,
        severity: document.getElementById('search-severity')?.value || undefined,
        event_type: document.getElementById('search-event-type')?.value || undefined,
        page: currentPage,
        page_size: pageSize
    };
}

async function loadEvents() {
    if (isLoading) {
        console.log('Запрос уже выполняется, пропуск...');
        return;
    }
    
    isLoading = true;
    const tbody = document.getElementById('events-table-body');
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center p-8 text-gray-500">
                    Загрузка событий...
                </td>
            </tr>
        `;
    }
    
    currentFilters = getFilters();
    const params = new URLSearchParams();
    Object.entries(currentFilters).forEach(([key, value]) => {
        if (value !== undefined && value !== '') {
            params.append(key, value);
        }
    });
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    
    try {
        const response = await fetch(`/api/events?${params.toString()}`, {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (response.status === 401) {
            if (tbody) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="7" class="text-center p-8 text-red-500">
                            <strong>Требуется аутентификация</strong><br>
                            Ваша сессия могла истечь. Пожалуйста, <a href="/login" class="underline">войдите снова</a>.
                        </td>
                    </tr>
                `;
            }
            return;
        }
        
        if (response.status === 502 || response.status === 503) {
            if (tbody) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="7" class="text-center p-8 text-red-500">
                            <strong>Ошибка подключения к базе данных</strong><br>
                            Не удалось подключиться к серверу базы данных. Попробуйте позже.
                        </td>
                    </tr>
                `;
            }
            return;
        }
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        totalEvents = data.total || 0;
        currentEvents = data.events || [];
        updateResultsInfo();
        renderEvents(currentEvents);
        renderPagination(data.total_pages || 1);
        
    } catch (error) {
        clearTimeout(timeoutId);
        console.error('Ошибка загрузки событий:', error);
        
        if (!tbody) return;
        
        if (error.name === 'AbortError') {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center p-8 text-red-500">
                        <strong>Превышено время ожидания</strong><br>
                        Сервер слишком долго отвечает. Попробуйте снова.
                    </td>
                </tr>
            `;
        } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center p-8 text-red-500">
                        <strong>Ошибка сети</strong><br>
                        Не удалось подключиться к серверу. Проверьте соединение.
                    </td>
                </tr>
            `;
        } else {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center p-8 text-red-500">
                        <strong>Ошибка загрузки событий</strong><br>
                        ${escapeHtml(error.message)}<br>
                        <button onclick="loadEvents()" class="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                            Повторить
                        </button>
                    </td>
                </tr>
            `;
        }
    } finally {
        isLoading = false;
    }
}

function renderEvents(events) {
    const tbody = document.getElementById('events-table-body');
    if (!tbody) return;
    
    if (events.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center p-8 text-gray-500">
                    События не найдены по заданным критериям.
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = events.map(event => `
        <tr class="event-row border-b border-gray-100 hover:bg-gray-50 cursor-pointer" data-event-id="${escapeHtml(event._id || '')}">
            <td class="p-3 text-sm">${formatTimestamp(event.timestamp)}</td>
            <td class="p-3 text-sm font-medium">${escapeHtml(event.hostname || '-')}</td>
            <td class="p-3 text-sm">${escapeHtml(event.source || '-')}</td>
            <td class="p-3 text-sm">${escapeHtml(event.event_type || '-')}</td>
            <td class="p-3 text-sm">
                <span class="severity-${(event.severity || 'low').toLowerCase()}">
                    ${escapeHtml(event.severity || '-')}
                </span>
            </td>
            <td class="p-3 text-sm">${escapeHtml(event.user || '-')}</td>
            <td class="p-3 text-sm">${escapeHtml(event.process || '-')}</td>
        </tr>
    `).join('');
}

function renderPagination(totalPages) {
    const container = document.getElementById('pagination');
    if (!container) return;
    
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = '';
    
    html += `
        <button onclick="goToPage(${currentPage - 1})" 
                ${currentPage === 1 ? 'disabled' : ''}
                class="px-3 py-1 rounded ${currentPage === 1 ? 'bg-gray-200 text-gray-400 cursor-not-allowed' : 'bg-blue-500 text-white hover:bg-blue-600'}">
            ← Назад
        </button>
    `;
    
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    if (startPage > 1) {
        html += `<button onclick="goToPage(1)" class="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300">1</button>`;
        if (startPage > 2) html += `<span class="px-2">...</span>`;
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <button onclick="goToPage(${i})" 
                    class="px-3 py-1 rounded ${i === currentPage ? 'bg-blue-500 text-white' : 'bg-gray-200 hover:bg-gray-300'}">
                ${i}
            </button>
        `;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) html += `<span class="px-2">...</span>`;
        html += `<button onclick="goToPage(${totalPages})" class="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300">${totalPages}</button>`;
    }
    
    html += `
        <button onclick="goToPage(${currentPage + 1})" 
                ${currentPage === totalPages ? 'disabled' : ''}
                class="px-3 py-1 rounded ${currentPage === totalPages ? 'bg-gray-200 text-gray-400 cursor-not-allowed' : 'bg-blue-500 text-white hover:bg-blue-600'}">
            Вперёд →
        </button>
    `;
    
    container.innerHTML = html;
}

function goToPage(page) {
    currentPage = page;
    loadEvents();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function updateResultsInfo() {
    const resultsInfo = document.getElementById('results-info');
    if (!resultsInfo) return;
    
    const start = (currentPage - 1) * pageSize + 1;
    const end = Math.min(currentPage * pageSize, totalEvents);
    resultsInfo.textContent = 
        totalEvents > 0 
            ? `Показано ${start}-${end} из ${totalEvents} событий`
            : 'События не найдены';
}

function showEventDetail(event) {
    const content = document.getElementById('event-detail-content');
    const modal = document.getElementById('event-modal');
    
    if (!content || !modal) return;
    
    content.innerHTML = `
        <div class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="text-sm font-medium text-gray-500">ID</label>
                    <p class="text-gray-800">${event._id || '-'}</p>
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-500">Время</label>
                    <p class="text-gray-800">${formatTimestamp(event.timestamp)}</p>
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-500">Хост</label>
                    <p class="text-gray-800">${escapeHtml(event.hostname || '-')}</p>
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-500">Источник</label>
                    <p class="text-gray-800">${escapeHtml(event.source || '-')}</p>
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-500">Тип события</label>
                    <p class="text-gray-800">${escapeHtml(event.event_type || '-')}</p>
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-500">Критичность</label>
                    <p class="severity-${(event.severity || 'low').toLowerCase()}">${escapeHtml(event.severity || '-')}</p>
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-500">Пользователь</label>
                    <p class="text-gray-800">${escapeHtml(event.user || '-')}</p>
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-500">Процесс</label>
                    <p class="text-gray-800">${escapeHtml(event.process || '-')}</p>
                </div>
            </div>
            ${event.command ? `
            <div>
                <label class="text-sm font-medium text-gray-500">Команда</label>
                <p class="text-gray-800 font-mono bg-gray-100 p-2 rounded">${escapeHtml(event.command)}</p>
            </div>
            ` : ''}
            <div>
                <label class="text-sm font-medium text-gray-500">Исходный лог</label>
                <pre class="text-gray-800 bg-gray-100 p-3 rounded text-sm overflow-x-auto whitespace-pre-wrap">${escapeHtml(event.raw_log || '-')}</pre>
            </div>
        </div>
    `;
    modal.classList.remove('hidden');
}

function closeModal() {
    const modal = document.getElementById('event-modal');
    if (modal) modal.classList.add('hidden');
}

async function exportData(format) {
    const filters = getFilters();
    delete filters.page;
    delete filters.page_size;
    
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== '') {
            params.append(key, value);
        }
    });
    params.append('format', format);
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);
    
    try {
        const response = await fetch(`/api/events/export?${params.toString()}`, {
            credentials: 'include',
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (response.status === 401) {
            alert('Требуется аутентификация. Пожалуйста, войдите снова.');
            window.location.href = '/login';
            return;
        }
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Ошибка экспорта: ${response.status} ${response.statusText}`);
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `events_export_${new Date().toISOString().slice(0,10)}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
    } catch (error) {
        clearTimeout(timeoutId);
        console.error('Ошибка экспорта:', error);
        
        if (error.name === 'AbortError') {
            alert('Превышено время ожидания экспорта. Попробуйте экспортировать меньше событий.');
        } else {
            alert(`Не удалось экспортировать данные: ${error.message}`);
        }
    }
}