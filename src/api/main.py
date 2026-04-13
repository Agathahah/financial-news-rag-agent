import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Financial News Intelligence API",
    description="RAG Agent untuk analisis berita keuangan Indonesia",
    version="1.0.0"
)

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    intent: str
    context_length: int

class TrendResponse(BaseModel):
    entity: str
    days: int
    summary: str


@app.get("/health")
async def health():
    from src.embedding.vector_store import get_collection_stats
    stats = get_collection_stats()
    return {
        "status": "ok",
        "model": "multilingual-e5-base",
        "vector_db": "chromadb",
        "total_documents": stats["total_documents"],
    }


@app.post("/ask", response_model=QueryResponse)
async def ask(req: QueryRequest):
    try:
        from src.agent.graph import run_pipeline
        result = run_pipeline(req.question)
        return QueryResponse(
            answer=result["answer"],
            intent=result["intent"],
            context_length=len(result["context"]),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trends/{entity}", response_model=TrendResponse)
async def trends(entity: str, days: int = 7):
    try:
        from src.agent.tools import get_entity_trend_tool
        summary = get_entity_trend_tool(entity, days=days)
        return TrendResponse(entity=entity, days=days, summary=summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search")
async def search(q: str, n: int = 5):
    try:
        from src.agent.tools import search_news_tool
        results = search_news_tool(q, n_results=n)
        return {"query": q, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
