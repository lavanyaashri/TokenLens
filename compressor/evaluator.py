"""
evaluator.py
Measures how much quality is lost after compression.

Two metrics:
1. ROUGE-L  — lexical overlap between baseline and compressed answer
2. Semantic Similarity — cosine similarity of answer embeddings
"""

from rouge_score import rouge_scorer
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from llm.ollama_client import generate


_scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
_embed_model = None

_QA_PROMPT = """Use the context below to answer the question. Be concise.

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


def answer_question(context: str, question: str, model: str = "llama3.2") -> str:
    """Ask the LLM a question given a context."""
    prompt = _QA_PROMPT.format(context=context, question=question)
    return generate(prompt, model=model, temperature=0.0)


def evaluate(baseline_answer: str, compressed_answer: str) -> dict:
    """
    Compare two answers and return quality scores.
    baseline_answer  = answer from full uncompressed text
    compressed_answer = answer from compressed text
    """
    # 1. ROUGE-L: measures word overlap
    rouge_result = _scorer.score(baseline_answer, compressed_answer)
    rouge_l = round(rouge_result["rougeL"].fmeasure, 4)

    # 2. Semantic similarity: measures meaning overlap
    model = _get_embed_model()
    embeddings = model.encode([baseline_answer, compressed_answer])
    sem_sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    sem_sim = round(float(sem_sim), 4)

    # 3. Combined score
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
    model: str = "llama3.2",
    on_status=None,
) -> dict:
    """
    Full pipeline:
    1. Get baseline answer from full text
    2. Get answer from compressed text
    3. Score them against each other
    """
    if on_status:
        on_status("Getting baseline answer from full text...")
    baseline_answer = answer_question(original_text, question, model=model)

    if on_status:
        on_status("Getting answer from compressed text...")
    compressed_answer = answer_question(compressed_text, question, model=model)

    if on_status:
        on_status("Scoring quality...")
    scores = evaluate(baseline_answer, compressed_answer)

    return scores 