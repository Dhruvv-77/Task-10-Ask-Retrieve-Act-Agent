import os
import glob
import re
import json
import logging
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings

logger = logging.getLogger("rag.ingest")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "documents"))
CHROMA_PERSIST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))

# Documented chunking configuration:
# 350-450 tokens (~1500 chars), ~15% overlap (~220 chars)
CHUNK_SIZE_CHARS = 1600
CHUNK_OVERLAP_CHARS = 240

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE_CHARS, overlap: int = CHUNK_OVERLAP_CHARS) -> List[str]:
    """
    Split text into chunks with sliding window overlap.
    Preserves paragraph and sentence boundaries wherever feasible.
    """
    if len(text) <= chunk_size:
        return [text.strip()]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:].strip())
            break
        
        # Try to find paragraph break or sentence break near end
        break_pos = text.rfind("\n\n", start, end)
        if break_pos == -1 or break_pos <= start:
            break_pos = text.rfind(". ", start, end)
        if break_pos != -1 and break_pos > start:
            end = break_pos + 1
            
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
        
    return chunks

def extract_metadata(doc_text: str, filename: str) -> Dict[str, str]:
    """Extract docId, title, and section from markdown header."""
    doc_id = "unknown"
    title = os.path.splitext(filename)[0]
    
    match_id = re.search(r"Doc ID:\s*([a-zA-Z0-9_-]+)", doc_text)
    if match_id:
        doc_id = match_id.group(1)
        
    match_title = re.search(r"^#\s+(.+)$", doc_text, re.MULTILINE)
    if match_title:
        title = match_title.group(1).split("(Doc ID")[0].strip()
        
    return {
        "docId": doc_id,
        "title": title,
        "section": "General",
        "source_url": f"https://docs.company.internal/policies/{filename}"
    }

def ingest_documents(data_dir: str = DATA_DIR) -> int:
    """Ingest markdown files from data_dir into Chroma vector store."""
    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    collection = client.get_or_create_collection(
        name="capstone-kb",
        metadata={"hnsw:space": "cosine"}
    )

    pattern = os.path.join(data_dir, "*.md")
    files = glob.glob(pattern)
    logger.info(f"Discovered {len(files)} markdown policy documents in {data_dir}.")

    all_ids = []
    all_docs = []
    all_metadatas = []

    for file_path in files:
        filename = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        meta = extract_metadata(content, filename)
        chunks = chunk_text(content)

        for idx, chunk in enumerate(chunks):
            chunk_id = f"{meta['docId']}_chunk_{idx}"
            chunk_meta = dict(meta)
            chunk_meta["chunk_index"] = idx
            
            all_ids.append(chunk_id)
            all_docs.append(chunk)
            all_metadatas.append(chunk_meta)

    if all_ids:
        # Upsert into Chroma collection
        collection.upsert(
            ids=all_ids,
            documents=all_docs,
            metadatas=all_metadatas
        )
        logger.info(f"Successfully upserted {len(all_ids)} chunks into ChromaDB ('capstone-kb').")
        
    return len(all_ids)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    count = ingest_documents()
    print(f"Ingested {count} chunks successfully.")
