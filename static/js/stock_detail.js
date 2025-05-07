document.addEventListener('DOMContentLoaded', function() {
    // Initialize price history chart
    initializePriceHistoryChart();
    
    // Setup period selectors
    setupPeriodSelectors();
    
    // Calculate and display 52-week statistics
    calculate52WeekStats();
});

/**
 * Initialize the price history chart
 */
function initializePriceHistoryChart() {
    const priceDataElement = document.getElementById('priceData');
    if (!priceDataElement) return;
    
    try {
        const priceData = JSON.parse(priceDataElement.textContent);
        
        if (!priceData || priceData.length === 0) {
            document.getElementById('priceHistoryChart').parentNode.innerHTML = 
                '<div class="alert alert-info text-center">No price history available for this stock.</div>';
            return;
        }
        
        // Sort data by date in ascending order
        priceData.sort((a, b) => new Date(a.date) - new Date(b.date));
        
        // Extract dates and prices for the chart
        const dates = priceData.map(item => {
            const date = new Date(item.date);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });
        
        const prices = priceData.map(item => item.close_price);
        const volumes = priceData.map(item => item.volume || 0);
        
        // Calculate the max volume for scaling
        const maxVolume = Math.max(...volumes);
        const volumeScaleFactor = maxVolume > 0 ? (Math.max(...prices) / maxVolume) * 0.3 : 0;
        
        // Calculate line color based on price trend
        const startPrice = prices[0];
        const endPrice = prices[prices.length - 1];
        const lineColor = endPrice >= startPrice ? 'rgba(75, 192, 192, 1)' : 'rgba(255, 99, 132, 1)';
        const gradientColor = endPrice >= startPrice ? 'rgba(75, 192, 192, 0.2)' : 'rgba(255, 99, 132, 0.2)';
        
        const ctx = document.getElementById('priceHistoryChart').getContext('2d');
        
        // Create a gradient fill
        let gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, gradientColor);
        gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
        
        window.priceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'Price',
                        data: prices,
                        borderColor: lineColor,
                        backgroundColor: gradient,
                        borderWidth: 2,
                        pointRadius: 1,
                        pointHoverRadius: 5,
                        fill: 'start',
                        tension: 0.4,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Volume',
                        data: volumes.map(vol => vol * volumeScaleFactor),
                        backgroundColor: 'rgba(128, 128, 128, 0.3)',
                        borderColor: 'rgba(128, 128, 128, 0.5)',
                        borderWidth: 1,
                        type: 'bar',
                        yAxisID: 'y'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            filter: function(item) {
                                // Only show the Price label, hide Volume
                                return item.text === 'Price';
                            }
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                const datasetLabel = context.dataset.label;
                                if (datasetLabel === 'Price') {
                                    return `Price: ${context.raw}`;
                                } else if (datasetLabel === 'Volume') {
                                    // Display the actual volume, not the scaled value
                                    return `Volume: ${volumes[context.dataIndex].toLocaleString()}`;
                                }
                                return datasetLabel + ': ' + context.raw;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        position: 'right',
                        grid: {
                            borderDash: [2, 4],
                            drawBorder: false,
                        }
                    }
                },
                elements: {
                    line: {
                        tension: 0.4
                    }
                }
            }
        });
        
    } catch (error) {
        console.error('Error initializing price history chart:', error);
        document.getElementById('priceHistoryChart').parentNode.innerHTML = 
            '<div class="alert alert-warning text-center">Error loading price history chart.</div>';
    }
}

/**
 * Setup period selectors for the price chart
 */
function setupPeriodSelectors() {
    const periodButtons = document.querySelectorAll('[data-period]');
    
    periodButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            periodButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Update chart with selected period
            updateChartPeriod(this.getAttribute('data-period'));
        });
    });
}

/**
 * Update the chart to show the selected time period
 */
function updateChartPeriod(period) {
    const priceDataElement = document.getElementById('priceData');
    if (!priceDataElement || !window.priceChart) return;
    
    try {
        const priceData = JSON.parse(priceDataElement.textContent);
        
        if (!priceData || priceData.length === 0) return;
        
        // Sort data by date in ascending order
        priceData.sort((a, b) => new Date(a.date) - new Date(b.date));
        
        // Filter data based on selected period
        let filteredData;
        const now = new Date();
        
        switch (period) {
            case '1M':
                const oneMonthAgo = new Date();
                oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);
                filteredData = priceData.filter(item => new Date(item.date) >= oneMonthAgo);
                break;
            case '3M':
                const threeMonthsAgo = new Date();
                threeMonthsAgo.setMonth(threeMonthsAgo.getMonth() - 3);
                filteredData = priceData.filter(item => new Date(item.date) >= threeMonthsAgo);
                break;
            case '6M':
                const sixMonthsAgo = new Date();
                sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);
                filteredData = priceData.filter(item => new Date(item.date) >= sixMonthsAgo);
                break;
            case '1Y':
                const oneYearAgo = new Date();
                oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);
                filteredData = priceData.filter(item => new Date(item.date) >= oneYearAgo);
                break;
            case 'ALL':
            default:
                filteredData = priceData;
                break;
        }
        
        // Update chart data
        const dates = filteredData.map(item => {
            const date = new Date(item.date);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });
        
        const prices = filteredData.map(item => item.close_price);
        const volumes = filteredData.map(item => item.volume || 0);
        
        // Calculate the max volume for scaling
        const maxVolume = Math.max(...volumes);
        const volumeScaleFactor = maxVolume > 0 ? (Math.max(...prices) / maxVolume) * 0.3 : 0;
        
        // Update chart datasets
        window.priceChart.data.labels = dates;
        window.priceChart.data.datasets[0].data = prices;
        window.priceChart.data.datasets[1].data = volumes.map(vol => vol * volumeScaleFactor);
        
        // Update line color based on new data range
        const startPrice = prices[0];
        const endPrice = prices[prices.length - 1];
        const lineColor = endPrice >= startPrice ? 'rgba(75, 192, 192, 1)' : 'rgba(255, 99, 132, 1)';
        const gradientColor = endPrice >= startPrice ? 'rgba(75, 192, 192, 0.2)' : 'rgba(255, 99, 132, 0.2)';
        
        window.priceChart.data.datasets[0].borderColor = lineColor;
        
        // Update gradient
        const ctx = document.getElementById('priceHistoryChart').getContext('2d');
        let gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, gradientColor);
        gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
        window.priceChart.data.datasets[0].backgroundColor = gradient;
        
        window.priceChart.update();
        
    } catch (error) {
        console.error('Error updating chart period:', error);
    }
}

/**
 * Calculate and display 52-week statistics
 */
function calculate52WeekStats() {
    const priceDataElement = document.getElementById('priceData');
    if (!priceDataElement) return;
    
    try {
        const priceData = JSON.parse(priceDataElement.textContent);
        
        if (!priceData || priceData.length === 0) {
            document.getElementById('stat-52wk-high').textContent = 'N/A';
            document.getElementById('stat-52wk-low').textContent = 'N/A';
            document.getElementById('stat-52wk-change').textContent = 'N/A';
            return;
        }
        
        // Get currency from the DOM
        const currentPriceText = document.getElementById('current-price').textContent;
        const currency = currentPriceText.split(' ').pop().trim();
        
        // Filter to last 52 weeks
        const oneYearAgo = new Date();
        oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);
        
        const yearData = priceData.filter(item => new Date(item.date) >= oneYearAgo);
        
        if (yearData.length === 0) {
            document.getElementById('stat-52wk-high').textContent = 'N/A';
            document.getElementById('stat-52wk-low').textContent = 'N/A';
            document.getElementById('stat-52wk-change').textContent = 'N/A';
            return;
        }
        
        // Find 52-week high and low
        const high52wk = Math.max(...yearData.map(item => item.close_price));
        const low52wk = Math.min(...yearData.map(item => item.close_price));
        
        // Calculate 52-week change
        const oldestPrice = yearData[0].close_price;
        const latestPrice = yearData[yearData.length - 1].close_price;
        const change52wk = ((latestPrice - oldestPrice) / oldestPrice) * 100;
        
        // Update the DOM
        document.getElementById('stat-52wk-high').textContent = `${high52wk.toFixed(2)} ${currency}`;
        document.getElementById('stat-52wk-low').textContent = `${low52wk.toFixed(2)} ${currency}`;
        
        const changeElement = document.getElementById('stat-52wk-change');
        const changeClass = change52wk >= 0 ? 'text-success' : 'text-danger';
        const changePrefix = change52wk >= 0 ? '+' : '';
        
        changeElement.innerHTML = `<span class="${changeClass}">${changePrefix}${change52wk.toFixed(2)}%</span>`;
        
    } catch (error) {
        console.error('Error calculating 52-week stats:', error);
        document.getElementById('stat-52wk-high').textContent = 'Error';
        document.getElementById('stat-52wk-low').textContent = 'Error';
        document.getElementById('stat-52wk-change').textContent = 'Error';
    }
}
