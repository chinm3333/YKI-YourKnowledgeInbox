import re

def chunk_text(text: str, chunk_size: int = 700, overlap: int = 100) -> list[str]:
    cleaned = re.sub(r"\r\n?", "\n", text).strip()
    if not cleaned:
        return []
    if len(cleaned) <= chunk_size:
        return [cleaned]
    overlap = max(0, min(overlap, chunk_size - 1))
    chunks: list[str] = []
    start = 0
    length = len(cleaned)
    while start < length:
        end = min(start + chunk_size, length)
        if end < length:
            end = _best_break(cleaned, start, end)
        piece = cleaned[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= length:
            break
        next_start = end - overlap
        if next_start <= start:
            next_start = end
        start = next_start
    return chunks

def _best_break(text: str, start: int, end: int) -> int:
    window = text[start:end]
    min_pos = max(1, int(len(window) * 0.4))
    for sep in ("\n\n", "\n", ". ", " "):
        idx = window.rfind(sep)
        if idx >= min_pos:
            return start + idx + len(sep)
    return end