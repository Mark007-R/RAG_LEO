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

let authPromptInFlight = null;

function getApiUrl(endpoint) {
    return `${API_CONFIG.BASE_URL}${endpoint}`;
}

function getStoredApiKey() {
    return localStorage.getItem(APP_CONFIG.STORAGE_KEYS.API_KEY);
}

function clearStoredApiKey() {
    localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.API_KEY);
}

function setStoredApiKey(apiKey) {
    const normalizedKey = (apiKey || '').trim();
    if (normalizedKey) {
        localStorage.setItem(APP_CONFIG.STORAGE_KEYS.API_KEY, normalizedKey);
    } else {
        clearStoredApiKey();
    }
}

function getHeaders(includeContentType = true) {
    const headers = {};

    const apiKey = getStoredApiKey();
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
    const apiKey = getStoredApiKey();
    if (apiKey) {
        headers['Authorization'] = `Bearer ${apiKey}`;
    }
    return headers;
}

async function promptForApiKey() {
    if (authPromptInFlight) {
        return authPromptInFlight;
    }

    authPromptInFlight = Promise.resolve().then(() => {
        const apiKey = window.prompt('This server requires an API access key. Enter it to continue:');
        if (!apiKey || !apiKey.trim()) {
            clearStoredApiKey();
            return false;
        }

        setStoredApiKey(apiKey);
        return true;
    }).finally(() => {
        authPromptInFlight = null;
    });

    return authPromptInFlight;
}

async function apiFetch(endpoint, options = {}) {
    const {
        includeContentType = true,
        allowAuthPrompt = true,
        headers: customHeaders = {},
        ...fetchOptions
    } = options;

    const url = endpoint.startsWith('http') ? endpoint : getApiUrl(endpoint);
    const requestHeaders = {
        ...(includeContentType ? getHeaders() : getHeadersForFormData()),
        ...customHeaders,
    };

    let response = await fetch(url, {
        ...fetchOptions,
        headers: requestHeaders,
    });

    if (response.status === 401 && allowAuthPrompt) {
        clearStoredApiKey();
        const hasReplacementKey = await promptForApiKey();
        if (hasReplacementKey) {
            response = await fetch(url, {
                ...fetchOptions,
                headers: {
                    ...(includeContentType ? getHeaders() : getHeadersForFormData()),
                    ...customHeaders,
                },
            });
        }
    }

    return response;
}
