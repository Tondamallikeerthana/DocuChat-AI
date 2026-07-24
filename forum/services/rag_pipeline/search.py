# import os
# from pathlib import Path
# from dotenv import load_dotenv
# from forum.services.rag_pipeline.vectorstore import FaissVectorStore
# from forum.services.rag_pipeline.data_loader import load_all_documents
# from langchain_groq import ChatGroq

# load_dotenv()

# class RAGSearch:
#     def __init__(self, persist_dir: str = "faiss_store", embedding_model: str = "all-MiniLM-L6-v2", llm_model: str = "openai/gpt-oss-120b"):
#         self.vectorstore = FaissVectorStore(persist_dir, embedding_model)
        
#         BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
#         data_path = str(BASE_DIR / "data")

#         # #Load or build vectorstore
#         # faiss_path = os.path.join(persist_dir, "faiss.index")
#         # meta_path = os.path.join(persist_dir, "metadata.pkl") 
#         # if not (os.path.exists(faiss_path) and os.path.exists(meta_path)):
#         #     print("[INFO] Loading all documents from data folder...")
#         #     docs = load_all_documents("data_path")
#         #     print(f"[INFO] Loaded {len(docs)} documents.")
#         #     self.vectorstore.build_from_documents(docs)
#         # else:
#         #     self.vectorstore.load()

#         print("[INFO] Loading all documents from data folder...")
#         docs = load_all_documents(data_path)
#         print(f"[INFO] Loaded {len(docs)} documents.")
#         print("[INFO] Rebuilding vector database...")
#         self.vectorstore.build_from_documents(docs)
#         self.vectorstore.load()
#         groq_api_key = os.getenv("GROQ_API_KEY")
#         self.llm = ChatGroq(groq_api_key=groq_api_key, model_name=llm_model)
#         print(f"[INFO] Groq LLM initialized: {llm_model}")

#     def search_and_summarize(self, query: str, top_k: int = 10) -> str:
#         results = self.vectorstore.query(query, top_k=top_k)
#         texts = [r["metadata"].get("text", "") for r in results if r["metadata"]]
#         context = "\n\n".join(texts)
#         if not context:
#             return "No relevant documents found."
#         prompt = f""" Answer the query below directly and concisely, without any extra background or implementation details. Use short, clear sentences.
#         You are a strict RAG assistant.
#         Answer only using provided content if answr is not fount in the context respond exactly with:
#         "No relevant documents found."
#         Do Not use your own knowledge.
#         Do Not guess.

# Query: {query}

# Context:
# {context}

# Answer:"""
#         response = self.llm.invoke(prompt)
#         return response.content.strip()



import os
from pathlib import Path
from dotenv import load_dotenv
from forum.services.rag_pipeline.vectorstore import FaissVectorStore
from forum.services.rag_pipeline.data_loader import load_all_documents
from openai import OpenAI
 
load_dotenv()
 
print(f"[DEBUG] Model: {os.getenv('LLM_MODEL')}")
 
 
def _format_context_entry(meta: dict) -> str:
    """Label each retrieved chunk with where it came from so the LLM
    can reference it (e.g. a video name + timestamp, or a file name)."""
    text = meta.get("text", "")
    if meta.get("type") == "video":
        label = f"video '{meta.get('video_title', 'unknown')}' at {meta.get('start_label', '')}"
    else:
        source = meta.get("source", "")
        label = Path(source).name if source else "document"
    return f"[{label}] {text}"
 
 
class RAGSearch:
    def __init__(self, persist_dir: str = "faiss_store",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        self.vectorstore = FaissVectorStore(persist_dir, embedding_model)
 
        BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
        data_path = str(BASE_DIR / "data")
 
        faiss_path = os.path.join(persist_dir, "faiss.index")
        meta_path = os.path.join(persist_dir, "metadata.pkl")
 
        if not (os.path.exists(faiss_path) and os.path.exists(meta_path)):
            print("[INFO] Building vector database for first time...")
            docs = load_all_documents(data_path)
            print(f"[INFO] Loaded {len(docs)} documents.")
            self.vectorstore.build_from_documents(docs)
        else:
            print("[INFO] Vector database already exists, loading...")
 
        self.vectorstore.load()
 
        gateway_url = os.getenv("LLM_GATEWAY_URL")
        gateway_key = os.getenv("LLM_GATEWAY_KEY")
 
        self.client = OpenAI(
            api_key=gateway_key,
            base_url=gateway_url
        )
 
        self.model_name = os.getenv("LLM_MODEL")
        print(f"[INFO] Using model: {self.model_name}")
 
    def search_and_summarize(self, query: str, top_k: int = 10) -> str:
        results = self.vectorstore.query(query, top_k=top_k)
        texts = [_format_context_entry(r["metadata"]) for r in results if r["metadata"]]
        context = "\n\n".join(texts)
 
        if not context:
            return "No relevant documents found."
 
        prompt = f"""Answer the query below directly and concisely.
You are a strict RAG assistant.
Answer only using the provided context.
If the answer is not in the context, respond with: "No relevant documents found."
Do not use your own knowledge. Do not guess.
Each context entry is labeled with its source in square brackets (a file name,
or a video title with a timestamp like "video 'Lecture 3' at 04:12"). If the
relevant content came from a video, mention the video title and timestamp in
your answer so the student knows where to look.
 
Query: {query}
 
Context:
{context}
 
Answer:"""
 
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=112,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[ERROR] LLM call failed: {e}")
            return "Sorry, I was unable to process your question right now."