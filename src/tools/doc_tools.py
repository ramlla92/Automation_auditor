# automation-auditor/src/tools/doc_tools.py
import os
import re
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
            
        if len(current_chunk) + len(para) + 2 > max_chars and current_chunk:
            chunks.append(current_chunk)
            current_chunk = para
        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
                
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
            
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    return [chunk for score, chunk in scored_chunks[:top_k]]

def verify_citations(text: str, known_files: List[str]) -> List[Dict[str, any]]:
    """
    Extracts potential file paths and cross-checks them against known repo files.
    """
    path_pattern = r'[a-zA-Z0-9_\-\./]+\.(?:py|md|yaml|json|jsonl|txt)'
    potential_paths = set(re.findall(path_pattern, text))
    
    # Ignore obvious URLs
    valid_paths = {p for p in potential_paths if not p.startswith("http://") and not p.startswith("https://")}
    
    sentences = re.split(r'(?<=[.!?]) +', text.replace('\n', ' '))
    lines = text.split('\n')
    
    results = []
    for path in valid_paths:
        normalized_path = path.lstrip("./")
        exists = any(known.endswith(normalized_path) for known in known_files)
        
        location = "body"
        claim_sentence = ""
        
        for sent in sentences:
            if path in sent:
                claim_sentence = sent.strip()
                break
                
        for line in lines:
            if path in line:
                sline = line.strip()
                if sline.startswith("#"):
                    location = "heading"
                elif sline.startswith("```"):
                    location = "code"
                elif sline.startswith("- ") or sline.startswith("* "):
                    location = "list"
                break
                
        results.append({
            "path": path,
            "exists": exists,
            "location": location,
            "claim_sentence": claim_sentence,
            "classification": "verified" if exists else "hallucinated"
        })
        
    return results

def analyze_concept_depth(text: str, concept: str) -> Dict[str, any]:
    """
    Classifies if a concept is just name-dropped or deeply explained.
    """
    concept_lower = concept.lower()
    text_lower = text.lower()
    
    index = text_lower.find(concept_lower)
    if index == -1:
        return {"concept": concept, "classification": "missing"}
        
    sentences = re.split(r'(?<=[.!?])\s+', text)
    concept_sent_idx = -1
    for i, s in enumerate(sentences):
        if concept_lower in s.lower():
            concept_sent_idx = i
            break
            
    if concept_sent_idx == -1:
        return {"concept": concept, "classification": "missing"}
        
    start_idx = max(0, concept_sent_idx - 1)
    end_idx = min(len(sentences), concept_sent_idx + 2)
    context_sentences = sentences[start_idx:end_idx]
    context = " ".join(context_sentences)
    
    target_sent = sentences[concept_sent_idx].strip()
    if len(target_sent.split()) < 10 or target_sent.startswith("#"):
        classification = "name-drop"
    else:
        deep_hints = ["how", "architecture", "graph", "judge", "swarm", "implement", "because", "since", "means", "due to", "synthesis", "process", "result"]
        depth_score = sum(hint in context.lower() for hint in deep_hints)
        classification = "deep-explanation" if depth_score >= 2 else "shallow"
    
    return {
        "concept": concept,
        "classification": classification,
        "context_snippet": context.strip()
    }
