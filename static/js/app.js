const AppState = {
    currentDocId: null,
    documents: [],
    chatHistory: [],
};

const DOM = {};

document.addEventListener('DOMContentLoaded', () => {
    cacheDOMElements();
    initializeApp();
    attachEventListeners();
});

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
    DOM.questionInput = document.getElementById('question');
    DOM.uploadBtn = document.getElementById('uploadBtn');
    DOM.askBtn = document.getElementById('askBtn');
    DOM.mobileMenuToggle = document.getElementById('mobileMenuToggle');
    DOM.sidebar = document.querySelector('.sidebar');
}

async function initializeApp() {
    await checkHealth();
    await loadDocuments();
    loadChatHistory();
}

function attachEventListeners() {
    DOM.pdfFileInput.addEventListener('change', handleFileSelect);
    DOM.uploadForm.addEventListener('submit', handleUpload);
    DOM.queryForm.addEventListener('submit', handleQuery);
    DOM.clearChatBtn.addEventListener('click', clearChat);
    DOM.docSelect.addEventListener('change', handleDocSelectChange);

    if (DOM.mobileMenuToggle && DOM.sidebar) {
        DOM.mobileMenuToggle.addEventListener('click', () => {
            DOM.sidebar.classList.toggle('open');
        });

        document.addEventListener('click', (event) => {
            const isMobile = window.matchMedia('(max-width: 980px)').matches;
            if (!isMobile || !DOM.sidebar.classList.contains('open')) {
                return;
            }

            const clickedInsideSidebar = DOM.sidebar.contains(event.target);
            const clickedMenuButton = DOM.mobileMenuToggle.contains(event.target);
            if (!clickedInsideSidebar && !clickedMenuButton) {
                DOM.sidebar.classList.remove('open');
            }
        });
    }
}

async function checkHealth() {
    try {
        const response = await apiFetch(API_CONFIG.ENDPOINTS.HEALTH, { allowAuthPrompt: false });
        const data = await response.json();
        
        if (data.status === 'healthy') {
            console.log('Backend is healthy');
            return true;
        }
    } catch (error) {
        console.error('Backend health check failed:', error);
        showStatusMessage('Backend connection failed', 'error');
        return false;
    }
}

async function loadDocuments() {
    try {
        const response = await apiFetch(API_CONFIG.ENDPOINTS.DOCUMENTS);
        
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

function displayDocuments() {
    if (AppState.documents.length === 0) return;
    
    DOM.documentsList.innerHTML = AppState.documents.map(doc => {
        const isActive = doc.doc_id === AppState.currentDocId;
        const uploadDate = doc.created_at ? new Date(doc.created_at).toLocaleDateString() : 'Unknown';
        const fileSize = doc.file_size ? formatFileSize(doc.file_size) : 'Unknown';
        
        return `
            <div class="document-item ${isActive ? 'active' : ''}" onclick="selectDocument('${doc.doc_id}', '${escapeHtml(doc.filename)}')">
                <div class="doc-header">
                    <span class="doc-name"> ${escapeHtml(doc.filename)}</span>
                </div>
                <div class="doc-meta">
                    <span class="doc-id">ID: ${doc.doc_id.substring(0, 12)}...</span>
                    <span class="doc-date"> ${uploadDate}</span>
                    <span class="doc-size"> ${fileSize}</span>
                </div>
                <div class="doc-actions">
                    <button class="btn-small btn-primary" onclick="event.stopPropagation(); selectDocument('${doc.doc_id}', '${escapeHtml(doc.filename)}')">
                        ${isActive ? ' Selected' : 'Select'}
                    </button>
                    <button class="btn-small btn-danger" onclick="event.stopPropagation(); deleteDocument('${doc.doc_id}', '${escapeHtml(doc.filename)}')">
                        Delete
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function updateDocumentSelect() {
    DOM.docSelect.innerHTML = '<option value="">Select document...</option>' +
        AppState.documents.map(doc => {
            const isSelected = doc.doc_id === AppState.currentDocId;
            return `<option value="${doc.doc_id}" ${isSelected ? 'selected' : ''}>
                ${escapeHtml(doc.filename)}
            </option>`;
        }).join('');
}

function selectDocument(docId, filename) {
    AppState.currentDocId = docId;
    DOM.docSelect.value = docId;
    displayDocuments();
    localStorage.setItem(APP_CONFIG.STORAGE_KEYS.CURRENT_DOC, docId);
    showStatusMessage(`Selected: ${filename}`, 'success');

    if (DOM.sidebar && window.matchMedia('(max-width: 980px)').matches) {
        DOM.sidebar.classList.remove('open');
    }
}

async function deleteDocument(docId, filename) {
    if (!confirm(`Delete "${filename}"? This cannot be undone.`)) return;
    
    try {
        const response = await apiFetch(`${API_CONFIG.ENDPOINTS.DOCUMENT}/${docId}`, {
            method: 'DELETE'
        });
        
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

function handleFileSelect(e) {
    const file = e.target.files[0];
    
    if (file) {
        const fileName = file.name.toLowerCase();
        const isValidType = APP_CONFIG.ALLOWED_FILE_TYPES.some(type => fileName.endsWith(type));
        
        if (!isValidType) {
            showStatusMessage('Only PDF files are allowed', 'error');
            e.target.value = '';
            return;
        }
        
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
        const response = await apiFetch(API_CONFIG.ENDPOINTS.UPLOAD, {
            method: 'POST',
            includeContentType: false,
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showStatusMessage(` ${result.filename} uploaded successfully!`, 'success');
            
            DOM.uploadForm.reset();
            DOM.fileNameDisplay.textContent = 'Choose PDF...';
            DOM.fileNameDisplay.parentElement.classList.remove('file-selected');

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
    
    const welcomeMsg = DOM.chat.querySelector('.welcome-message');
    if (welcomeMsg) welcomeMsg.remove();

    addMessage(question, 'user');
    DOM.questionInput.value = '';

    const loadingId = addMessage('Thinking...', 'bot', true);
    setButtonLoading(DOM.askBtn, true);
    
    try {
        const response = await apiFetch(API_CONFIG.ENDPOINTS.QUERY, {
            method: 'POST',
            body: JSON.stringify({
                query: question,
                doc_id: selectedDocId,
                top_k: APP_CONFIG.DEFAULT_TOP_K,
                temperature: APP_CONFIG.DEFAULT_TEMPERATURE,
                max_tokens: APP_CONFIG.DEFAULT_MAX_TOKENS
            })
        });
        
        const result = await response.json();
        
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();
        
        if (response.ok) {
            const timeInSeconds = result.total_time_ms / 1000;
            addMessage(result.answer, 'bot', false, timeInSeconds);
            
            if (result.retrieved_chunks && result.retrieved_chunks.length > 0) {
                addRetrievedChunks(result.retrieved_chunks);
            }
            
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

function addMessage(text, type, isLoading = false, processingTime = null) {
    const msgId = 'msg-' + Date.now();
    const msgDiv = document.createElement('div');
    msgDiv.id = msgId;
    msgDiv.className = `message ${type}-msg`;
    
    const label = type === 'user' ? 'You' : 'RAG_LEO';
    const timestamp = new Date().toLocaleTimeString();
    
    let metaHtml = `<div class="message-meta">${timestamp}`;
    if (processingTime) {
        metaHtml += ` •  ${processingTime.toFixed(2)}s`;
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

function addRetrievedChunks(chunks) {
    const chunksDiv = document.createElement('div');
    chunksDiv.className = 'retrieved-chunks';
    chunksDiv.innerHTML = `
        <details>
            <summary>View ${chunks.length} retrieved context chunks</summary>
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

function clearChat() {
    if (!confirm('Clear all messages?')) return;
    
    DOM.chat.innerHTML = `
        <div class="welcome-message">
            <p class="welcome-kicker">Session Reset</p>
            <p class="welcome-title">Chat cleared</p>
            <p class="welcome-description">Select a document and continue asking questions.</p>
        </div>
    `;
    
    AppState.chatHistory = [];
    localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.CHAT_HISTORY);
}

function handleDocSelectChange(e) {
    AppState.currentDocId = e.target.value;
    displayDocuments();
    if (AppState.currentDocId) {
        localStorage.setItem(APP_CONFIG.STORAGE_KEYS.CURRENT_DOC, AppState.currentDocId);
    }
}

function saveChatMessage(question, answer, docId) {
    const message = {
        timestamp: new Date().toISOString(),
        docId,
        question,
        answer
    };
    
    AppState.chatHistory.push(message);
    
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

function showStatusMessage(message, type = 'info') {
    if (!DOM.uploadStatus) return;
    
    DOM.uploadStatus.textContent = message;
    DOM.uploadStatus.className = `status-message ${type}`;
    DOM.uploadStatus.style.display = 'block';
    
    setTimeout(() => {
        DOM.uploadStatus.style.display = 'none';
    }, 5000);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

window.AppState = AppState;
window.API_CONFIG = API_CONFIG;
