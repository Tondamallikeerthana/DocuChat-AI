from dotenv import load_dotenv

load_dotenv()

_rag_instance = None

def get_rag_instance():
    global _rag_instance
    if _rag_instance is None:
        print("[INFO] Initializing RAG pipeline...")
        from forum.services.rag_pipeline.search import RAGSearch
        _rag_instance = RAGSearch()
        print("[INFO] RAG pipeline ready.")
    return _rag_instance

def get_rag_response(query: str, thread) -> str:
    try:
        rag = get_rag_instance()
        return rag.search_and_summarize(query, top_k=3)
    except Exception as e:
        print(f"[ERROR] RAG failed: {e}")
        return "Sorry, I was unable to process your question right now."