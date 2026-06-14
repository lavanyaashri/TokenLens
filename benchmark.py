"""
benchmark.py
Automatically benchmarks TokenLens compression quality across 100 Wikipedia articles.
Saves results to benchmark_results.csv for publishing on HuggingFace.

Run with: python benchmark.py
"""

import csv
import time
import random
import wikipediaapi
from compressor.extractive import extractive_compress
from compressor.evaluator import run_full_eval

# ── Config ────────────────────────────────────────────────────────────────────
OUTPUT_FILE = "benchmark_results.csv"
ARTICLES_PER_CATEGORY = 20
RATIOS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
QA_MODEL = "llama3.2"

# One question per category that works for any article in that category
CATEGORIES = [
    {
        "name": "science",
        "topics": [
            "Quantum mechanics", "Black hole", "DNA", "Photosynthesis",
            "Evolution", "General relativity", "Neuroscience", "Climate change",
            "Artificial intelligence", "Periodic table", "Gravity", "Vaccine",
            "Stem cell", "Nuclear fusion", "Plate tectonics", "Ecosystem",
            "Thermodynamics", "Electromagnetism", "Cell biology", "Astronomy"
        ],
        "question": "What is the main concept explained in this article?"
    },
    {
        "name": "history",
        "topics": [
            "World War II", "French Revolution", "Roman Empire",
            "Industrial Revolution", "Cold War", "Renaissance",
            "American Civil War", "Ancient Egypt", "Byzantine Empire",
            "Mongol Empire", "Ottoman Empire", "British Empire",
            "Ancient Greece", "Russian Revolution", "Age of Exploration",
            "Feudalism", "Crusades", "Ming dynasty", "Aztec Empire", "Viking Age"
        ],
        "question": "What were the main causes and effects described in this article?"
    },
    {
        "name": "technology",
        "topics": [
            "Internet", "Smartphone", "Cryptocurrency", "Machine learning",
            "Computer programming", "Semiconductor", "Social media",
            "Cloud computing", "Robotics", "Electric vehicle",
            "Blockchain", "Virtual reality", "5G", "Quantum computing",
            "Cybersecurity", "Operating system", "Database", "Algorithm",
            "Neural network", "Augmented reality"
        ],
        "question": "What is this technology and how does it work?"
    },
    {
        "name": "science_people",
        "topics": [
            "Albert Einstein", "Isaac Newton", "Marie Curie", "Charles Darwin",
            "Stephen Hawking", "Nikola Tesla", "Richard Feynman", "Alan Turing",
            "Galileo Galilei", "Carl Sagan", "Ada Lovelace", "James Watson",
            "Rosalind Franklin", "Max Planck", "Niels Bohr", "Werner Heisenberg",
            "Erwin Schrodinger", "Paul Dirac", "Enrico Fermi", "Lise Meitner"
        ],
        "question": "What were the main contributions of this person?"
    },
    {
        "name": "concepts",
        "topics": [
            "Democracy", "Capitalism", "Philosophy", "Psychology",
            "Sociology", "Economics", "Linguistics", "Anthropology",
            "Ethics", "Logic", "Epistemology", "Metaphysics",
            "Political science", "Cognitive science", "Behaviorism",
            "Existentialism", "Utilitarianism", "Stoicism", "Empiricism", "Rationalism"
        ],
        "question": "What is the main idea or argument explained in this article?"
    },
]


def get_wikipedia_text(title: str, wiki: wikipediaapi.Wikipedia) -> str | None:
    """Fetch a Wikipedia article and return its text."""
    page = wiki.page(title)
    if not page.exists():
        print(f"  [skip] {title} — page not found")
        return None
    text = page.text
    if len(text.split()) < 300:
        print(f"  [skip] {title} — too short ({len(text.split())} words)")
        return None
    return text


def run_benchmark():
    wiki = wikipediaapi.Wikipedia(
        language='en',
        user_agent='TokenLens-Benchmark/1.0 (lavanyaashri@github)'
    )

    results = []
    total = 0
    errors = 0

    print("TokenLens Benchmark — 100 Wikipedia Articles")
    print("=" * 50)

    for category in CATEGORIES:
        print(f"\nCategory: {category['name']} ({len(category['topics'])} articles)")
        question = category["question"]
        completed = 0

        for topic in category["topics"]:
            if completed >= ARTICLES_PER_CATEGORY:
                break

            print(f"  Processing: {topic}...")

            # Fetch article
            text = get_wikipedia_text(topic, wiki)
            if text is None:
                errors += 1
                continue

            # Truncate to first 3000 words to keep it manageable
            words = text.split()[:3000]
            text = " ".join(words)
            orig_tokens = len(text) // 4

            # Run tradeoff curve
            article_results = []
            success = True

            for ratio in RATIOS:
                try:
                    compressed = extractive_compress(
                        text,
                        query=question,
                        compression_ratio=ratio,
                    )

                    eval_result = run_full_eval(
                        original_text=text,
                        compressed_text=compressed["compressed_text"],
                        question=question,
                        model=QA_MODEL,
                    )

                    article_results.append({
                        "category": category["name"],
                        "topic": topic,
                        "question": question,
                        "original_tokens": orig_tokens,
                        "compression_ratio": ratio,
                        "compression_pct": compressed["stats"]["compression_pct"],
                        "compressed_tokens": compressed["stats"]["compressed_tokens"],
                        "tokens_saved": compressed["stats"]["tokens_saved"],
                        "semantic_similarity": round(eval_result["semantic_similarity"], 4),
                        "rouge_l": round(eval_result["rouge_l"], 4),
                        "combined_score": round(eval_result["combined_score"], 4),
                    })

                except Exception as e:
                    print(f"    [error] ratio {ratio}: {e}")
                    success = False
                    break

            if success and article_results:
                results.extend(article_results)
                completed += 1
                total += 1
                avg_sem = sum(r["semantic_similarity"] for r in article_results) / len(article_results)
                print(f"    Done. Avg semantic similarity: {avg_sem:.1%}")

                # Save after every article so progress isn't lost
                save_results(results)

            # Small delay to not hammer Ollama
            time.sleep(1)

    print(f"\nBenchmark complete!")
    print(f"Articles processed: {total}")
    print(f"Errors: {errors}")
    print(f"Total rows: {len(results)}")
    print(f"Saved to: {OUTPUT_FILE}")

    # Print summary by category
    print("\nSummary by category:")
    print("-" * 50)
    for category in CATEGORIES:
        cat_results = [r for r in results if r["category"] == category["name"]]
        if not cat_results:
            continue
        avg_sem = sum(r["semantic_similarity"] for r in cat_results) / len(cat_results)
        avg_comp = sum(r["compression_pct"] for r in cat_results) / len(cat_results)
        avg_rouge = sum(r["rouge_l"] for r in cat_results) / len(cat_results)
        print(f"{category['name']:20} avg compression: {avg_comp:.1f}%  avg semantic: {avg_sem:.1%}  avg rouge: {avg_rouge:.1%}")


def save_results(results: list):
    """Save results to CSV."""
    if not results:
        return
    fieldnames = results[0].keys()
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    run_benchmark()