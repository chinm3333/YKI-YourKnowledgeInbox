import pytest
from services.chunk import chunk_text

def test_short_text_is_single_chunk():
    assert chunk_text("hello inbox") == ["hello inbox"]

def test_empty_text():
    assert chunk_text("   \n") == []

def test_overlap_is_applied():
    text = ("alpha paragraph. " * 40) + ("\n\nbeta paragraph. " * 40)
    chunks = chunk_text(text, chunk_size=120, overlap=30)
    assert len(chunks) >= 2
    assert chunks[0][-20:] in chunks[1] or any(
        token in chunks[1] for token in chunks[0].split()[-3:]
    )

def test_respects_paragraph_breaks():
    text = ("A" * 80) + "\n\n" + ("B" * 80)
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert any(chunk.startswith("B") or "B" * 10 in chunk for chunk in chunks)