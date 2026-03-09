# � RAG_LEO - Production-Grade RAG Document Q&A System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-brightgreen.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Overview

RAG_LEO is a **production-ready** Retrieval-Augmented Generation (RAG) system for PDF document Q&A. Built with **Flask**, **FAISS**, **LangChain**, and powered by **Groq's Llama 3 API**, it provides fast, accurate, and scalable document understanding.

### ✨ Key Production Features

- 🏗️ **Application Factory Pattern** - Modular, testable architecture
- 🗄️ **PostgreSQL Support** - Production database with SQLAlchemy ORM
- 🔒 **Enterprise Security** - API key authentication, rate limiting, CORS
- 📊 **Database Migrations** - Alembic for schema versioning
- 🐳 **Docker Ready** - Full containerization with Docker Compose
- 📈 **Comprehensive Monitoring** - Health checks, metrics, logging
- ✅ **Test Coverage** - Unit and integration tests with pytest
- 🚀 **Production Server** - Gunicorn WSGI with nginx reverse proxy
- 📝 **API Validation** - Pydantic schemas for type safety
- 🔄 **Background Tasks** - Optional Celery integration
- 📦 **CI/CD Ready** - Pre-commit hooks, linting, formatting

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Nginx Reverse Proxy                   │
│                  (SSL, Rate Limiting)                    │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                   RAG_LEO Flask App                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Routes     │  │   Services   │  │  Middleware  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Models     │  │   Schemas    │  │  Extensions  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└───────┬──────────────────┬──────────────────┬───────────┘
        │                  │                  │
┌───────▼────────┐ ┌───────▼────────┐ ┌──────▼───────┐
│   PostgreSQL   │ │   Redis Cache  │ │  FAISS Index │
│   (Database)   │ │ (Rate Limiting)│ │  (Vectors)   │
└────────────────┘ └────────────────┘ └──────────────┘
```

---

## 📁 Project Structure

```
RAG_LEO/
├── app.py                      # Application entry point (factory pattern)
├── config.py                   # Configuration management
├── models.py                   # Database models (SQLAlchemy)
├── schemas.py                  # Request/response schemas (Pydantic)
├── services.py                 # Business logic layer
├── database.py                 # Database operations
├── extensions.py               # Flask extensions initialization
├── middleware.py               # Security middleware
├── exceptions.py               # Custom exceptions
├── logger_config.py            # Logging configuration
├── rag_pipeline.py             # RAG pipeline (FAISS + Groq)
├── utils.py                    # Utility functions
│
├── templates/                  # HTML templates
│   └── index.html
├── static/                     # Static assets
│   └── style.css
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_app.py
│   ├── test_models.py
│   └── test_schemas.py
│
├── uploads/                    # Uploaded PDFs (created at runtime)
├── indexes/                    # FAISS indexes (created at runtime)
├── metadata/                   # Chunk metadata (created at runtime)
├── logs/                       # Application logs (created at runtime)
│
├── Dockerfile                  # Production Docker image
├── docker-compose.yml          # Multi-container orchestration
├── nginx.conf                  # Nginx configuration
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── pyproject.toml              # Python project configuration
├── .pre-commit-config.yaml     # Pre-commit hooks
├── Makefile                    # Common tasks automation
├── deploy.sh                   # Deployment script (Linux/Mac)
├── deploy.ps1                  # Deployment script (Windows)
└── README.md                   # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized deployment)
- Groq API Key ([Get it here](https://console.groq.com/))

### 1. Clone Repository

```bash
git clone <repository-url>
cd RAG_LEO
```

### 2. Environment Setup

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
# Required: GROQ_API_KEY, SECRET_KEY, API_KEYS
```

### 3. Choose Your Deployment Method

#### Option A: Docker (Recommended for Production)

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
| Language | Python 3.8+ |

---

## 🚀 Setup Instructions

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/rag-flask-app.git
cd rag-flask-app
```

### 2️⃣ Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Get Groq API Key
1. Sign up at [https://console.groq.com](https://console.groq.com)
2. Generate an API key from your account
3. Copy your API key

### 5️⃣ Configure Environment Variables
Create a `.env` file in the project root:

```env name=.env
# Groq Configuration
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=llama-3.1-8b-instant

# Flask Configuration (optional)
FLASK_DEBUG=False
FLASK_ENV=production
```

**Available Groq Models:**
- `llama-3.1-8b-instant` (Fast, lightweight)
- `llama-3.1-70b-versatile` (More powerful)
- `llama-3.3-70b-versatile` (Latest, recommended)

### 6️⃣ Run the Flask App
```bash
python app.py
```

Visit: 👉 [http://localhost:5000](http://localhost:5000)

---

## 🧪 API Endpoints

| Endpoint | Method | Description |
|-----------|---------|-------------|
| `/` | GET | Renders main page with UI |
| `/upload` | POST | Upload a PDF and create embeddings |
| `/documents` | GET | List all uploaded documents with model info |
| `/ask` | POST | Query a document using RAG + Llama 3 |
| `/document/<doc_id>` | DELETE | Delete a document and its index |
| `/health` | GET | Health check and system status |

---

## 💬 Example Usage

### 1️⃣ Upload a PDF
```bash
curl -X POST -F "file=@report.pdf" http://localhost:5000/upload
```

**Response:**
```json
{
  "message": "Document uploaded and indexed successfully",
  "doc_id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "report.pdf",
  "chunks_count": 45,
  "text_length": 12500,
  "model": "llama-3.1-8b-instant"
}
```

### 2️⃣ Ask a Question
```bash
curl -X POST http://localhost:5000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the key insights from the report?",
    "doc_id": "123e4567-e89b-12d3-a456-426614174000",
    "top_k": 4
  }'
```

**Response:**
```json
{
  "answer": "The report highlights that renewable energy investments have grown by 25% in the last year, with solar energy leading the sector.",
  "retrieved_chunks": [
    "Renewable energy investments increased by 25%...",
    "Solar energy accounted for 60% of growth..."
  ],
  "doc_id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "report.pdf",
  "query": "What are the key insights from the report?",
  "model": "llama-3.1-8b-instant",
  "chunks_retrieved": 2
}
```

### 3️⃣ List All Documents
```bash
curl http://localhost:5000/documents
```

### 4️⃣ Delete a Document
```bash
curl -X DELETE http://localhost:5000/document/123e4567-e89b-12d3-a456-426614174000
```

### 5️⃣ Health Check
```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "documents_count": 3,
  "current_doc_loaded": "123e4567-e89b-12d3-a456-426614174000",
  "pipeline_status": "initialized",
  "model": "llama-3.1-8b-instant",
  "timestamp": "2025-11-11T15:22:32Z"
}
```

---

## 🧠 Model Details

### Embedding Model
**`sentence-transformers/all-MiniLM-L6-v2`**
- Size: ~22MB
- Runs locally (CPU/GPU)
- Converts text chunks into 384-dimensional semantic vectors
- Fast and efficient for similarity search

### Generation Model (via Groq)
**`Llama 3` (Multiple sizes available)**
- **Llama 3.1-8B Instant:** Fast responses, good quality, lower latency
- **Llama 3.1-70B:** Higher quality, more capable, slightly higher latency
- **Llama 3.3-70B:** Latest version, best quality responses

### Vector Index
**`faiss.IndexFlatIP`**
- Enables cosine similarity search (inner product on normalized vectors)
- Retrieves top-K most relevant document chunks per query
- Persisted to disk for reuse

---

## ⚙️ Configuration

Modify these parameters in `rag_pipeline.py` or via API requests:

| Parameter | Description | Default |
|------------|--------------|----------|
| `chunk_size` | Size of text chunks in characters | 1000 |
| `chunk_overlap` | Overlap between consecutive chunks | 200 |
| `top_k` | Number of chunks retrieved per query | 4 |
| `max_tokens` | Maximum tokens in generated answer | 256 |
| `temperature` | Sampling temperature (0-2.0) | 0.7 |
| `groq_model_name` | Groq model to use | `llama-3.1-8b-instant` |

---

## 🧩 Example Workflow

1️⃣ **Upload Document:** User uploads `annual_report.pdf`  
2️⃣ **Text Extraction:** PyPDF2 extracts all text from PDF pages  
3️⃣ **Chunking:** Text is split into overlapping chunks (1000 chars, 200 char overlap)  
4️⃣ **Embedding:** SentenceTransformers converts chunks to embeddings  
5️⃣ **Indexing:** FAISS builds a searchable index, saved to disk  
6️⃣ **Query:** User asks "What was the revenue growth?"  
7️⃣ **Retrieval:** Top-4 most similar chunks are retrieved using FAISS  
8️⃣ **Generation:** Groq/Llama 3 generates an answer using retrieved chunks  
9️⃣ **Response:** Answer is returned to user with source chunks  

---

## 📊 Performance & Costs

### Speed
- **PDF Processing:** ~1-2 seconds (depends on file size)
- **Query Response:** ~1-3 seconds (Groq API latency)
- **Embedding Generation:** ~0.5 seconds per 32 chunks (SentenceTransformers)

### Cost Estimation (Groq API)
- **Free Tier:** 14,400 requests/day (~600/hour)
- **Paid Tier:** Pay-as-you-go (usually $0.05-$0.20 per 1M tokens)
- **Embedding Model:** Free (runs locally)

---

## 🔒 Security Best Practices

1. **Never commit `.env` file** — Add to `.gitignore`:
   ```
   .env
   .env.local
   uploads/*
   indexes/*
   metadata/*
   ```

2. **Protect API Keys** — Keep GROQ_API_KEY private
3. **Validate User Input** — The app validates file types and query formats
4. **Rate Limiting** — Consider adding rate limits for production deployment

---

## 🧪 Testing

### Local Testing
```bash
# Start the application
python app.py

# In another terminal, upload a test PDF
curl -X POST -F "file=@sample.pdf" http://localhost:5000/upload

# Query the document
curl -X POST http://localhost:5000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Test question", "doc_id": "your_doc_id"}'
```

### Unit Tests (Optional)
```bash
pytest tests/
```

---

## 📈 Future Enhancements

- ✅ Multi-document question answering
- ✅ Persistent vector database (Chroma, Milvus, or Pinecone)
- ✅ Web UI improvements (React/Vue frontend)
- ✅ Source citation with page numbers
- ✅ Support for DOCX, TXT, and Markdown files
- ✅ User authentication and document access control
- ✅ Streaming responses for real-time UI updates
- ✅ Batch processing for multiple documents
- ✅ Analytics dashboard for query history

---

## 🐛 Troubleshooting

### Issue: `GROQ_API_KEY not set`
**Solution:** Create `.env` file with your Groq API key
```bash
echo "GROQ_API_KEY=your_key_here" > .env
```

### Issue: `rate_limit_error` from Groq API
**Solution:** Wait a moment and retry. Consider using a paid Groq plan for higher limits.

### Issue: `PDF extraction failed`
**Solution:** Ensure the PDF is not corrupted and contains extractable text.

### Issue: `FAISS index not found`
**Solution:** Re-upload the document. Indexes may have been deleted.

### Issue: Slow embedding generation
**Solution:** Use GPU acceleration. Install CUDA and set `device='cuda'` in pipeline initialization.

---

## 📚 References

- [Groq API Documentation](https://console.groq.com/docs)
- [LangChain Documentation](https://python.langchain.com/)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [SentenceTransformers](https://www.sbert.net/)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

## 🧑‍💻 Author
**Gijode** (Updated: 2025-11-11)

---

## 🤝 Contributing
Contributions are welcome! Feel free to open issues and submit pull requests.

---

## 📜 License
This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---