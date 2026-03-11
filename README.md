# RAG_LEO - Production-Grade RAG Document Q&A System

## Overview

RAG_LEO is a **production-ready** Retrieval-Augmented Generation (RAG) system for PDF document Q&A. Built with **Flask**, **FAISS**, **LangChain**, and powered by **Groq's Llama 3 API**, it provides fast, accurate, and scalable document understanding.

### Key Features

- **Application Factory Pattern** - Modular, testable architecture
- **SQLAlchemy ORM** - SQLite by default, configurable via `DATABASE_URL`
- **API Key Authentication** - Bearer token or `X-API-Key` header (optional)
- **Rate Limiting** - 60 requests/min by default, fully configurable
- **CORS Support** - Built-in Flask-CORS configuration
- **Pydantic v2 Validation** - Type-safe request/response schemas
- **FAISS Vector Search** - Cosine similarity with persisted indexes
- **Structured Logging** - Rotating file + console logs, per-request timing
- **Health & Stats Endpoints** - Uptime, document counts, query metrics
- **pytest Test Suite** - Unit and integration tests with coverage reports

---

## Screenshots
![Chat Home Page](images/Chat_Home_Page.png)
![Chat Home Page 2](images/Chat_Home_Page2.png)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   RAG_LEO Flask App                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Routes     │  │   Services   │  │  Middleware  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Models     │  │   Schemas    │  │  Extensions  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└────────────────┬──────────────────────────┬─────────────┘
                 │                          │
     ┌───────────▼────────┐      ┌──────────▼───────┐
     │   SQLite Database  │      │   FAISS Index    │
     │   (SQLAlchemy ORM) │      │   (Vectors +     │
     │   rag_leo.db       │      │    Metadata)     │
     └────────────────────┘      └──────────────────┘
```

## Project Structure

```
RAG_LEO/
├── app.py                      # Application entry point & route definitions
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Tool configuration (black, pytest, mypy)
├── .env                        # Environment variables (not committed)
├── rag_leo.db                  # SQLite database (created at runtime)
│
├── src/                        # Application package
│   ├── __init__.py
│   ├── config.py               # Pydantic settings (reads .env)
│   ├── database.py             # SQLAlchemy session management
│   ├── exceptions.py           # Custom exception hierarchy
│   ├── extensions.py           # Flask extensions init (CORS, etc.)
│   ├── logger_config.py        # Rotating file + console logging
│   ├── middleware.py           # Request validation & sanitization
│   ├── models.py               # SQLAlchemy ORM models
│   ├── rag_pipeline.py         # FAISS + SentenceTransformers + Groq
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── services.py             # Business logic layer
│   └── utils.py                # File helpers, directory utilities
│
├── templates/                  # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── admin.html
│   └── error.html
├── static/
│   ├── css/main.css
│   └── js/
│       ├── app.js
│       └── config.js
│
├── tests/
│   ├── conftest.py
│   ├── test_app.py
│   ├── test_models.py
│   └── test_schemas.py
│
├── uploads/                    # Uploaded PDFs (auto-created)
├── indexes/                    # FAISS index files (auto-created)
├── metadata/                   # Chunk metadata pickles (auto-created)
├── logs/                       # Rotating log files (auto-created)
└── temp/                       # Temporary processing files
```


## Quick Start

### Prerequisites

- Python 3.11+
- Groq API Key ([Get one here](https://console.groq.com/))

### 1. Clone the Repository

```bash
git clone <repository-url>
cd RAG_LEO
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Required
GROQ_API_KEY=your-groq-api-key-here
SECRET_KEY=your-random-secret-key-here

# Optional — API key auth (leave API_KEYS blank to disable)
API_KEY_ENABLED=True
API_KEYS=key1,key2

# Optional overrides
GROQ_MODEL_NAME=llama-3.3-70b-versatile
DATABASE_URL=sqlite:///rag_leo.db
FLASK_DEBUG=False
```

### 5. Run the App

```bash
python app.py
```

Visit: [http://localhost:5000](http://localhost:5000)


## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | ✅ | — | Groq API key |
| `SECRET_KEY` | ✅ | — | Flask secret key |

## Model Details

### Embedding Model
**`sentence-transformers/all-MiniLM-L6-v2`** (default)
- Runs locally on CPU
- Produces 384-dimensional semantic vectors
- Fast and efficient for similarity search
- Configurable via `EMBED_MODEL_NAME`

### Generation Model (via Groq API)
**`llama-3.3-70b-versatile`** (default) — configurable via `GROQ_MODEL_NAME`

| Model | Speed | Quality |
|---|---|---|
| `llama-3.1-8b-instant` | Fastest | Good |
| `llama-3.1-70b-versatile` | Moderate | High |
| `llama-3.3-70b-versatile` | Moderate | Best (recommended) |

### Vector Index
**FAISS `IndexFlatIP`**
- Cosine similarity search (inner product on L2-normalised vectors)
- Top-K retrieval per query (default K=5)
- Index and metadata persisted to `indexes/` and `metadata/` directories


## Configuration

All settings live in `src/config.py` and are read from the `.env` file via Pydantic `BaseSettings`. Key RAG parameters:

| Setting | Default | Description |
|---|---|---|
| `CHUNK_SIZE` | `1000` | Text chunk size in characters |
| `CHUNK_OVERLAP` | `200` | Overlap between consecutive chunks |
| `TOP_K_RETRIEVAL` | `5` | Chunks retrieved per query |
| `LLM_MAX_TOKENS` | `1024` | Max tokens in generated answer |
| `LLM_TEMPERATURE` | `0.3` | Sampling temperature (0.0–2.0) |
| `GROQ_MODEL_NAME` | `llama-3.3-70b-versatile` | Groq model to use |
| `LLM_TIMEOUT` | `30` | Groq API timeout in seconds |
| `LLM_MAX_RETRIES` | `2` | Groq API retry attempts |


## Workflow

1️⃣ **Upload** — User POSTs `annual_report.pdf` to `/api/v1/upload`  
2️⃣ **Extract** — PyPDF2 extracts all text from the PDF pages  
3️⃣ **Chunk** — `RecursiveCharacterTextSplitter` splits text into 1000-char chunks with 200-char overlap  
4️⃣ **Embed** — SentenceTransformers encodes each chunk into a 384-dim vector  
5️⃣ **Index** — FAISS builds a searchable index; index + metadata are saved to disk  
6️⃣ **Store** — Document record saved to SQLite with chunk count, file size, processing time  
7️⃣ **Query** — User POSTs `{"doc_id": "...", "query": "What was the revenue growth?"}` to `/api/v1/ask`  
8️⃣ **Retrieve** — Top-5 most similar chunks fetched via FAISS cosine search  
9️⃣ **Generate** — Groq Llama 3 generates an answer from the retrieved chunks  
🔟 **Respond** — Answer and source chunks returned; query logged to database  

## Performance

- **PDF Processing:** ~1–2 seconds depending on file size
- **Query Response:** ~1–3 seconds (dominated by Groq API latency)
- **Embedding Generation:** ~0.5 seconds per 32 chunks (CPU, SentenceTransformers)
- **Response time header:** Every API response includes `X-Response-Time` (ms)

### Groq API Cost
- **Free Tier:** 14,400 requests/day
- **Paid:** Pay-as-you-go (~$0.05–$0.20 per 1M tokens)
- **Embeddings:** Free — runs locally


## Author
**Mark Rodrigues**

## Contributing
Contributions are welcome! Feel free to open issues and submit pull requests.

## License
This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.