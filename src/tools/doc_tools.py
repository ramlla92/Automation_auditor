# automation-auditor/src/tools/doc_tools.py
import os
from typing import List, Dict, Optional
from pypdf import PdfReader

class PdfLoadError(Exception):
    """Raised when PDF ingestion fails."""
    pass

def load_pdf_text(pdf_path: str) -> str:
    """
    Extracts all text from a PDF file.
    """
    if not os.path.exists(pdf_path):
        raise PdfLoadError(f"PDF file not found: {pdf_path}")
    
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        raise PdfLoadError(f"Failed to load PDF {pdf_path}: {str(e)}")

def chunk_text(text: str, max_chars: int = 1000) -> List[str]:
    """
    Splits text into chunks, respecting paragraph boundaries where possible.
    """
    if not text:
        return []

    # Split into paragraphs first
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # If adding this paragraph exceeds max_chars, save current and start new
        if len(current_chunk) + len(para) + 2 > max_chars and current_chunk:
            chunks.append(current_chunk)
            current_chunk = para
        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
                
        # Handle cases where a single paragraph is larger than max_chars
        while len(current_chunk) > max_chars:
            chunks.append(current_chunk[:max_chars])
            current_chunk = current_chunk[max_chars:].strip()

    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks

def ingest_pdf(pdf_path: str, max_chars: int = 1000) -> List[str]:
    """
    Convenience wrapper to load and chunk a PDF.
    """
    text = load_pdf_text(pdf_path)
    return chunk_text(text, max_chars)

def simple_keyword_search(chunks: List[str], query: str, top_k: int = 5) -> List[str]:
    """
    Scores and returns top_k chunks based on simple keyword frequency.
    """
    query_lower = query.lower()
    scored_chunks = []
    
    for chunk in chunks:
        score = chunk.lower().count(query_lower)
        if score > 0:
            scored_chunks.append((score, chunk))
            
    # Sort by score descending
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    
    # Return top_k content only
    return [chunk for score, chunk in scored_chunks[:top_k]]
