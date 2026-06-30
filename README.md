# Enterprise RAG Engine

A low-latency, real-time Retrieval-Augmented Generation (RAG) chat engine built with FastAPI and WebSockets. 

Instead of traditional HTTP polling, this system maintains a persistent bidirectional WebSocket tunnel to stream LLM responses instantly. It utilizes FAISS and PyTorch for local semantic vector search to dynamically inject context into the Gemini 2.5 Flash model, strictly preventing hallucination. Session history is managed via an active SQLite/SQLAlchemy ORM layer.

## Architecture & Stack
- **Backend Framework:** FastAPI (Python)
- **Network Protocol:** WebSockets (Full-duplex real-time communication)
- **Vector Database (Memory):** FAISS + `sentence-transformers` (all-MiniLM-L6-v2)
- **LLM:** Google Gemini API (2.5 Flash)
- **Relational Database (Persistence):** SQLite + SQLAlchemy
- **Containerization:** Docker
- **Frontend:** Vanilla HTML/JS (Dark-mode SaaS UI)

## Quick Start (Docker)

The entire application environment is containerized. You do not need to install PyTorch or FAISS locally.

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/enterprise-rag-engine.git](https://github.com/YOUR_USERNAME/enterprise-rag-engine.git)
   cd enterprise-rag-engine
   ```

2. **Add your API Key:**
   Open `main.py` and replace `"YOUR_API_KEY_HERE"` with your actual Google Gemini API key.

3. **Build the image:**
   ```bash
   docker build -t final-rag-engine .
   ```
   *(Note: The initial build takes a few minutes to pull the PyTorch and Python 3.10 slim images).*

4. **Run the container:**
   ```bash
   docker run -p 8000:8000 final-rag-engine
   ```

5. **Access the application:**
   Open your browser and navigate to `http://localhost:8000`.

## Testing the RAG Pipeline
The engine is currently loaded with a sample embedded knowledge base. To test the vector search distance calculations, ask a specific question like:
> *"What is the developer's Codeforces handle and what club are they in?"*