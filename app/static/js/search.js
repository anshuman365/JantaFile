// app/static/js/search.js

// Function to append debug messages to the HTML log div
function logToPage(message) {
    const debugLogElement = document.getElementById('debug-log');
    if (debugLogElement) {
        const p = document.createElement('p');
        p.textContent = `[DEBUG] ${new Date().toLocaleTimeString()}: ${message}`;
        p.style.color = '#fff';
        p.style.fontSize = '12px';
        p.style.margin = '2px 0';
        debugLogElement.appendChild(p);
        debugLogElement.scrollTop = debugLogElement.scrollHeight; // Scroll to bottom
    }
}

logToPage("search.js file loaded and executing."); // This should be the very first log

// All episodes data will be stored here after fetching from backend
let allEpisodes = [];
let isDataLoaded = false;
let lastQuery = '';
let isSearching = false;
let debounceTimeout; // For debouncing input

// Get DOM elements
const searchInput = document.getElementById('search-input');
const resultsContainer = document.getElementById('results-container');
const noResultsContainer = document.getElementById('no-results');
const errorContainer = document.getElementById('error-message');
const loadingIndicator = document.getElementById('loading-indicator');
const initialPrompt = document.getElementById('initial-prompt');
const searchButton = document.getElementById('search-button');

// --- Helper Functions for UI State ---
function showLoading(forInitialLoad = false) {
    isSearching = true;
    loadingIndicator.style.display = 'block';
    if (!forInitialLoad) {
        initialPrompt.style.display = 'none';
    }
    noResultsContainer.classList.add('hidden');
    errorContainer.classList.add('hidden');
    resultsContainer.innerHTML = ''; // Clear results while loading
}

function hideLoading() {
    isSearching = false;
    loadingIndicator.style.display = 'none';
}

function showInitialState() {
    resultsContainer.innerHTML = '';
    initialPrompt.style.display = 'block';
    noResultsContainer.classList.add('hidden');
    errorContainer.classList.add('hidden');
}

function showResultsContainer() {
    resultsContainer.classList.remove('hidden');
    resultsContainer.style.display = 'grid';
    initialPrompt.style.display = 'none';
    noResultsContainer.classList.add('hidden');
    errorContainer.classList.add('hidden');
}

function showNoResults() {
    resultsContainer.innerHTML = '';
    initialPrompt.style.display = 'none';
    noResultsContainer.classList.remove('hidden');
    errorContainer.classList.add('hidden');
}

function showError() {
    resultsContainer.innerHTML = '';
    initialPrompt.style.display = 'none';
    noResultsContainer.classList.add('hidden');
    errorContainer.classList.remove('hidden');
}

function createResultCard(result) {
    const card = document.createElement('article');
    card.className = 'bg-gray-800 p-6 rounded-lg shadow-md mb-6 border border-gray-700 hover:border-blue-500 transition-all duration-300 ease-in-out transform hover:-translate-y-1';

    card.innerHTML = `
        <div class="flex items-start space-x-4">
            <div class="flex-shrink-0">
                <div class="h-12 w-12 bg-blue-900 rounded-full flex items-center justify-center">
                    <i class="fas fa-file-alt text-blue-400 text-xl"></i>
                </div>
            </div>
            <div class="flex-1">
                <h3 class="text-xl font-semibold text-white mb-2">
                    <a href="/episodes/${result.id}" class="hover:text-blue-400 transition-colors duration-200">
                        ${result.title}
                    </a>
                </h3>
                <p class="text-gray-300 text-sm mb-4">${result.description}</p>
                <div class="flex items-center space-x-4">
                    <a href="/episodes/${result.id}"
                       class="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md shadow-sm transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-800">
                        View Case Files
                        <i class="fas fa-chevron-right ml-2"></i>
                    </a>
                </div>
            </div>
        </div>
    `;
    return card;
}

function displayResults(results) {
    logToPage(`displayResults called with ${results.length} results.`);
    resultsContainer.innerHTML = '';

    if (results.length > 0) {
        results.forEach(result => {
            resultsContainer.appendChild(createResultCard(result));
        });
        showResultsContainer();
    } else {
        showNoResults();
    }
}

// --- Main Search Logic ---
async function fetchAllEpisodes() {
    logToPage("Fetching all episodes from backend...");
    showLoading(true); // Show loading for initial data fetch
    try {
        const response = await fetch('/api/search'); // Endpoint to get all episodes
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        allEpisodes = await response.json();
        isDataLoaded = true;
        logToPage(`Successfully loaded ${allEpisodes.length} episodes.`);
        showInitialState(); // Show initial prompt after data is loaded

        // If there's an initial query from URL, perform search after data loads
        const urlParams = new URLSearchParams(window.location.search);
        const initialQuery = urlParams.get('q');
        if (initialQuery) {
            if (searchInput) {
                searchInput.value = initialQuery;
            }
            handleSearch(initialQuery); // Trigger search
        }

    } catch (error) {
        logToPage(`Error loading all episodes: ${error.message}`);
        showError(); // Show error if initial load fails
    } finally {
        hideLoading();
    }
}

function handleSearch(query) {
    logToPage(`handleSearch called with query: '${query}'`);
    const trimmedQuery = query.trim().toLowerCase();

    if (!isDataLoaded) {
        logToPage("Data not yet loaded, deferring search.");
        showLoading(true); // Keep loading indicator if data isn't ready
        return;
    }

    if (trimmedQuery === lastQuery && !isSearching && trimmedQuery !== '') {
        logToPage("Skipping search: query unchanged or already searching.");
        return;
    }

    lastQuery = trimmedQuery;
    isSearching = true;

    showLoading(); // Show loading indicator for filtering

    let filteredResults = [];
    if (trimmedQuery) {
        filteredResults = allEpisodes.filter(episode =>
            episode.title.toLowerCase().includes(trimmedQuery) ||
            episode.description.toLowerCase().includes(trimmedQuery)
        );
    } else {
        // If query is empty, show initial state (no results)
        showInitialState();
        hideLoading();
        isSearching = false;
        return;
    }

    logToPage(`Client-side filtered ${filteredResults.length} results.`);
    displayResults(filteredResults);
    hideLoading();
    isSearching = false;
}

function clearSearch() {
    if (searchInput) {
        searchInput.value = '';
    }
    handleSearch('');
}

// --- Event Listeners ---
// Ensure DOM elements are available before adding listeners
document.addEventListener('DOMContentLoaded', () => {
    logToPage("DOMContentLoaded fired in search.js.");

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            logToPage(`Input event detected: '${e.target.value}'`);
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(() => handleSearch(e.target.value), 300);
        });

        searchInput.addEventListener('keyup', (e) => {
            if (e.key === 'Escape') {
                logToPage("Escape key pressed.");
                clearSearch();
            } else if (e.key === 'Enter') {
                logToPage("Enter key pressed (manual search).");
                clearTimeout(debounceTimeout);
                handleSearch(searchInput.value);
            }
        });
    } else {
        logToPage("Error: searchInput element not found on DOMContentLoaded.");
    }

    if (searchButton) {
        searchButton.addEventListener('click', () => {
            logToPage("Search button clicked (manual search).");
            clearTimeout(debounceTimeout);
            handleSearch(searchInput.value);
        });
    } else {
        logToPage("Error: searchButton element not found on DOMContentLoaded.");
    }

    // Initial load of all episodes
    fetchAllEpisodes();
});

