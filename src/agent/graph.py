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
        keywords = ["IHSG", "rupiah", "inflasi", "BI rate", "OJK", "Bank Indonesia"]
        entity = next(
            (kw for kw in keywords if kw.lower() in query.lower()),
            query.split()[-1]
        )
        state["context"] = get_entity_trend_tool(entity, days=7)

    elif intent == "entity_news":
        state["context"] = search_news_tool(query, n_results=5)

    elif intent == "comparative":
        context_a = search_news_tool(query, n_results=3)
        context_b = summarize_topic_tool(query)
        state["context"] = f"{context_a}\n\n{context_b}"

    else:
        state["context"] = summarize_topic_tool(query)

    print(f"[retrieve] context length: {len(state['context'])} chars")
    return state


def answer_node(state: AgentState) -> AgentState:
    prompt = f"""Kamu adalah analis keuangan Indonesia yang berbicara langsung dan selalu punya opini.

Pertanyaan pengguna: {state['query']}

Konteks dari database berita:
{state['context']}

Instruksi:
- Jawab langsung dalam 2-3 kalimat
- Mulai dari insight, bukan dari penjelasan konteks
- Berikan opini atau rekomendasi jika relevan
- Gunakan bahasa Indonesia yang natural"""

    # Coba Groq dulu (gratis)
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
            )
            state["answer"] = response.choices[0].message.content
            print(f"[answer] via Groq: {len(state['answer'])} chars")
            return state
        except Exception as e:
            print(f"Groq error: {e}")

    # Fallback ke Anthropic
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key and anthropic_key != "your_key_here":
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=anthropic_key)
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}]
            )
            state["answer"] = response.content[0].text
            print(f"[answer] via Anthropic: {len(state['answer'])} chars")
            return state
        except Exception as e:
            print(f"Anthropic error: {e}")

    # Final fallback tanpa LLM
    state["answer"] = f"Berdasarkan data terkini:\n{state['context'][:300]}..."
    print(f"[answer] fallback: {len(state['answer'])} chars")
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
        return None


def run_pipeline(query: str) -> dict:
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
    for query in test_queries:
        print(f"Query: {query}")
        print("-" * 50)
        result = run_pipeline(query)
        print(f"Intent : {result['intent']}")
        print(f"Answer : {result['answer']}")
        print()
