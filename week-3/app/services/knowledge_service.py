import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.config import (
    DOCUMENTS_DIR,
    KNOWLEDGE_BASE_PATH,
    EMBEDDING_MODEL
)
from app.services.chunking_service import chunk_markdown_document
from app.services.embedding_service import get_embedding


def get_raw_documents() -> List[Dict[str, Any]]:
    """Scan and load all raw markdown policy documents from the data/documents directory."""
    if not os.path.exists(DOCUMENTS_DIR):
        return []

    docs = []
    for filename in sorted(os.listdir(DOCUMENTS_DIR)):
        if filename.endswith(".md"):
            doc_id = filename[:-3]
            filepath = os.path.join(DOCUMENTS_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            title = doc_id.replace("_", " ").title()
            for line in content.splitlines():
                if line.strip().startswith("# "):
                    title = line.strip()[2:].strip()
                    break

            docs.append({
                "id": doc_id,
                "filename": filename,
                "title": title,
                "content": content,
                "char_count": len(content),
                "line_count": len(content.splitlines())
            })
    return docs


def load_knowledge_base() -> Optional[Dict[str, Any]]:
    """Load the persisted knowledge base JSON from disk if it exists."""
    if not os.path.exists(KNOWLEDGE_BASE_PATH):
        return None
    try:
        with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


async def build_knowledge_base() -> Dict[str, Any]:
    """
    Execute the full Exercise 2 pipeline:
    Raw Documents -> Semantic Chunking -> Ollama Embeddings -> Local JSON Vector Representation.
    
    Determines embedding dimension dynamically from the model's actual output.
    Fails explicitly if Ollama or the embedding model is unavailable.
    """
    raw_docs = get_raw_documents()
    if not raw_docs:
        raise RuntimeError(f"No documents found in '{DOCUMENTS_DIR}' to index.")

    all_chunks: List[Dict[str, Any]] = []
    doc_summaries: List[Dict[str, Any]] = []
    detected_dimension: Optional[int] = None

    for doc in raw_docs:
        chunks = chunk_markdown_document(
            doc_id=doc["id"],
            markdown_content=doc["content"],
            filename=doc["filename"]
        )

        # Generate real embedding for each chunk
        for chunk in chunks:
            vector = await get_embedding(chunk["text"])
            
            # Dynamically determine dimension from the actual response
            if detected_dimension is None:
                detected_dimension = len(vector)

            chunk["embedding"] = vector
            all_chunks.append(chunk)

        doc_summaries.append({
            "id": doc["id"],
            "title": doc["title"],
            "filename": doc["filename"],
            "total_chunks": len(chunks)
        })

    kb_data = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "embedding_model": EMBEDDING_MODEL,
            "embedding_dimension": detected_dimension or 0,
            "total_documents": len(raw_docs),
            "total_chunks": len(all_chunks)
        },
        "documents": doc_summaries,
        "chunks": all_chunks
    }

    # Ensure parent directory exists and persist to JSON
    os.makedirs(os.path.dirname(KNOWLEDGE_BASE_PATH), exist_ok=True)
    with open(KNOWLEDGE_BASE_PATH, "w", encoding="utf-8") as f:
        json.dump(kb_data, f, indent=2)

    return kb_data


def get_knowledge_summary() -> Dict[str, Any]:
    """Provide high-level summary of the knowledge base for inspection UI and API."""
    kb = load_knowledge_base()
    raw_docs = get_raw_documents()

    if kb is None:
        return {
            "status": "not_indexed",
            "message": "Knowledge base not yet generated. Click 'Index Knowledge Base' to process documents.",
            "total_documents": len(raw_docs),
            "total_chunks": 0,
            "embedding_model": EMBEDDING_MODEL,
            "embedding_dimension": None
        }

    meta = kb.get("metadata", {})
    return {
        "status": "ready",
        "message": "Knowledge base indexed and ready.",
        "total_documents": meta.get("total_documents", len(raw_docs)),
        "total_chunks": meta.get("total_chunks", len(kb.get("chunks", []))),
        "embedding_model": meta.get("embedding_model", EMBEDDING_MODEL),
        "embedding_dimension": meta.get("embedding_dimension"),
        "generated_at": meta.get("generated_at")
    }
