import chromadb

def get_collection(path: str = "./chroma_db", name: str = "financial_news"):
    """Helper untuk akses collection dari modul lain."""
    client = chromadb.PersistentClient(path=path)
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}
    )

def get_collection_stats() -> dict:
    col = get_collection()
    return {
        "total_documents": col.count(),
        "collection_name": col.name,
    }
