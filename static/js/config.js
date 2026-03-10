// API Configuration
const API_CONFIG = {
    BASE_URL: window.location.origin,
    API_VERSION: 'v1',
    ENDPOINTS: {
        HEALTH: '/api/v1/health',
        STATS: '/api/v1/stats',
        UPLOAD: '/api/v1/upload',
        QUERY: '/api/v1/ask',
        DOCUMENTS: '/api/v1/documents',
        DOCUMENT: '/api/v1/document', // + /{doc_id}
    },
    DEFAULT_HEADERS: {
        'Content-Type': 'application/json',
    }
};

// App configuration
const APP_CONFIG = {
    MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
    ALLOWED_FILE_TYPES: ['.pdf'],
    DEFAULT_TOP_K: 4,
    DEFAULT_TEMPERATURE: 0.7,
    DEFAULT_MAX_TOKENS: 512,
    AUTO_SAVE_KEY: true,
    STORAGE_KEYS: {
        API_KEY: 'rag_leo_api_key',
        CURRENT_DOC: 'rag_leo_current_doc',
        CHAT_HISTORY: 'rag_leo_chat_history',
    }
};

// Helper to get full API URL
function getApiUrl(endpoint) {
    return `${API_CONFIG.BASE_URL}${endpoint}`;
}

// Helper to get headers with API key
function getHeaders(includeContentType = true) {
    const headers = {};
    
    // Add API key if available
    const apiKey = localStorage.getItem(APP_CONFIG.STORAGE_KEYS.API_KEY);
    if (apiKey) {
        headers['Authorization'] = `Bearer ${apiKey}`;
    }
    
    // Add content type if requested
    if (includeContentType) {
        headers['Content-Type'] = 'application/json';
    }
    
    return headers;
}

// Helper for FormData requests (no Content-Type header)
function getHeadersForFormData() {
    const headers = {};
    const apiKey = localStorage.getItem(APP_CONFIG.STORAGE_KEYS.API_KEY);
    if (apiKey) {
        headers['Authorization'] = `Bearer ${apiKey}`;
    }
    return headers;
}
