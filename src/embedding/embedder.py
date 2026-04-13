import os
import json
from sentence_transformers import SentenceTransformer
import chromadb
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "intfloat/multilingual-e5-base"

class NewsEmbedder:
    def __init__(self):
        print(f"Loading model: {MODEL_NAME}")
        self.model = SentenceTransformer(MODEL_NAME)
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(
            name="financial_news",
            metadata={"hnsw:space": "cosine"}
        )
        print(f"ChromaDB collection: {self.collection.count()} docs existing")

    def embed_articles(self, articles: list) -> int:
        # Filter artikel yang sudah ada di collection
        existing_ids = set()
        if self.collection.count() > 0:
            existing = self.collection.get()
            existing_ids = set(existing["ids"])

        new_articles = [
            a for a in articles
            if a["url"] not in existing_ids
        ]

        if not new_articles:
            print("No new articles to embed")
            return 0

        # e5 butuh prefix "passage:" untuk dokumen
        texts = [
            f"passage: {a['title']}. {a.get('summary', '')}"
            for a in new_articles
        ]

        print(f"Embedding {len(new_articles)} articles...")
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            normalize_embeddings=True
        )

        self.collection.add(
            ids=[a["url"] for a in new_articles],
            embeddings=embeddings.tolist(),
            documents=texts,
            metadatas=[
                {
                    "source": a.get("source", ""),
                    "published_date": str(a.get("published_at", ""))[:10],
                    "title": a.get("title", ""),
                    "url": a.get("url", ""),
                }
                for a in new_articles
            ]
        )

        print(f"Embedded {len(new_articles)} articles")
        print(f"Total in ChromaDB: {self.collection.count()}")
        return len(new_articles)

    def search(self, query: str, n_results: int = 5, date_filter: str = None) -> list:
        # e5 butuh prefix "query:" untuk pertanyaan
        query_embedding = self.model.encode(
            f"query: {query}",
            normalize_embeddings=True
        )

        where_clause = None
        if date_filter:
            where_clause = {"published_date": {"$gte": date_filter}}

        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=min(n_results, self.collection.count()),
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )

        # Format hasil yang bersih
        output = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(docs, metas, distances):
            output.append({
                "title": meta.get("title", ""),
                "source": meta.get("source", ""),
                "date": meta.get("published_date", ""),
                "url": meta.get("url", ""),
                "relevance_score": round(1 - dist, 3),
                "snippet": doc[:200],
            })

        return output

if __name__ == "__main__":
    embedder = NewsEmbedder()

    # Load sample articles
    with open("data/sample/articles.json") as f:
        articles = json.load(f)

    # Embed semua artikel
    count = embedder.embed_articles(articles)
    print(f"\nEmbedded {count} new articles")

    # Test search
    print("\n=== Test Search ===")
    queries = [
        "dampak kenaikan suku bunga Bank Indonesia",
        "perkembangan IHSG minggu ini",
        "nilai tukar rupiah terhadap dolar",
    ]
    for q in queries:
        results = embedder.search(q, n_results=2)
        print(f"\nQuery: '{q}'")
        for r in results:
            print(f"  [{r['relevance_score']}] {r['title']} ({r['source']})")
