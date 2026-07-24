import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from forum.services.rag_pipeline.vectorstore import FaissVectorStore

load_dotenv()

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.getenv("LLM_GATEWAY_KEY"),
            base_url=os.getenv("LLM_GATEWAY_URL"),
        )
    return _client


def _format_context_entry(meta: dict) -> str:
    text = meta.get("text", "")
    if meta.get("type") == "video":
        label = f"video '{meta.get('video_title', 'unknown')}' at {meta.get('start_label', '')}"
    else:
        source = meta.get("source", "")
        label = Path(source).name if source and source != "pasted-text" else "your pasted text"
    return f"[{label}] {text}"


def answer_from_store(store: FaissVectorStore, query: str, top_k: int = 5) -> str:
    results = store.query(query, top_k=top_k)
    texts = [_format_context_entry(r["metadata"]) for r in results if r["metadata"]]
    context = "\n\n".join(texts)

    if not context:
        return "No relevant documents found."

    prompt = f"""Answer the query below directly and concisely.
You are a strict RAG assistant.
Answer only using the provided context.
If the answer is not in the context, respond with: "No relevant documents found."
Do not use your own knowledge. Do not guess.

Query: {query}

Context:
{context}

Answer:"""

    try:
        response = _get_client().chat.completions.create(
            model=os.getenv("LLM_MODEL"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[ERROR] LLM call failed: {e}")
        return "Sorry, I was unable to process your question right now."