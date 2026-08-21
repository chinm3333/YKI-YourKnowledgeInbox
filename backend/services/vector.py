import logging
from typing import Any
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from config import settings
logger = logging.getLogger(__name__)
COLLECTION = "knowledge_inbox"
_client = None
_collection = None

def get_collection():
    global _client, _collection
    if _collection is not None:
        return _collection
    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name=settings.embedding_model)
    _client = chromadb.PersistentClient(path=str(settings.chroma_path))
    _collection = _client.get_or_create_collection(name=COLLECTION,embedding_function=embedding_fn,metadata={"hnsw:space": "cosine"})
    logger.info("Chroma collection ready", extra={"source_type": "chroma"})
    return _collection

def upsert_chunks(item_id: str,chunks: list[str],metadata: dict[str, str]) -> int:
    if not chunks:
        return 0
    collection = get_collection()
    ids = [f"{item_id}:{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "item_id": item_id,
            "chunk_index": i,
            "title": metadata.get("title", ""),
            "type": metadata.get("type", ""),
            "source": metadata.get("source") or "",
        }
        for i in range(len(chunks))
    ]
    collection.upsert(ids=ids, documents=chunks, metadatas=metadatas)
    return len(chunks)

def query_chunks(question: str, top_k: int) -> list[dict[str, Any]]:
    collection = get_collection()
    if collection.count() == 0:
        return []
    result = collection.query(
        query_texts=[question],
        n_results=min(top_k, max(collection.count(), 1)),
        include=["documents", "metadatas", "distances"],
    )
    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]
    hits: list[dict[str, Any]] = []
    for doc, meta, distance in zip(documents, metadatas, distances):
        if not doc:
            continue
        # Cosine distance: 0 is identical. Convert to a 0–1 similarity-ish score.
        score = max(0.0, 1.0 - float(distance))
        if score < settings.min_chunk_score:
            continue
        hits.append(
            {
                "item_id": meta.get("item_id"),
                "title": meta.get("title") or "Untitled",
                "type": meta.get("type"),
                "source": meta.get("source") or None,
                "snippet": doc,
                "score": round(score, 4),
            }
        )
    return hits

def delete_chunks(item_id: str) -> None:
    collection = get_collection()
    collection.delete(where={"item_id": item_id})