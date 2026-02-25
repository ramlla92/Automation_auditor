import pytest
from src.tools.doc_tools import chunk_text, simple_keyword_search

def test_chunk_text_basic():
    """Test basic chunking logic."""
    text = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
    chunks = chunk_text(text, max_chars=20)
    # Paragraph 1 is 11 chars. Paragraph 2 is 11 chars. 
    # 11 + 2 (newline) + 11 > 20, so they should split.
    assert len(chunks) == 3
    assert "Paragraph 1" in chunks[0]
    assert "Paragraph 2" in chunks[1]

def test_chunk_text_oversized_paragraph():
    """Test chunking when a single paragraph is too large."""
    text = "A" * 50
    chunks = chunk_text(text, max_chars=20)
    assert len(chunks) == 3 # 20, 20, 10
    assert len(chunks[0]) == 20
    assert len(chunks[1]) == 20
    assert len(chunks[2]) == 10

def test_simple_keyword_search():
    """Test RAG-lite keyword ranking."""
    chunks = [
        "The apple is red and sweet.",
        "Bananas are yellow and long.",
        "Apples are better than oranges, maybe the best apple is a Fuji apple."
    ]
    results = simple_keyword_search(chunks, "apple", top_k=2)
    
    assert len(results) == 2
    # Third chunk has "apple" 3 times (case insensitive check in tool matches "Apple" and "apple")
    # Wait, tool does "query.lower() in chunk.lower() count"
    # "Apples" counts as 1. "apple" counts as 1. "apple" counts as 1. Total 3.
    # First chunk has "apple" 1 time.
    assert "Fuji apple" in results[0]
    assert "is red" in results[1]

def test_simple_keyword_search_no_match():
    """Test no matches found."""
    chunks = ["Hello world"]
    results = simple_keyword_search(chunks, "missing")
    assert results == []
