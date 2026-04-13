from langchain.schema import Document
from langchain.prompts import PromptTemplate

RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""Kamu adalah analis keuangan Indonesia.

Konteks dari berita terkini:
{context}

Pertanyaan: {question}

Jawab langsung dengan insight. Berikan opini jika relevan."""
)

def build_rag_context(search_results: list) -> str:
    """Konversi hasil vector search ke context string untuk LLM."""
    docs = []
    for r in search_results:
        docs.append(
            Document(
                page_content=r.get("snippet", r.get("title", "")),
                metadata={
                    "source": r.get("source", ""),
                    "date": r.get("date", ""),
                    "score": r.get("relevance_score", 0),
                }
            )
        )
    return "\n\n".join([
        f"[{d.metadata['source']} | {d.metadata['date']}]\n{d.page_content}"
        for d in docs
    ])

def format_prompt(context: str, question: str) -> str:
    return RAG_PROMPT.format(context=context, question=question)
