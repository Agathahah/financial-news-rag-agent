import os
import json
from dotenv import load_dotenv

load_dotenv()

def search_news_tool(query: str, n_results: int = 5) -> str:
    """Mencari artikel berita relevan berdasarkan query semantik."""
    try:
        from src.embedding.embedder import NewsEmbedder
        embedder = NewsEmbedder()
        results = embedder.search(query, n_results=n_results)

        if not results:
            return "Tidak ada artikel yang relevan ditemukan."

        output = []
        for r in results:
            output.append(
                f"[{r['source']} | {r['date']} | score: {r['relevance_score']}]\n"
                f"Judul: {r['title']}\n"
                f"URL: {r['url']}"
            )
        return "\n\n".join(output)
    except Exception as e:
        return f"Search error: {e}"


def get_entity_trend_tool(entity: str, days: int = 7) -> str:
    """Mengambil tren frekuensi entitas dari analytics database."""
    try:
        from src.analytics.spark_analytics import get_daily_trends
        trends = get_daily_trends(entity, days)
        total = trends["total"]
        direction = trends["direction"]
        arah = "meningkat" if direction > 0 else "menurun"

        return (
            f"Dalam {days} hari terakhir, '{entity}' disebut {total} kali. "
            f"Tren: {arah}."
        )
    except Exception as e:
        return f"Trend error: {e}"


def summarize_topic_tool(topic: str) -> str:
    """Membuat ringkasan dari artikel-artikel terkait topik."""
    try:
        from src.embedding.embedder import NewsEmbedder
        embedder = NewsEmbedder()
        results = embedder.search(topic, n_results=3)

        if not results:
            return "Tidak ada artikel yang relevan untuk diringkas."

        summaries = []
        for r in results:
            summaries.append(f"- {r['title']} ({r['source']}, {r['date']})")

        return (
            f"Artikel terkait '{topic}':\n" +
            "\n".join(summaries)
        )
    except Exception as e:
        return f"Summary error: {e}"


TOOLS = {
    "search_news": search_news_tool,
    "get_entity_trend": get_entity_trend_tool,
    "summarize_topic": summarize_topic_tool,
}


if __name__ == "__main__":
    print("=== Tools Test ===\n")

    print("1. search_news_tool:")
    result = search_news_tool("kenaikan BI rate", n_results=2)
    print(result)

    print("\n2. get_entity_trend_tool:")
    result = get_entity_trend_tool("IHSG", days=7)
    print(result)

    print("\n3. summarize_topic_tool:")
    result = summarize_topic_tool("inflasi rupiah")
    print(result)
