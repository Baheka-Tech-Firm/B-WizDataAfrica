document.addEventListener('DOMContentLoaded', function() {
    // Initialize stock data
    fetchLatestPrices();
    
    // Setup event listeners
    setupSearchAndFilters();
    setupAdvancedFilters();
});

/**
 * Fetch the latest prices for stocks displayed in the table
 */
function fetchLatestPrices() {
    const priceElements = document.querySelectorAll('.stock-price');
    const changeElements = document.querySelectorAll('.stock-change');
    
    // Group by exchange to minimize API calls
    const stocksByExchange = {};
    
    priceElements.forEach(element => {
        const ticker = element.getAttribute('data-ticker');
        const exchange = element.getAttribute('data-exchange');
        
        if (!stocksByExchange[exchange]) {
            stocksByExchange[exchange] = [];
        }
        
        stocksByExchange[exchange].push(ticker);
    });
    
    // Fetch prices for each exchange
    for (const [exchange, tickers] of Object.entries(stocksByExchange)) {
        tickers.forEach(ticker => {
            fetch(`/api/v1/stocks/${exchange}/${ticker}/prices?limit=1`, {
                headers: {'X-API-Token': getApiToken()}
            })
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                if (data && data.prices && data.prices.length > 0) {
                    const price = data.prices[0];
                    const currency = data.stock.currency || '';
                    
                    // Update price cells
                    const priceElement = document.querySelector(`.stock-price[data-ticker="${ticker}"][data-exchange="${exchange}"]`);
                    if (priceElement) {
                        priceElement.textContent = `${price.close_price} ${currency}`;
                    }
                    
                    // Update change cells
                    const changeElement = document.querySelector(`.stock-change[data-ticker="${ticker}"][data-exchange="${exchange}"]`);
                    if (changeElement) {
                        const changePercent = price.change_percent;
                        const changeClass = changePercent > 0 ? 'text-success' : (changePercent < 0 ? 'text-danger' : '');
                        const changeSign = changePercent > 0 ? '+' : '';
                        
                        changeElement.textContent = `${changeSign}${changePercent}%`;
                        changeElement.className = `stock-change ${changeClass}`;
                    }
                }
            })
            .catch(error => {
                console.error(`Error fetching price for ${ticker} (${exchange}):`, error);
                const priceElement = document.querySelector(`.stock-price[data-ticker="${ticker}"][data-exchange="${exchange}"]`);
                if (priceElement) {
                    priceElement.textContent = 'N/A';
                }
                
                const changeElement = document.querySelector(`.stock-change[data-ticker="${ticker}"][data-exchange="${exchange}"]`);
                if (changeElement) {
                    changeElement.textContent = '-';
                }
            });
        });
    }
}

/**
 * Setup search and filter functionality
 */
function setupSearchAndFilters() {
    const searchInput = document.getElementById('searchStocks');
    const sectorFilter = document.getElementById('sectorFilter');
    const sortBy = document.getElementById('sortBy');
    
    if (searchInput) {
        searchInput.addEventListener('input', filterStocks);
    }
    
    if (sectorFilter) {
        sectorFilter.addEventListener('change', filterStocks);
    }
    
    if (sortBy) {
        sortBy.addEventListener('change', sortStocks);
    }
}

/**
 * Filter stocks based on search input and sector filter
 */
function filterStocks() {
    const searchInput = document.getElementById('searchStocks');
    const sectorFilter = document.getElementById('sectorFilter');
    
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    const sectorValue = sectorFilter ? sectorFilter.value.toLowerCase() : '';
    
    const rows = document.querySelectorAll('#stocksTable tbody tr');
    let visibleCount = 0;
    
    rows.forEach(row => {
        const ticker = row.getAttribute('data-ticker').toLowerCase();
        const name = row.cells[1].textContent.toLowerCase();
        const sector = row.getAttribute('data-sector').toLowerCase();
        
        const matchesSearch = ticker.includes(searchTerm) || name.includes(searchTerm);
        const matchesSector = !sectorValue || sector.includes(sectorValue);
        
        if (matchesSearch && matchesSector) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });
    
    // Show/hide no results message
    const noResultsMessage = document.getElementById('noResultsMessage');
    if (noResultsMessage) {
        noResultsMessage.style.display = visibleCount === 0 ? 'block' : 'none';
    }
}

/**
 * Sort stocks based on selected criteria
 */
function sortStocks() {
    const sortBy = document.getElementById('sortBy').value;
    const [field, direction] = sortBy.split('_');
    
    const tbody = document.querySelector('#stocksTable tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        let aValue, bValue;
        
        if (field === 'name') {
            aValue = a.cells[1].textContent;
            bValue = b.cells[1].textContent;
        } else if (field === 'ticker') {
            aValue = a.cells[0].textContent;
            bValue = b.cells[0].textContent;
        } else if (field === 'price') {
            aValue = parseFloat(a.cells[4].textContent) || 0;
            bValue = parseFloat(b.cells[4].textContent) || 0;
        } else if (field === 'change') {
            aValue = parseFloat(a.cells[5].textContent.replace('%', '')) || 0;
            bValue = parseFloat(b.cells[5].textContent.replace('%', '')) || 0;
        }
        
        if (direction === 'asc') {
            return aValue > bValue ? 1 : -1;
        } else {
            return aValue < bValue ? 1 : -1;
        }
    });
    
    // Remove all existing rows
    while (tbody.firstChild) {
        tbody.removeChild(tbody.firstChild);
    }
    
    // Add sorted rows
    rows.forEach(row => {
        tbody.appendChild(row);
    });
}

/**
 * Setup advanced filter functionality
 */
function setupAdvancedFilters() {
    const applyFiltersBtn = document.getElementById('applyFilters');
    const resetFiltersBtn = document.getElementById('resetFilters');
    
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', applyAdvancedFilters);
    }
    
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', resetAdvancedFilters);
    }
}

/**
 * Apply advanced filters from the modal
 */
function applyAdvancedFilters() {
    const exchangeSelect = document.getElementById('exchangeSelect');
    const sectorSelect = document.getElementById('sectorSelect');
    const minPrice = document.getElementById('minPrice');
    const maxPrice = document.getElementById('maxPrice');
    const sortOrder = document.getElementById('sortOrder');
    
    // Update the main filters
    if (exchangeSelect && sectorSelect) {
        const exchangeFilter = document.getElementById('exchangeFilterDropdown');
        const sectorFilter = document.getElementById('sectorFilter');
        const sortBy = document.getElementById('sortBy');
        
        if (exchangeFilter && exchangeSelect.value) {
            // This would ideally update the current exchange, but for this demo
            // we'll just update the text
            exchangeFilter.textContent = exchangeSelect.options[exchangeSelect.selectedIndex].text;
        }
        
        if (sectorFilter && sectorSelect.value) {
            sectorFilter.value = sectorSelect.value;
        }
        
        if (sortBy && sortOrder.value) {
            sortBy.value = sortOrder.value;
        }
    }
    
    // Apply price filter
    if (minPrice || maxPrice) {
        const minVal = minPrice.value ? parseFloat(minPrice.value) : null;
        const maxVal = maxPrice.value ? parseFloat(maxPrice.value) : null;
        
        const rows = document.querySelectorAll('#stocksTable tbody tr');
        
        rows.forEach(row => {
            const priceCell = row.cells[4];
            const priceText = priceCell.textContent;
            const price = parseFloat(priceText.replace(/[^0-9.-]+/g,""));
            
            let hideRow = false;
            
            if (minVal !== null && !isNaN(price) && price < minVal) {
                hideRow = true;
            }
            
            if (maxVal !== null && !isNaN(price) && price > maxVal) {
                hideRow = true;
            }
            
            row.dataset.priceHidden = hideRow ? 'true' : 'false';
            
            // We only hide the row if it's not already hidden by other filters
            if (row.style.display !== 'none' && hideRow) {
                row.style.display = 'none';
            } else if (row.style.display === 'none' && !hideRow) {
                // We don't unhide rows that might be hidden by other filters
                // A complete re-filter would be better
                filterStocks();
            }
        });
    }
    
    // Re-sort if needed
    if (sortOrder && sortOrder.value) {
        sortStocks();
    }
}

/**
 * Reset advanced filters
 */
function resetAdvancedFilters() {
    const form = document.getElementById('advancedFilterForm');
    if (form) {
        form.reset();
    }
    
    // Reset main filters
    const sectorFilter = document.getElementById('sectorFilter');
    if (sectorFilter) {
        sectorFilter.value = '';
    }
    
    const searchInput = document.getElementById('searchStocks');
    if (searchInput) {
        searchInput.value = '';
    }
    
    // Reset display of all rows
    const rows = document.querySelectorAll('#stocksTable tbody tr');
    rows.forEach(row => {
        row.style.display = '';
        row.dataset.priceHidden = 'false';
    });
    
    // Hide no results message
    const noResultsMessage = document.getElementById('noResultsMessage');
    if (noResultsMessage) {
        noResultsMessage.style.display = 'none';
    }
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
