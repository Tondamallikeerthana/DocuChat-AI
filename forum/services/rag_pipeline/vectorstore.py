import os
import faiss
import numpy as np
import pickle
from typing import List, Any
from sentence_transformers import SentenceTransformer
from forum.services.rag_pipeline.embedding import EmbeddingPipeline
 
class FaissVectorStore:
  def __init__(self, persist_dir: str = "faiss_store", embedding_model: str="all-MiniLM-L6-v2",chunk_size: int=1000,chunk_overlap: int = 200):
    self.persist_dir = persist_dir
    os.makedirs(self.persist_dir, exist_ok=True)
    self.index = None
    self.metadata=[]
    self.embedding_model=embedding_model
    self.model=SentenceTransformer(embedding_model)
    self.chunk_size=chunk_size
    self.chunk_overlap=chunk_overlap
    print(f"[INFO] Loaded embedding model: {embedding_model}")
 
  def build_from_documents(self, documents: List[Any]):
    print(f"[INFO] Building vector store from {len(documents)} raw documents...")
    emb_pipe = EmbeddingPipeline(model_name=self.embedding_model, chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
    chunks = emb_pipe.chunk_documents(documents)
    embeddings = emb_pipe.embed_chunks(chunks)
    # NOTE: previously this only kept {"text": ...}, which silently dropped
    # source/page/video_title/timestamp metadata. Now we keep everything
    # langchain attached to the chunk and just add "text" alongside it.
    metadatas = [{**chunk.metadata, "text": chunk.page_content} for chunk in chunks]
    self.add_embeddings(np.array(embeddings).astype('float32'),metadatas)
    self.save()
    print(f"[INFO] Vector store built and saved to {self.persist_dir}")
 
  def add_documents(self, documents: List[Any]):
    """
    Add new documents (e.g. a newly uploaded video, or a new PDF) to an
    already-built vector store WITHOUT rebuilding from the whole data
    folder. Call self.load() first if you're adding to a store from a
    previous run, then call this, which appends + saves.
    """
    if not documents:
      print("[INFO] No new documents to add.")
      return
    print(f"[INFO] Adding {len(documents)} new raw documents to existing vector store...")
    emb_pipe = EmbeddingPipeline(model_name=self.embedding_model, chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
    chunks = emb_pipe.chunk_documents(documents)
    embeddings = emb_pipe.embed_chunks(chunks)
    metadatas = [{**chunk.metadata, "text": chunk.page_content} for chunk in chunks]
    self.add_embeddings(np.array(embeddings).astype('float32'), metadatas)
    self.save()
    print(f"[INFO] Added {len(chunks)} new chunks. Vector store saved to {self.persist_dir}")
 
  def add_embeddings(self, embeddings: np.ndarray, metadatas: List[Any] = None):
    dim = embeddings.shape[1]
    if self.index is None:
      self.index=faiss.IndexFlatL2(dim)
    self.index.add(embeddings)
    if metadatas:
      self.metadata.extend(metadatas)
    print(f"[INFO] Added {embeddings.shape[0]} vectors to Fiass index.")
 
  def save(self):
    fiass_path = os.path.join(self.persist_dir,"faiss.index")
    meta_path = os.path.join(self.persist_dir,"metadata.pkl")
    faiss.write_index(self.index, fiass_path)
    with open(meta_path,"wb") as f:
      pickle.dump(self.metadata, f)
    print(f"[INFO] Saved Fiass index and metadata to {self.persist_dir}")
 
  def load(self):
    faiss_path = os.path.join(self.persist_dir,"faiss.index")
    meta_path = os.path.join(self.persist_dir,"metadata.pkl")
    self.index = faiss.read_index(faiss_path)
    with open(meta_path, "rb") as f:
      self.metadata=pickle.load(f)
    print(f"[INFO] Loaded Fiass index and metadata from {self.persist_dir}")
 
  def search(self, query_embedding: np.ndarray, top_k: int = 5):
    D, I =self.index.search(query_embedding,top_k)
    results = []
    for idx, dist in zip(I[0], D[0]):
      meta = self.metadata[idx] if idx < len(self.metadata) else None
      results.append({"index": idx,"distance": dist,"metadata": meta})
    return results
  
  def query(self, query_text: str,top_k: int = 5):
    print(f"[INFO] Querying vector store for: '{query_text}'")
    query_emb = self.model.encode([query_text]).astype('float32')
    return self.search(query_emb, top_k=top_k)