import feedparser
import requests
import json
from datetime import datetime, timedelta

RSS_FEEDS = {
    "kontan": "https://rss.kontan.co.id/category/finansial",
    "bisnis": "https://ekonomi.bisnis.com/feed/rss/finansial",
    "detikfinance": "https://finance.detik.com/rss",
}

def fetch_gdelt_articles(keyword: str = "Bank Indonesia", days_back: int = 7) -> list:
    since = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d%H%M%S")
    url = (
        f"https://api.gdeltproject.org/api/v2/doc/doc?"
        f"query={keyword}+sourcelang:Indonesian"
        f"&mode=artlist&maxrecords=250&startdatetime={since}"
        f"&format=json"
    )
    try:
        resp = requests.get(url, timeout=30)
        articles = resp.json().get("articles", [])
        return [
            {
                "source": a.get("domain", "gdelt"),
                "title": a.get("title", ""),
                "url": a.get("url", ""),
                "published_at": a.get("seendate", ""),
                "summary": "",
                "language": "id",
            }
            for a in articles if a.get("title")
        ]
    except Exception as e:
        print(f"GDELT fetch failed: {e}, using sample data instead")
        return []

def fetch_rss_articles() -> list:
    results = []
    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:50]:
                results.append({
                    "source": source,
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "published_at": entry.get("published", ""),
                    "summary": entry.get("summary", ""),
                    "language": "id",
                })
        except Exception as e:
            print(f"RSS fetch failed for {source}: {e}")
    return results

def load_sample_articles(path: str = "data/sample/articles.json") -> list:
    """Fallback ke sample data untuk development offline."""
    with open(path, "r") as f:
        return json.load(f)

if __name__ == "__main__":
    articles = fetch_rss_articles()
    if not articles:
        print("RSS tidak tersedia, load sample data")
        articles = load_sample_articles()
    print(f"Fetched {len(articles)} articles")
