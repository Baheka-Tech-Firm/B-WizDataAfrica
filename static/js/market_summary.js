document.addEventListener('DOMContentLoaded', function() {
    // Initialize market indicators chart
    initializeMarketIndicatorsChart();
    
    // Setup summary date selectors
    setupSummarySelectors();
});

/**
 * Initialize the market indicators chart
 */
function initializeMarketIndicatorsChart() {
    const ctx = document.getElementById('marketIndicatorsChart');
    if (!ctx) return;
    
    // Get summary data
    const summaryDataElement = document.getElementById('summaryData');
    if (!summaryDataElement) return;
    
    try {
        const summaries = JSON.parse(summaryDataElement.textContent);
        
        if (!summaries || summaries.length === 0) {
            ctx.parentNode.innerHTML = '<div class="alert alert-info text-center">No market data available.</div>';
            return;
        }
        
        // Extract dates in reverse (oldest first)
        const dates = summaries.map(summary => {
            const date = new Date(summary.date);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        }).reverse();
        
        // Generate random indicator data for the chart
        // In a real implementation, this would be extracted from the summary content
        // or fetched from a separate API endpoint
        const generateIndicatorData = (length, min, max) => {
            return Array(length).fill().map(() => {
                return min + Math.random() * (max - min);
            });
        };
        
        const marketIndexData = generateIndicatorData(dates.length, 95, 105);
        const volumeData = generateIndicatorData(dates.length, 70, 130);
        const sentimentData = generateIndicatorData(dates.length, -10, 10);
        
        // Create chart
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'Market Index',
                        data: marketIndexData,
                        borderColor: 'rgba(75, 192, 192, 1)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        yAxisID: 'y',
                        tension: 0.4
                    },
                    {
                        label: 'Trading Volume',
                        data: volumeData,
                        borderColor: 'rgba(153, 102, 255, 1)',
                        backgroundColor: 'rgba(153, 102, 255, 0.2)',
                        yAxisID: 'y1',
                        tension: 0.4
                    },
                    {
                        label: 'Market Sentiment',
                        data: sentimentData,
                        borderColor: 'rgba(255, 159, 64, 1)',
                        backgroundColor: 'rgba(255, 159, 64, 0.2)',
                        yAxisID: 'y2',
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Index (Normalized)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: false,
                        position: 'right',
                        grid: {
                            drawOnChartArea: false,
                        }
                    },
                    y2: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Sentiment'
                        },
                        grid: {
                            drawOnChartArea: false,
                        }
                    }
                }
            }
        });
        
    } catch (error) {
        console.error('Error initializing market indicators chart:', error);
        ctx.parentNode.innerHTML = '<div class="alert alert-warning text-center">Error loading market indicators chart.</div>';
    }
}

/**
 * Setup summary date selectors
 */
function setupSummarySelectors() {
    // Get all summary links
    const summaryLinks = document.querySelectorAll('.summary-link, .dropdown-item[data-summary-id]');
    
    summaryLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const summaryId = this.getAttribute('data-summary-id');
            if (!summaryId) return;
            
            // Get summary data
            const summaryDataElement = document.getElementById('summaryData');
            if (!summaryDataElement) return;
            
            try {
                const summaries = JSON.parse(summaryDataElement.textContent);
                const summary = summaries.find(s => s.id == summaryId);
                
                if (!summary) {
                    console.error('Summary not found:', summaryId);
                    return;
                }
                
                // Update current summary
                updateCurrentSummary(summary);
                
                // Update dropdown button text if clicked from dropdown
                if (this.classList.contains('dropdown-item')) {
                    const dropdownButton = document.getElementById('summaryDateDropdown');
                    if (dropdownButton) {
                        const date = new Date(summary.date);
                        dropdownButton.textContent = date.toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' });
                    }
                }
                
                // Update active state of summary links
                summaryLinks.forEach(link => {
                    if (link.getAttribute('data-summary-id') == summaryId) {
                        link.classList.add('active');
                    } else {
                        link.classList.remove('active');
                    }
                });
                
            } catch (error) {
                console.error('Error loading summary:', error);
            }
        });
    });
}

/**
 * Update the current summary display
 */
function updateCurrentSummary(summary) {
    const currentSummaryElement = document.getElementById('current-summary');
    if (!currentSummaryElement) return;
    
    const date = new Date(summary.date);
    const formattedDate = date.toLocaleDateString('en-US', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
    const createdDate = new Date(summary.created_at);
    const formattedCreatedDate = createdDate.toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    
    let highlightsHtml = '';
    if (summary.highlights) {
        highlightsHtml = `
            <div class="card bg-dark mb-4">
                <div class="card-body">
                    <h5 class="card-title"><i class="fas fa-star me-2"></i>Market Highlights</h5>
                    <div class="highlights-section">
                        ${summary.highlights.split('\n').join('<br>')}
                    </div>
                </div>
            </div>
        `;
    }
    
    // Format the content with markdown-like formatting
    let formattedContent = summary.content;
    
    // Convert headers (## Header)
    formattedContent = formattedContent.replace(/## (.*?)(\n|$)/g, '<h4>$1</h4>');
    
    // Convert subheaders (### Subheader)
    formattedContent = formattedContent.replace(/### (.*?)(\n|$)/g, '<h5>$1</h5>');
    
    // Convert bullet points
    formattedContent = formattedContent.replace(/- (.*?)(\n|$)/g, '<li>$1</li>');
    formattedContent = formattedContent.replace(/<li>(.*?)<\/li>/g, '<ul><li>$1</li></ul>');
    formattedContent = formattedContent.replace(/<\/ul><ul>/g, '');
    
    // Convert line breaks
    formattedContent = formattedContent.replace(/\n\n/g, '<br><br>');
    
    currentSummaryElement.innerHTML = `
        <h3 class="mb-3">${summary.title}</h3>
        
        <div class="d-flex align-items-center mb-4">
            <div class="me-4">
                <span class="badge bg-primary">${formattedDate}</span>
            </div>
            <div class="small text-muted">
                Generated on ${formattedCreatedDate}
            </div>
        </div>
        
        ${highlightsHtml}
        
        <div class="summary-content">
            ${formattedContent}
        </div>
    `;
}
