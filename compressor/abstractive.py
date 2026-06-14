"""
abstractive.py
Compression Strategy B: LLM-based summarization.

How it works:
1. Split text into chunks
2. For each chunk, ask a local LLM to summarize it concisely
3. Concatenate all summaries into the compressed prompt
"""

from compressor.chunker import split_into_chunks
from llm.ollama_client import generate


_SUMMARIZE_PROMPT = """Summarize the following text as concisely as possible.
Keep all key facts, numbers, and named entities. Remove filler and redundancy.
Respond with ONLY the summary — no preamble.

TEXT:
{chunk}

SUMMARY:"""


def abstractive_compress(
    text: str,
    model: str = "llama3.2:1b",
    chunk_size: int = 300,
    overlap: int = 30,
    on_progress=None,
) -> dict:
    """
    Compress text by summarizing each chunk with a local LLM.
    """
    chunks = split_into_chunks(text, chunk_size=chunk_size, overlap=overlap)
    n_chunks = len(chunks)
    summaries = []

    for i, chunk in enumerate(chunks):
        if on_progress:
            on_progress(i + 1, n_chunks)

        prompt = _SUMMARIZE_PROMPT.format(chunk=chunk)
        summary = generate(prompt, model=model, temperature=0.0)
        summaries.append(summary)

    compressed_text = "\n\n".join(summaries)

    return {
        "compressed_text": compressed_text,
        "chunk_summaries": list(zip(chunks, summaries)),
        "stats": _build_stats(text, compressed_text, n_chunks),
    }


def _build_stats(original, compressed, n_chunks):
    orig_tokens = len(original) // 4
    comp_tokens = len(compressed) // 4
    saved = orig_tokens - comp_tokens
    ratio = (saved / orig_tokens * 100) if orig_tokens > 0 else 0

    return {
        "original_tokens": orig_tokens,
        "compressed_tokens": comp_tokens,
        "tokens_saved": saved,
        "compression_pct": round(ratio, 1),
        "chunks_processed": n_chunks,
    }