# Indonesian Financial News RAG Agent

Pipeline AI untuk menjawab pertanyaan analisis keuangan Indonesia
secara real-time, didukung PySpark analytics backend dan semantic
search berbasis vector database.

## Masalah

Analis keuangan Indonesia tidak kekurangan informasi — mereka
kekurangan jawaban. Berita tersebar di puluhan sumber, tidak
terstruktur, dan tidak bisa dijawab dengan search biasa.

Project ini membangun sistem yang bisa menjawab:
- "Bagaimana tren IHSG minggu ini?"
- "Apa dampak kenaikan BI rate terhadap pasar?"
- "Berita terbaru Bank Indonesia hari ini?"

## Arsitektur

    [News Sources]
    RSS + GDELT API
          |
          v
    [Airflow DAG]
    Schedule harian
          |
          v
    [PySpark Ingestion]
    Clean, dedup, normalize
          |
          v
    [PostgreSQL - Star Schema]
    fact_articles + dim_daily_trends
          |
          v
    [PySpark Analytics]
    Window functions + entity tracking
          |
          v
    [Embedding Layer]
    multilingual-e5-base (Hugging Face)
          |
          v
    [ChromaDB]
    Vector store - 200+ docs
          |
          v
    [LangGraph Agent]
    Intent classifier -> Tool routing -> LLM answer
          |
          v
    [FastAPI]
    /ask  /trends  /search  /health

## Stack

| Layer      | Teknologi                          |
|------------|------------------------------------|
| Ingestion  | PySpark 3.5, Airflow               |
| Storage    | PostgreSQL 15, Star Schema         |
| Embedding  | Hugging Face multilingual-e5-base  |
| Vector DB  | ChromaDB                           |
| Agent      | LangChain, LangGraph               |
| LLM        | Groq (llama-3.1-8b-instant)        |
| API        | FastAPI, Pydantic                  |

## Hasil

- 200 artikel diproses dalam 2.5 detik (PySpark)
- Relevance score rata-rata 0.85+ pada semantic search
- Intent classification 100% akurat pada test queries
- API response time <3 detik end-to-end

## Setup

    # 1. Clone dan install
    git clone https://github.com/Agathahah/financial-news-rag-agent.git
    cd financial-news-rag-agent
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt

    # 2. Jalankan PostgreSQL
    docker-compose up -d

    # 3. Isi API keys di .env
    cp .env.example .env

    # 4. Jalankan pipeline
    python -m src.ingestion.spark_pipeline
    python -m src.analytics.spark_analytics
    python -m src.embedding.embedder

    # 5. Jalankan API
    uvicorn src.api.main:app --reload

## API Endpoints

    # Tanya apapun tentang keuangan Indonesia
    curl -X POST http://localhost:8000/ask \
      -H "Content-Type: application/json" \
      -d '{"question": "bagaimana tren IHSG minggu ini?"}'

    # Tren entitas spesifik
    curl http://localhost:8000/trends/IHSG?days=7

    # Semantic search
    curl "http://localhost:8000/search?q=Bank+Indonesia"

    # Health check
    curl http://localhost:8000/health

## Business Impact

Lihat [reports/business_impact.md](reports/business_impact.md) untuk analisis lengkap
keputusan arsitektur dan hasil terukur.
