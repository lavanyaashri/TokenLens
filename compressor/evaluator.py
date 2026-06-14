"""
evaluator.py
Measures how much quality is lost after compression.

Two metrics:
1. ROUGE-L  — lexical overlap between baseline and compressed answer
2. Semantic Similarity — cosine similarity of answer embeddings

Runs both LLM calls in parallel using asyncio for speed.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from rouge_score import rouge_scorer
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from llm.ollama_client import generate


_scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
_embed_model = None
_executor = ThreadPoolExecutor(max_workers=4)

_QA_PROMPT = """Use the context below to answer the question. Be concise. Two sentences maximum.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:"""


def _get_embed_model():
    global _embed_model
    if _embed_model is None:
        _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embed_model


def answer_question(context: str, question: str, model: str = "llama3.2:1b") -> str:
    """Ask the LLM a question given a context."""
    prompt = _QA_PROMPT.format(context=context, question=question)
    return generate(prompt, model=model, temperature=0.0)


def evaluate(baseline_answer: str, compressed_answer: str) -> dict:
    """Compare two answers and return quality scores."""
    # ROUGE-L
    rouge_result = _scorer.score(baseline_answer, compressed_answer)
    rouge_l = round(rouge_result["rougeL"].fmeasure, 4)

    # Semantic similarity
    model = _get_embed_model()
    embeddings = model.encode([baseline_answer, compressed_answer])
    sem_sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    sem_sim = round(float(sem_sim), 4)

    # Combined
    combined = round((rouge_l + sem_sim) / 2, 4)

    return {
        "rouge_l": rouge_l,
        "semantic_similarity": sem_sim,
        "combined_score": combined,
        "baseline_answer": baseline_answer,
        "compressed_answer": compressed_answer,
    }


def run_full_eval(
    original_text: str,
    compressed_text: str,
    question: str,
    model: str = "llama3.2:1b",
    on_status=None,
) -> dict:
    """
    Run baseline and compressed answers IN PARALLEL using threads.
    This cuts evaluation time roughly in half vs running sequentially.
    """
    if on_status:
        on_status("Getting answers in parallel...")

    # Run both LLM calls at the same time in separate threads
    with ThreadPoolExecutor(max_workers=2) as executor:
        baseline_future = executor.submit(
            answer_question, original_text, question, model
        )
        compressed_future = executor.submit(
            answer_question, compressed_text, question, model
        )

        baseline_answer = baseline_future.result()
        compressed_answer = compressed_future.result()

    if on_status:
        on_status("Scoring quality...")

    scores = evaluate(baseline_answer, compressed_answer)
    return scores