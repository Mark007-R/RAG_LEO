const API_CONFIG = {
    BASE_URL: window.location.origin,
    ENDPOINTS: {
        HEALTH: '/api/v1/health',
        STATS: '/api/v1/stats',
        UPLOAD: '/api/v1/upload',
        QUERY: '/api/v1/ask',
        DOCUMENTS: '/api/v1/documents',
        DOCUMENT: '/api/v1/document',
    }
};

const APP_CONFIG = {
    MAX_FILE_SIZE: 10 * 1024 * 1024,
    ALLOWED_FILE_TYPES: ['.pdf'],
    DEFAULT_TOP_K: 5,
    DEFAULT_TEMPERATURE: 0.3,
    DEFAULT_MAX_TOKENS: 1024,
    STORAGE_KEYS: {
        API_KEY: 'rag_leo_api_key',
        CURRENT_DOC: 'rag_leo_current_doc',
        CHAT_HISTORY: 'rag_leo_chat_history',
    }
};

function getApiUrl(endpoint) {
    return `${API_CONFIG.BASE_URL}${endpoint}`;
}

function getHeaders(includeContentType = true) {
    const headers = {};

    const apiKey = localStorage.getItem(APP_CONFIG.STORAGE_KEYS.API_KEY);
    if (apiKey) {
        headers['Authorization'] = `Bearer ${apiKey}`;
    }

    if (includeContentType) {
        headers['Content-Type'] = 'application/json';
    }

    return headers;
}

function getHeadersForFormData() {
    const headers = {};
    const apiKey = localStorage.getItem(APP_CONFIG.STORAGE_KEYS.API_KEY);
    if (apiKey) {
        headers['Authorization'] = `Bearer ${apiKey}`;
    }
    return headers;
}
