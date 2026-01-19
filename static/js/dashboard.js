const DashboardController = {
    charts: {},
    widgetStates: {},
    abortController: null,
    
    widgets: {
        'active-agents': { 
            endpoint: '/api/dashboard/active-agents', 
            containerId: 'active-agents-content', 
            renderer: 'renderActiveAgents' 
        },
        'recent-logins': { 
            endpoint: '/api/dashboard/recent-logins', 
            containerId: 'recent-logins-content', 
            renderer: 'renderRecentLogins' 
        },
        'host-list': { 
            endpoint: '/api/dashboard/hosts', 
            containerId: 'host-list-content', 
            renderer: 'renderHostList' 
        },
        'events-by-type': { 
            endpoint: '/api/dashboard/events-by-type', 
            containerId: 'events-by-type-content', 
            isChart: true, 
            renderer: 'renderEventsByType' 
        },
        'events-by-severity': { 
            endpoint: '/api/dashboard/events-by-severity', 
            containerId: 'events-by-severity-content', 
            isChart: true, 
            renderer: 'renderEventsBySeverity' 
        },
        'top-users': { 
            endpoint: '/api/dashboard/top-users', 
            containerId: 'top-users-content', 
            renderer: 'renderTopUsers' 
        },
        'top-processes': { 
            endpoint: '/api/dashboard/top-processes', 
            containerId: 'top-processes-content', 
            renderer: 'renderTopProcesses' 
        },
        'event-timeline': { 
            endpoint: '/api/dashboard/timeline', 
            containerId: 'event-timeline-content', 
            isChart: true, 
            renderer: 'renderEventTimeline' 
        }
    },

    init() {
        this.initializeCharts();
        
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshAll());
        }
        
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) { 
                stopAutoRefresh(); 
                this.abortController?.abort(); 
            } else { 
                this.refreshAll(); 
                startAutoRefresh(() => this.refreshAll()); 
            }
        });
        
        this.refreshAll();
        startAutoRefresh(() => this.refreshAll());
    },

    initializeCharts() {
        if (typeof Chart === 'undefined') return;
        
        const create = (id, type, config) => { 
            const ctx = document.getElementById(id); 
            return ctx ? new Chart(ctx, { type, ...config }) : null; 
        };
        
        this.charts.eventsType = create('events-type-chart', 'doughnut', {
            data: { 
                labels: [], 
                datasets: [{ data: [], backgroundColor: CHART_COLORS }] 
            }, 
            options: DOUGHNUT_OPTIONS
        });
        
        this.charts.severity = create('severity-chart', 'doughnut', {
            data: { 
                labels: ['Низкая', 'Средняя', 'Высокая', 'Критическая'], 
                datasets: [{ data: [0, 0, 0, 0], backgroundColor: SEVERITY_COLORS }] 
            }, 
            options: DOUGHNUT_OPTIONS
        });
        
        this.charts.timeline = create('timeline-chart', 'bar', {
            data: { 
                labels: Array.from({length: 24}, (_, i) => `${i}:00`), 
                datasets: [{ 
                    label: 'События', 
                    data: Array(24).fill(0), 
                    backgroundColor: '#3b82f6' 
                }] 
            },
            options: { 
                responsive: true, 
                maintainAspectRatio: false, 
                scales: { 
                    y: { beginAtZero: true }, 
                    x: { ticks: { font: { size: 8 }, maxRotation: 45 } } 
                }, 
                plugins: { legend: { display: false } } 
            }
        });
    },
    
    async refreshAll() {
        this.abortController?.abort();
        this.abortController = new AbortController();
        this.updateLastRefreshTime();
        
        Object.values(this.widgets).forEach(w => {
            if (!w.isChart) {
                const container = document.getElementById(w.containerId);
                if (container) {
                    container.replaceChildren(Object.assign(document.createElement('div'), {
                        className: 'flex justify-center py-4', 
                        innerHTML: '<div class="loading-spinner"></div>'
                    }));
                }
            }
        });
        
        await Promise.allSettled(
            Object.keys(this.widgets).map(name => this.refreshWidget(name))
        );
    },

    async refreshWidget(widgetName) {
        const widget = this.widgets[widgetName];
        if (!widget) return;
        
        const container = document.getElementById(widget.containerId);
        try {
            const response = await apiRequest(widget.endpoint, { 
                signal: this.abortController?.signal 
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            if (data.error) return this.setWidgetError(widgetName, container, data.error);
            
            this[widget.renderer]?.(data, container);
            this.widgetStates[widgetName] = { status: 'ok' };
            
            const card = document.querySelector(`[data-widget="${widgetName}"]`);
            if (card) {
                card.classList.remove('widget-error');
                card.querySelector('.error-dot')?.remove();
            }
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error(`Ошибка загрузки ${widgetName}:`, error);
                this.setWidgetError(widgetName, container, error.message);
            }
        }
    },

    setWidgetError(widgetName, container, message) {
        this.widgetStates[widgetName] = { status: 'error', message };
        
        if (container) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <p class="text-red-500 text-sm">Ошибка загрузки данных</p>
                    <button onclick="DashboardController.refreshWidget('${widgetName}')" 
                            class="text-blue-500 text-xs hover:underline mt-2">
                        Повторить
                    </button>
                </div>`;
        }
        
        const card = document.querySelector(`[data-widget="${widgetName}"]`);
        if (card) {
            card.classList.add('widget-error');
            const header = card.querySelector('h2');
            if (header && !header.querySelector('.error-dot')) {
                header.insertAdjacentHTML('beforeend', 
                    '<span class="error-dot inline-block w-2 h-2 bg-red-500 rounded-full ml-2" title="Ошибка загрузки данных"></span>'
                );
            }
        }
    },

    updateLastRefreshTime() {
        const el = document.getElementById('last-update');
        if (el) {
            el.textContent = `Последнее обновление: ${new Date().toLocaleTimeString('ru-RU')}`;
        }
    },

    renderActiveAgents(data, container) {
        renderListWidget(
            container, 
            data.agents || [], 
            'Нет активных агентов', 
            a => `<li class="flex justify-between items-center">
                <span class="font-medium">${escapeHtml(a.agent_id)}</span>
                <span class="text-gray-500 text-xs">${formatTime(a.last_activity)}</span>
            </li>`
        );
    },

    renderRecentLogins(data, container) {
        renderListWidget(
            container, 
            (data.logins || []).slice(0, 10), 
            'Нет последних входов', 
            l => `<li class="flex justify-between items-center py-1 border-b border-gray-100">
                <span class="${l.success ? 'text-green-600' : 'text-red-600'}">
                    ${l.success ? '✓' : '✗'} ${escapeHtml(l.user)}
                </span>
                <span class="text-gray-500 text-xs">${formatTime(l.timestamp)}</span>
            </li>`
        );
    },

    renderHostList(data, container) {
        renderListWidget(
            container, 
            data.hosts || [], 
            'Хосты не найдены', 
            h => `<li class="flex justify-between items-center">
                <span class="font-medium">${escapeHtml(h.hostname)}</span>
                <span class="bg-blue-100 text-blue-800 px-2 py-0.5 rounded text-xs">
                    ${formatNumber(h.event_count)} событий
                </span>
            </li>`
        );
    },

    renderEventsByType(data) {
        if (!this.charts.eventsType) return;
        const types = data.event_types || [];
        this.charts.eventsType.data.labels = types.map(e => e.event_type);
        this.charts.eventsType.data.datasets[0].data = types.map(e => e.count);
        this.charts.eventsType.update('none');
    },

    renderEventsBySeverity(data) {
        if (!this.charts.severity) return;
        const map = { low: 0, medium: 0, high: 0, critical: 0 };
        (data.severities || []).forEach(s => { 
            const k = (s.severity || '').toLowerCase(); 
            if (k in map) map[k] = s.count; 
        });
        this.charts.severity.data.datasets[0].data = Object.values(map);
        this.charts.severity.update('none');
    },

    renderTopUsers(data, container) { 
        renderRankedList(
            container, 
            data.users || [], 
            'Нет активности пользователей', 
            'user', 
            'event_count', 
            'bg-green-100 text-green-800'
        ); 
    },

    renderTopProcesses(data, container) { 
        renderRankedList(
            container, 
            data.processes || [], 
            'Нет данных о процессах', 
            'process', 
            'event_count', 
            'bg-purple-100 text-purple-800'
        ); 
    },

    renderEventTimeline(data) {
        if (!this.charts.timeline) return;
        const hourly = Array(24).fill(0);
        (data.timeline || []).forEach(t => { 
            if (t.hour >= 0 && t.hour < 24) hourly[t.hour] = t.event_count; 
        });
        this.charts.timeline.data.datasets[0].data = hourly;
        this.charts.timeline.update('none');
    },

    destroy() {
        this.abortController?.abort();
        stopAutoRefresh();
        Object.values(this.charts).forEach(c => c?.destroy());
        this.charts = {};
    }
};
