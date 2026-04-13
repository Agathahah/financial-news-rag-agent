import os
from typing import TypedDict
from dotenv import load_dotenv

load_dotenv()

class AgentState(TypedDict):
    query: str
    intent: str
    context: str
    answer: str


def classify_node(state: AgentState) -> AgentState:
    from src.agent.intent_classifier import IntentClassifier
    classifier = IntentClassifier()
    state["intent"] = classifier.classify(state["query"])
    print(f"[classify] intent: {state['intent']}")
    return state


def retrieve_node(state: AgentState) -> AgentState:
    from src.agent.tools import (
        search_news_tool,
        get_entity_trend_tool,
        summarize_topic_tool,
    )

    intent = state["intent"]
    query = state["query"]

    if intent == "trend_analysis":
        # Ekstrak entitas dari query — ambil kata kunci utama
        keywords = ["IHSG", "rupiah", "inflasi", "BI rate", "OJK", "Bank Indonesia"]
        entity = next(
            (kw for kw in keywords if kw.lower() in query.lower()),
            query.split()[-1]
        )
        state["context"] = get_entity_trend_tool(entity, days=7)

    elif intent == "entity_news":
        state["context"] = search_news_tool(query, n_results=5)

    elif intent == "comparative":
        # Ambil dua perspektif untuk perbandingan
        context_a = search_news_tool(query, n_results=3)
        context_b = summarize_topic_tool(query)
        state["context"] = f"{context_a}\n\n{context_b}"

    else:  # factual_query
        state["context"] = summarize_topic_tool(query)

    print(f"[retrieve] context length: {len(state['context'])} chars")
    return state


def answer_node(state: AgentState) -> AgentState:
    try:
        from anthropic import Anthropic
        client = Anthropic()

        prompt = f"""Kamu adalah analis keuangan Indonesia yang berbicara langsung dan selalu punya opini.

Pertanyaan pengguna: {state['query']}

Konteks dari database berita:
{state['context']}

Instruksi:
- Jawab langsung dalam 2-3 kalimat
- Mulai dari insight, bukan dari penjelasan konteks
- Berikan opini atau rekomendasi jika relevan
- Gunakan bahasa Indonesia yang natural"""

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        state["answer"] = response.content[0].text

    except Exception as e:
        # Fallback tanpa LLM — tetap berguna
        state["answer"] = (
            f"Berdasarkan data terkini:\n{state['context'][:300]}..."
        )
        print(f"LLM error (fallback): {e}")

    print(f"[answer] generated: {len(state['answer'])} chars")
    return state


def build_graph():
    try:
        from langgraph.graph import StateGraph, END

        workflow = StateGraph(AgentState)
        workflow.add_node("classify", classify_node)
        workflow.add_node("retrieve", retrieve_node)
        workflow.add_node("answer", answer_node)
        workflow.set_entry_point("classify")
        workflow.add_edge("classify", "retrieve")
        workflow.add_edge("retrieve", "answer")
        workflow.add_edge("answer", END)

        return workflow.compile()

    except ImportError:
        print("LangGraph not available, using sequential pipeline")
        return None


def run_pipeline(query: str) -> dict:
    """Jalankan pipeline secara sequential — fallback kalau LangGraph error."""
    state = AgentState(query=query, intent="", context="", answer="")
    state = classify_node(state)
    state = retrieve_node(state)
    state = answer_node(state)
    return dict(state)


if __name__ == "__main__":
    test_queries = [
        "bagaimana tren IHSG minggu ini?",
        "berita terbaru Bank Indonesia hari ini",
        "apa itu inflasi dan dampaknya?",
    ]

    print("=== LangGraph Agent Test ===\n")

    graph = build_graph()

    for query in test_queries:
        print(f"Query: {query}")
        print("-" * 50)

        if graph:
            result = graph.invoke({"query": query, "intent": "", "context": "", "answer": ""})
        else:
            result = run_pipeline(query)

        print(f"Intent : {result['intent']}")
        print(f"Answer : {result['answer']}")
        print()
