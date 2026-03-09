// RAG_LEO - Main Application Logic

// Global state
const AppState = {
    currentDocId: null,
    documents: [],
    chatHistory: [],
    apiKeyValid: false,
    isLoading: false,
};

// DOM elements cache
const DOM = {};

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    cacheDOMElements();
    initializeApp();
    attachEventListeners();
});

// Cache DOM elements
function cacheDOMElements() {
    DOM.uploadForm = document.getElementById('uploadForm');
    DOM.queryForm = document.getElementById('queryForm');
    DOM.chat = document.getElementById('chat');
    DOM.uploadStatus = document.getElementById('uploadStatus');
    DOM.documentsList = document.getElementById('documentsList');
    DOM.docSelect = document.getElementById('docSelect');
    DOM.pdfFileInput = document.getElementById('pdfFile');
    DOM.fileNameDisplay = document.getElementById('fileName');
    DOM.clearChatBtn = document.getElementById('clearChat');
    DOM.apiKeyInput = document.getElementById('apiKeyInput');
    DOM.apiKeyStatus = document.getElementById('apiKeyStatus');
    DOM.questionInput = document.getElementById('question');
    DOM.uploadBtn = document.getElementById('uploadBtn');
    DOM.askBtn = document.getElementById('askBtn');
}

// Initialize application
async function initializeApp() {
    // Load API key from localStorage
    loadApiKey();
    
    // Check backend health
    await checkHealth();
    
    // Load documents
    await loadDocuments();
    
    // Load chat history from localStorage
    loadChatHistory();
}

// Attach event listeners
function attachEventListeners() {
    // File input change
    DOM.pdfFileInput.addEventListener('change', handleFileSelect);
    
    // Upload form submit
    DOM.uploadForm.addEventListener('submit', handleUpload);
    
    // Query form submit
    DOM.queryForm.addEventListener('submit', handleQuery);
    
    // Clear chat
    DOM.clearChatBtn.addEventListener('click', clearChat);
    
    // Document select change
    DOM.docSelect.addEventListener('change', handleDocSelectChange);
    
    // API key input
    if (DOM.apiKeyInput) {
        DOM.apiKeyInput.addEventListener('input', handleApiKeyInput);
        DOM.apiKeyInput.addEventListener('blur', saveApiKey);
    }
}

// Load API key from localStorage
function loadApiKey() {
    const savedKey = localStorage.getItem(APP_CONFIG.STORAGE_KEYS.API_KEY);
    if (savedKey && DOM.apiKeyInput) {
        DOM.apiKeyInput.value = savedKey;
        updateApiKeyStatus(true);
    }
}

// Handle API key input
function handleApiKeyInput(e) {
    const key = e.target.value.trim();
    updateApiKeyStatus(key.length > 0);
}

// Save API key to localStorage
function saveApiKey() {
    const key = DOM.apiKeyInput.value.trim();
    if (key) {
        localStorage.setItem(APP_CONFIG.STORAGE_KEYS.API_KEY, key);
        AppState.apiKeyValid = true;
    } else {
        localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.API_KEY);
        AppState.apiKeyValid = false;
    }
}

// Update API key status display
function updateApiKeyStatus(isValid) {
    if (!DOM.apiKeyStatus) return;
    
    AppState.apiKeyValid = isValid;
    
    if (isValid) {
        DOM.apiKeyStatus.className = 'api-key-status valid';
        DOM.apiKeyStatus.textContent = '✓ API Key Set';
    } else {
        DOM.apiKeyStatus.className = 'api-key-status invalid';
        DOM.apiKeyStatus.textContent = '⚠ No API Key';
    }
}

// Check backend health
async function checkHealth() {
    try {
        const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.HEALTH));
        const data = await response.json();
        
        if (data.status === 'healthy') {
            console.log('✓ Backend is healthy');
            return true;
        }
    } catch (error) {
        console.error('✗ Backend health check failed:', error);
        showStatusMessage('Backend connection failed', 'error');
        return false;
    }
}

// Load documents from server
async function loadDocuments() {
    try {
        const response = await fetch(
            getApiUrl(API_CONFIG.ENDPOINTS.DOCUMENTS),
            { headers: getHeaders() }
        );
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const result = await response.json();
        AppState.documents = result.documents || [];
        
        displayDocuments();
        updateDocumentSelect();
        
        if (AppState.documents.length === 0) {
            DOM.documentsList.innerHTML = '<p style="color: var(--text-secondary); font-size: 13px;">No documents yet</p>';
        }
    } catch (error) {
        console.error('Error loading documents:', error);
        DOM.documentsList.innerHTML = '<p style="color: var(--error-color); font-size: 13px;">Failed to load documents</p>';
    }
}

// Display documents list in sidebar
function displayDocuments() {
    if (AppState.documents.length === 0) return;
    
    DOM.documentsList.innerHTML = AppState.documents.map(doc => {
        const isActive = doc.id === AppState.currentDocId;
        const uploadDate = doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : 'Unknown';
        const fileSize = doc.file_size ? formatFileSize(doc.file_size) : 'Unknown';
        
        return `
            <div class="document-item ${isActive ? 'active' : ''}" onclick="selectDocument('${doc.id}', '${escapeHtml(doc.filename)}')">
                <div class="doc-header">
                    <span class="doc-name">📄 ${escapeHtml(doc.filename)}</span>
                </div>
                <div class="doc-meta">
                    <span class="doc-id">ID: ${doc.id.substring(0, 12)}...</span>
                    <span class="doc-date">📅 ${uploadDate}</span>
                    <span class="doc-size">📦 ${fileSize}</span>
                </div>
                <div class="doc-actions">
                    <button class="btn-small btn-primary" onclick="event.stopPropagation(); selectDocument('${doc.id}', '${escapeHtml(doc.filename)}')">
                        ${isActive ? '✓ Selected' : 'Select'}
                    </button>
                    <button class="btn-small btn-danger" onclick="event.stopPropagation(); deleteDocument('${doc.id}', '${escapeHtml(doc.filename)}')">
                        🗑️
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Update document select dropdown
function updateDocumentSelect() {
    DOM.docSelect.innerHTML = '<option value="">Select document...</option>' +
        AppState.documents.map(doc => {
            const isSelected = doc.id === AppState.currentDocId;
            return `<option value="${doc.id}" ${isSelected ? 'selected' : ''}>
                ${escapeHtml(doc.filename)}
            </option>`;
        }).join('');
}

// Select document
function selectDocument(docId, filename) {
    AppState.currentDocId = docId;
    DOM.docSelect.value = docId;
    displayDocuments();
    localStorage.setItem(APP_CONFIG.STORAGE_KEYS.CURRENT_DOC, docId);
    showStatusMessage(`Selected: ${filename}`, 'success');
}

// Delete document
async function deleteDocument(docId, filename) {
    if (!confirm(`Delete "${filename}"? This cannot be undone.`)) return;
    
    try {
        const response = await fetch(
            `${getApiUrl(API_CONFIG.ENDPOINTS.DOCUMENT)}/${docId}`,
            {
                method: 'DELETE',
                headers: getHeaders()
            }
        );
        
        const result = await response.json();
        
        if (response.ok) {
            showStatusMessage(`Deleted: ${filename}`, 'success');
            if (AppState.currentDocId === docId) {
                AppState.currentDocId = null;
                localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.CURRENT_DOC);
            }
            await loadDocuments();
        } else {
            showStatusMessage(result.error || 'Delete failed', 'error');
        }
    } catch (error) {
        console.error('Error deleting document:', error);
        showStatusMessage('Delete failed', 'error');
    }
}

// Handle file select
function handleFileSelect(e) {
    const file = e.target.files[0];
    
    if (file) {
        // Validate file type
        const fileName = file.name.toLowerCase();
        const isValidType = APP_CONFIG.ALLOWED_FILE_TYPES.some(type => fileName.endsWith(type));
        
        if (!isValidType) {
            showStatusMessage('Only PDF files are allowed', 'error');
            e.target.value = '';
            return;
        }
        
        // Validate file size
        if (file.size > APP_CONFIG.MAX_FILE_SIZE) {
            showStatusMessage(`File too large (max ${formatFileSize(APP_CONFIG.MAX_FILE_SIZE)})`, 'error');
            e.target.value = '';
            return;
        }
        
        DOM.fileNameDisplay.textContent = file.name;
        DOM.fileNameDisplay.parentElement.classList.add('file-selected');
    } else {
        DOM.fileNameDisplay.textContent = 'Choose PDF...';
        DOM.fileNameDisplay.parentElement.classList.remove('file-selected');
    }
}

// Handle upload
async function handleUpload(e) {
    e.preventDefault();
    
    const file = DOM.pdfFileInput.files[0];
    if (!file) {
        showStatusMessage('Please select a file', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    setButtonLoading(DOM.uploadBtn, true);
    showStatusMessage('Processing PDF...', 'info');
    
    try {
        const response = await fetch(
            getApiUrl(API_CONFIG.ENDPOINTS.UPLOAD),
            {
                method: 'POST',
                headers: getHeadersForFormData(),
                body: formData
            }
        );
        
        const result = await response.json();
        
        if (response.ok) {
            showStatusMessage(`✓ ${result.filename} uploaded successfully!`, 'success');
            
            // Reset form
            DOM.uploadForm.reset();
            DOM.fileNameDisplay.textContent = 'Choose PDF...';
            DOM.fileNameDisplay.parentElement.classList.remove('file-selected');
            
            // Reload documents and select the new one
            await loadDocuments();
            selectDocument(result.doc_id, result.filename);
        } else {
            showStatusMessage(result.error || result.detail || 'Upload failed', 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showStatusMessage('Upload failed: ' + error.message, 'error');
    } finally {
        setButtonLoading(DOM.uploadBtn, false);
    }
}

// Handle query
async function handleQuery(e) {
    e.preventDefault();
    
    const question = DOM.questionInput.value.trim();
    const selectedDocId = DOM.docSelect.value;
    
    if (!question) {
        showStatusMessage('Please enter a question', 'error');
        return;
    }
    
    if (!selectedDocId) {
        showStatusMessage('Please select a document', 'error');
        return;
    }
    
    // Remove welcome message if present
    const welcomeMsg = DOM.chat.querySelector('.welcome-message');
    if (welcomeMsg) welcomeMsg.remove();
    
    // Add user message
    addMessage(question, 'user');
    DOM.questionInput.value = '';
    
    // Add loading message
    const loadingId = addMessage('Thinking...', 'bot', true);
    setButtonLoading(DOM.askBtn, true);
    
    try {
        const response = await fetch(
            getApiUrl(API_CONFIG.ENDPOINTS.QUERY),
            {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify({
                    query: question,
                    doc_id: selectedDocId,
                    top_k: APP_CONFIG.DEFAULT_TOP_K,
                    temperature: APP_CONFIG.DEFAULT_TEMPERATURE,
                    max_tokens: APP_CONFIG.DEFAULT_MAX_TOKENS
                })
            }
        );
        
        const result = await response.json();
        
        // Remove loading message
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();
        
        if (response.ok) {
            addMessage(result.answer, 'bot', false, result.processing_time);
            
            if (result.retrieved_chunks && result.retrieved_chunks.length > 0) {
                addRetrievedChunks(result.retrieved_chunks);
            }
            
            // Save to history
            saveChatMessage(question, result.answer, selectedDocId);
        } else {
            addMessage(`Error: ${result.error || result.detail || 'Query failed'}`, 'bot');
        }
    } catch (error) {
        console.error('Query error:', error);
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();
        addMessage('Failed to get answer: ' + error.message, 'bot');
    } finally {
        setButtonLoading(DOM.askBtn, false);
    }
}

// Add message to chat
function addMessage(text, type, isLoading = false, processingTime = null) {
    const msgId = 'msg-' + Date.now();
    const msgDiv = document.createElement('div');
    msgDiv.id = msgId;
    msgDiv.className = `message ${type}-msg`;
    
    const label = type === 'user' ? 'You' : '🦁 RAG_LEO';
    const timestamp = new Date().toLocaleTimeString();
    
    let metaHtml = `<div class="message-meta">⏰ ${timestamp}`;
    if (processingTime) {
        metaHtml += ` • ⚡ ${processingTime.toFixed(2)}s`;
    }
    metaHtml += '</div>';
    
    msgDiv.innerHTML = `
        <strong>${label}:</strong>
        <div>${escapeHtml(text)}</div>
        ${type === 'bot' && !isLoading ? metaHtml : ''}
    `;
    
    DOM.chat.appendChild(msgDiv);
    DOM.chat.scrollTop = DOM.chat.scrollHeight;
    
    return msgId;
}

// Add retrieved chunks
function addRetrievedChunks(chunks) {
    const chunksDiv = document.createElement('div');
    chunksDiv.className = 'retrieved-chunks';
    chunksDiv.innerHTML = `
        <details>
            <summary>📚 View ${chunks.length} retrieved context chunks</summary>
            ${chunks.map((chunk, i) => `
                <div class="chunk-item">
                    <strong>Chunk ${i + 1} (Relevance Score)</strong>
                    <p>${escapeHtml(chunk)}</p>
                </div>
            `).join('')}
        </details>
    `;
    DOM.chat.appendChild(chunksDiv);
    DOM.chat.scrollTop = DOM.chat.scrollHeight;
}

// Clear chat
function clearChat() {
    if (!confirm('Clear all messages?')) return;
    
    DOM.chat.innerHTML = `
        <div class="welcome-message">
            <p>👋 Chat cleared!</p>
            <p>Select a document and start asking questions.</p>
        </div>
    `;
    
    AppState.chatHistory = [];
    localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.CHAT_HISTORY);
}

// Handle document select change
function handleDocSelectChange(e) {
    AppState.currentDocId = e.target.value;
    displayDocuments();
    if (AppState.currentDocId) {
        localStorage.setItem(APP_CONFIG.STORAGE_KEYS.CURRENT_DOC, AppState.currentDocId);
    }
}

// Save chat message to history
function saveChatMessage(question, answer, docId) {
    const message = {
        timestamp: new Date().toISOString(),
        docId,
        question,
        answer
    };
    
    AppState.chatHistory.push(message);
    
    // Keep only last 50 messages
    if (AppState.chatHistory.length > 50) {
        AppState.chatHistory = AppState.chatHistory.slice(-50);
    }
    
    try {
        localStorage.setItem(
            APP_CONFIG.STORAGE_KEYS.CHAT_HISTORY,
            JSON.stringify(AppState.chatHistory)
        );
    } catch (e) {
        console.warn('Failed to save chat history:', e);
    }
}

// Load chat history from localStorage
function loadChatHistory() {
    try {
        const saved = localStorage.getItem(APP_CONFIG.STORAGE_KEYS.CHAT_HISTORY);
        if (saved) {
            AppState.chatHistory = JSON.parse(saved);
        }
    } catch (e) {
        console.warn('Failed to load chat history:', e);
        AppState.chatHistory = [];
    }
}

// Set button loading state
function setButtonLoading(button, isLoading) {
    if (!button) return;
    
    const btnText = button.querySelector('.btn-text');
    const btnLoading = button.querySelector('.btn-loading');
    
    button.disabled = isLoading;
    
    if (btnText) {
        btnText.style.display = isLoading ? 'none' : 'inline';
    }
    
    if (btnLoading) {
        btnLoading.style.display = isLoading ? 'inline' : 'none';
    }
}

// Show status message
function showStatusMessage(message, type = 'info') {
    if (!DOM.uploadStatus) return;
    
    DOM.uploadStatus.textContent = message;
    DOM.uploadStatus.className = `status-message ${type}`;
    DOM.uploadStatus.style.display = 'block';
    
    setTimeout(() => {
        DOM.uploadStatus.style.display = 'none';
    }, 5000);
}

// Utility: Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Utility: Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Export for debugging
window.AppState = AppState;
window.API_CONFIG = API_CONFIG;
