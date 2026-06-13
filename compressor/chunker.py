"""
chunker.py
Splits long text into overlapping chunks for processing.
"""


def split_into_chunks(text: str, chunk_size: int = 200, overlap: int = 30) -> list[str]:
    """
    Split text into word-based chunks with overlap.
    overlap means consecutive chunks share some words so
    we don't lose context at the boundaries.
    """
    words = text.split()

    if len(words) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap

        if chunk_size <= overlap:
            break

    return chunks


def word_count(text: str) -> int:
    return len(text.split())


def token_estimate(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return len(text) // 4

