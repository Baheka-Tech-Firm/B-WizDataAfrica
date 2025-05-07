document.addEventListener('DOMContentLoaded', function() {
    // Initialize data and charts
    fetchDashboardData();
    initializeMarketPerformanceChart();
    
    // Setup event listeners
    setupTimeframeSelector();
    setupExchangeFilters();
    
    // Fetch the latest market summary
    fetchLatestMarketSummary();
});

/**
 * Fetch dashboard data including stats and top movers
 */
function fetchDashboardData() {
    // Fetch stock count
    fetch('/api/v1/stocks?limit=1', {
        headers: {'X-API-Token': getApiToken()}
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        // Update stocks count using the pagination total or response length
        document.getElementById('stocks-count').textContent = 
            data.total || data.length > 0 ? data.length : '0';
    })
    .catch(error => {
        console.error('Error fetching stocks count:', error);
        document.getElementById('stocks-count').textContent = 'N/A';
    });
    
    // Fetch indices count
    fetch('/api/v1/indices?limit=1', {
        headers: {'X-API-Token': getApiToken()}
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        document.getElementById('indices-count').textContent = 
            data.total || data.length > 0 ? data.length : '0';
    })
    .catch(error => {
        console.error('Error fetching indices count:', error);
        document.getElementById('indices-count').textContent = 'N/A';
    });
    
    // Set a placeholder for data points (this would typically be a count of price records)
    document.getElementById('data-points').textContent = '10,000+';
    
    // Fetch top gainers
    fetchTopMovers('gainers');
    
    // Fetch top losers
    fetchTopMovers('losers');
}

/**
 * Fetch top market movers (gainers or losers)
 */
function fetchTopMovers(type, exchange = 'all') {
    const endpoint = type === 'gainers' 
        ? `/api/v1/stocks?sort=change_desc&limit=5${exchange !== 'all' ? `&exchange=${exchange}` : ''}`
        : `/api/v1/stocks?sort=change_asc&limit=5${exchange !== 'all' ? `&exchange=${exchange}` : ''}`;
    
    fetch(endpoint, {
        headers: {'X-API-Token': getApiToken()}
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        // Update table with the stock data
        const tableId = type === 'gainers' ? 'top-gainers-table' : 'top-losers-table';
        const table = document.getElementById(tableId);
        
        if (!data || data.length === 0) {
            table.innerHTML = `<tr><td colspan="4" class="text-center py-3">No data available</td></tr>`;
            return;
        }
        
        let html = '';
        data.forEach(stock => {
            const changeClass = stock.change_percent > 0 ? 'text-success' : 'text-danger';
            const changeSign = stock.change_percent > 0 ? '+' : '';
            
            html += `
                <tr>
                    <td><a href="/stock/${stock.ticker}">${stock.ticker}</a></td>
                    <td>${stock.exchange}</td>
                    <td>${stock.last_price || 'N/A'} ${stock.currency || ''}</td>
                    <td class="${changeClass}">${changeSign}${stock.change_percent || 0}%</td>
                </tr>
            `;
        });
        
        table.innerHTML = html;
    })
    .catch(error => {
        console.error(`Error fetching top ${type}:`, error);
        const tableId = type === 'gainers' ? 'top-gainers-table' : 'top-losers-table';
        document.getElementById(tableId).innerHTML = 
            `<tr><td colspan="4" class="text-center py-3">Error loading data</td></tr>`;
    });
}

/**
 * Initialize the market performance chart
 */
function initializeMarketPerformanceChart(days = 7) {
    const ctx = document.getElementById('marketPerformanceChart').getContext('2d');
    
    // Generate some placeholder dates for the x-axis
    const labels = [];
    const now = new Date();
    for (let i = days - 1; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
    }
    
    // We'll fetch actual data from each exchange's main index
    fetchMarketIndexData(days)
        .then(data => {
            // Create the chart
            window.marketChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: data
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                display: false
                            }
                        },
                        y: {
                            grid: {
                                borderDash: [2, 4],
                                drawBorder: false,
                            },
                            ticks: {
                                // Include a percent sign in the ticks
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        }
                    },
                    elements: {
                        line: {
                            tension: 0.4
                        },
                        point: {
                            radius: 3,
                            hoverRadius: 5
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error initializing market performance chart:', error);
            document.getElementById('marketPerformanceChart').parentNode.innerHTML = 
                '<div class="alert alert-warning text-center">Error loading market performance data</div>';
        });
}

/**
 * Fetch market index data for the performance chart
 */
function fetchMarketIndexData(days) {
    // For demonstration purposes, we'll generate some mock data
    // In a real implementation, this would fetch from the API
    return new Promise((resolve) => {
        const colors = [
            { borderColor: 'rgba(75, 192, 192, 1)', backgroundColor: 'rgba(75, 192, 192, 0.2)' },
            { borderColor: 'rgba(255, 159, 64, 1)', backgroundColor: 'rgba(255, 159, 64, 0.2)' },
            { borderColor: 'rgba(54, 162, 235, 1)', backgroundColor: 'rgba(54, 162, 235, 0.2)' }
        ];
        
        const exchanges = ['JSE All Share', 'NGX All Share', 'BRVM Composite'];
        
        const datasets = exchanges.map((exchange, index) => {
            // Generate random performance data between -5% and +5%
            const performanceData = Array(days).fill().map(() => {
                return (Math.random() * 10 - 5).toFixed(2);
            });
            
            return {
                label: exchange,
                data: performanceData,
                borderColor: colors[index].borderColor,
                backgroundColor: colors[index].backgroundColor,
                borderWidth: 2,
                fill: false,
                pointBackgroundColor: colors[index].borderColor
            };
        });
        
        resolve(datasets);
    });
}

/**
 * Setup event listeners for the timeframe selector dropdown
 */
function setupTimeframeSelector() {
    const dropdownItems = document.querySelectorAll('#timeframeDropdown + .dropdown-menu .dropdown-item');
    
    dropdownItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const days = parseInt(this.getAttribute('data-days'));
            document.getElementById('timeframeDropdown').textContent = this.textContent;
            
            // Update the chart with the new timeframe
            if (window.marketChart) {
                window.marketChart.destroy();
            }
            initializeMarketPerformanceChart(days);
        });
    });
    
    // Refresh button for exchange list
    const refreshBtn = document.getElementById('refreshExchangeBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            // Add rotation animation
            this.classList.add('fa-spin');
            
            // Fetch updated exchange data
            setTimeout(() => {
                this.classList.remove('fa-spin');
            }, 1000);
        });
    }
}

/**
 * Setup event listeners for exchange filters
 */
function setupExchangeFilters() {
    // For gainers dropdown
    const gainersDropdownItems = document.querySelectorAll('#exchangeGainersDropdown + .dropdown-menu .dropdown-item');
    
    gainersDropdownItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const exchange = this.getAttribute('data-exchange');
            document.getElementById('exchangeGainersDropdown').textContent = this.textContent;
            
            // Fetch top gainers for the selected exchange
            fetchTopMovers('gainers', exchange);
        });
    });
    
    // For losers dropdown
    const losersDropdownItems = document.querySelectorAll('#exchangeLosersDropdown + .dropdown-menu .dropdown-item');
    
    losersDropdownItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const exchange = this.getAttribute('data-exchange');
            document.getElementById('exchangeLosersDropdown').textContent = this.textContent;
            
            // Fetch top losers for the selected exchange
            fetchTopMovers('losers', exchange);
        });
    });
}

/**
 * Fetch the latest market summary
 */
function fetchLatestMarketSummary() {
    fetch('/api/v1/market-summaries?limit=1', {
        headers: {'X-API-Token': getApiToken()}
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        if (data && data.length > 0) {
            const summary = data[0];
            const previewElem = document.getElementById('market-summary-preview');
            
            // Display summary highlights
            if (summary.highlights) {
                previewElem.innerHTML = `<p class="summary-highlights">${summary.highlights.split('\n').slice(0, 3).join('<br>')}</p>`;
            } else {
                previewElem.innerHTML = `<p class="text-muted">No highlights available for the latest market summary.</p>`;
            }
        }
    })
    .catch(error => {
        console.error('Error fetching market summary:', error);
        document.getElementById('market-summary-preview').innerHTML = 
            `<p class="text-muted">Could not load the latest market summary.</p>`;
    });
}

/**
 * Get the API token from localStorage or prompt the user to get one
 */
function getApiToken() {
    const token = localStorage.getItem('apiToken');
    if (!token) {
        // This is just a placeholder. In a real app, you would have a proper
        // authentication flow to get an API token
        return 'demo_token';
    }
    return token;
}
