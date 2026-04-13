import json
from datetime import datetime, timedelta
import random

sources = ["kontan", "bisnis", "detikfinance", "cnbcindonesia"]
entities = ["Bank Indonesia", "BI rate", "IHSG", "rupiah", "inflasi", "OJK"]
templates = [
    "{entity} mengalami perubahan signifikan minggu ini",
    "Analis: dampak {entity} terhadap pasar modal",
    "Update terbaru {entity} — apa artinya bagi investor?",
    "Perkembangan {entity} dan implikasinya ke ekonomi",
]

articles = []
for i in range(200):
    entity = random.choice(entities)
    template = random.choice(templates)
    days_ago = random.randint(0, 30)
    pub_date = datetime.now() - timedelta(days=days_ago)
    articles.append({
        "source": random.choice(sources),
        "title": template.format(entity=entity),
        "url": f"https://example.com/article-{i:04d}",
        "summary": f"Artikel tentang {entity} yang diterbitkan pada {pub_date.strftime('%Y-%m-%d')}.",
        "published_at": pub_date.isoformat(),
        "language": "id",
    })

with open("data/sample/articles.json", "w") as f:
    json.dump(articles, f, indent=2, ensure_ascii=False)

print(f"Created {len(articles)} sample articles")
