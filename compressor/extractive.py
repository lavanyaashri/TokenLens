"""
extractive.py
Compression Strategy A: Embedding-based extraction.

How it works:
1. Embed every chunk using a local sentence-transformer model
2. Embed the query/task
3. Rank chunks by cosine similarity to the query
4. Keep only the top-k most relevant chunks
5. Reassemble them in original order (preserves coherence)
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from compressor.chunker import split_into_chunks


# Load once at module level — runs fully locally, no API needed
# ~90MB download on first use
_MODEL_NAME = "all-MiniLM-L6-v2"
_model = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def extractive_compress(
    text: str,
    query: str,
    compression_ratio: float = 0.5,
    chunk_size: int = 200,
    overlap: int = 30,
) -> dict:
    """
    Compress text by keeping only the chunks most relevant to the query.
    """
    model = _get_model()

    # 1. Split into chunks
    chunks = split_into_chunks(text, chunk_size=chunk_size, overlap=overlap)
    n_chunks = len(chunks)

    if n_chunks == 1:
        return {
            "compressed_text": text,
            "kept_indices": [0],
            "scores": [1.0],
            "stats": _build_stats(text, text, n_chunks, n_chunks),
        }

    # 2. Embed all chunks and the query
    chunk_embeddings = model.encode(chunks, show_progress_bar=False)
    query_embedding = model.encode([query], show_progress_bar=False)

    # 3. Score each chunk by similarity to the query
    similarities = cosine_similarity(query_embedding, chunk_embeddings)[0]

    # 4. Keep the top-k chunks
    n_keep = max(1, int(np.ceil(n_chunks * compression_ratio)))

    # 5. Sort kept chunks by original position so text flows naturally
    top_indices = np.argsort(similarities)[-n_keep:]
    top_indices_sorted = sorted(top_indices.tolist())

    # 6. Join them back together
    kept_chunks = [chunks[i] for i in top_indices_sorted]
    compressed_text = "\n\n".join(kept_chunks)

    return {
        "compressed_text": compressed_text,
        "kept_indices": top_indices_sorted,
        "scores": similarities.tolist(),
        "stats": _build_stats(text, compressed_text, n_chunks, n_keep),
    }


def _build_stats(original, compressed, total_chunks, kept_chunks):
    orig_tokens = len(original) // 4
    comp_tokens = len(compressed) // 4
    saved = orig_tokens - comp_tokens
    ratio = (saved / orig_tokens * 100) if orig_tokens > 0 else 0

    return {
        "original_tokens": orig_tokens,
        "compressed_tokens": comp_tokens,
        "tokens_saved": saved,
        "compression_pct": round(ratio, 1),
        "chunks_total": total_chunks,
        "chunks_kept": kept_chunks,
    }