import re
from transformers import pipeline as hf_pipeline

INTENT_LABELS = {
    "trend_analysis": [
        "tren", "perkembangan", "bulan ini", "minggu ini",
        "historis", "pergerakan", "naik", "turun", "fluktuasi"
    ],
    "entity_news": [
        "berita", "terbaru", "hari ini", "update", "info",
        "kabar", "laporan", "rilis", "pengumuman"
    ],
    "comparative": [
        "bandingkan", "vs", "versus", "dibanding",
        "lebih baik", "lebih buruk", "perbandingan"
    ],
    "factual_query": [
        "apa", "apa itu", "jelaskan", "definisi",
        "maksud", "artinya", "bagaimana cara"
    ],
}

class IntentClassifier:
    def __init__(self, model_path: str = None):
        self.model_path = model_path
        self.classifier = None

        if model_path:
            try:
                self.classifier = hf_pipeline(
                    "text-classification",
                    model=model_path,
                    tokenizer=model_path,
                )
                print(f"Loaded fine-tuned model from {model_path}")
            except Exception as e:
                print(f"Model load failed: {e}, using rule-based fallback")

    def classify(self, query: str) -> str:
        if self.classifier:
            result = self.classifier(query)[0]
            if result["score"] >= 0.7:
                return result["label"]
            print(f"Low confidence {result['score']:.2f}, falling back to rules")

        return self._rule_based(query)

    def _rule_based(self, query: str) -> str:
        query_lower = query.lower()
        scores = {intent: 0 for intent in INTENT_LABELS}

        for intent, keywords in INTENT_LABELS.items():
            for kw in keywords:
                if kw in query_lower:
                    scores[intent] += 1

        best_intent = max(scores, key=scores.get)

        # Kalau tidak ada keyword yang cocok, default ke factual
        if scores[best_intent] == 0:
            return "factual_query"

        return best_intent

    def classify_with_confidence(self, query: str) -> dict:
        query_lower = query.lower()
        scores = {intent: 0 for intent in INTENT_LABELS}

        for intent, keywords in INTENT_LABELS.items():
            for kw in keywords:
                if kw in query_lower:
                    scores[intent] += 1

        total = sum(scores.values()) or 1
        confidence = {k: round(v / total, 2) for k, v in scores.items()}
        best = max(scores, key=scores.get)

        return {
            "intent": best if scores[best] > 0 else "factual_query",
            "confidence": confidence,
            "method": "rule_based",
        }


if __name__ == "__main__":
    classifier = IntentClassifier()

    test_queries = [
        "bagaimana tren inflasi bulan ini?",
        "berita terbaru IHSG hari ini",
        "apa itu BI rate?",
        "bandingkan rupiah vs dolar minggu ini",
        "perkembangan OJK terhadap fintech",
        "dampak kenaikan suku bunga Bank Indonesia",
    ]

    print("=== Intent Classifier Test ===\n")
    for query in test_queries:
        result = classifier.classify_with_confidence(query)
        intent = result["intent"]
        conf = result["confidence"]
        top_conf = max(conf.values())
        print(f"Query  : {query}")
        print(f"Intent : {intent} (confidence: {top_conf:.0%})")
        print()
