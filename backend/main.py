"""
main.py — TokenLens FastAPI Backend
Run with: uvicorn backend.main:app --reload
"""

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import PyPDF2
import io

from compressor.extractive import extractive_compress
from compressor.abstractive import abstractive_compress
from compressor.evaluator import run_full_eval
from llm.ollama_client import is_ollama_running, list_models

app = FastAPI(title="TokenLens API")

# Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend files
import os
if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def root():
    return FileResponse("frontend/index.html")


@app.get("/api/status")
def status():
    """Check if Ollama is running and return available models."""
    running = is_ollama_running()
    models = list_models() if running else []
    return {
        "ollama_running": running,
        "models": models,
    }


@app.post("/api/compress")
async def compress(
    text: str = Form(...),
    question: str = Form(...),
    strategy: str = Form(...),
    compression_ratio: float = Form(0.5),
    chunk_size: int = Form(200),
    overlap: int = Form(30),
    qa_model: str = Form("llama3.2:latest"),
    summarize_model: str = Form("phi3:latest"),
    run_eval: bool = Form(True),
):
    """Main compression endpoint."""
    results = {}

    if strategy in ["extractive", "both"]:
        ext = extractive_compress(
            text,
            query=question or "Summarize the key points",
            compression_ratio=compression_ratio,
            chunk_size=chunk_size,
            overlap=overlap,
        )
        results["extractive"] = ext

    if strategy in ["abstractive", "both"]:
        abs_result = abstractive_compress(
            text,
            model=summarize_model,
            chunk_size=chunk_size,
            overlap=overlap,
        )
        results["abstractive"] = abs_result

    # Run evaluation for each strategy
    if run_eval and question.strip():
        for key in results:
            eval_result = run_full_eval(
                original_text=text,
                compressed_text=results[key]["compressed_text"],
                question=question,
                model=qa_model,
            )
            results[key]["eval"] = eval_result

    return {"results": results}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Extract text from uploaded file."""
    content = await file.read()

    if file.content_type == "application/pdf":
        try:
            pdf = PyPDF2.PdfReader(io.BytesIO(content))
            text = "\n".join(
                page.extract_text() for page in pdf.pages
                if page.extract_text()
            )
            return {"text": text, "words": len(text.split())}
        except Exception as e:
            return {"error": str(e)}
    else:
        text = content.decode("utf-8", errors="ignore")
        return {"text": text, "words": len(text.split())}
    

@app.post("/api/tradeoff")
async def tradeoff_curve(
    text: str = Form(...),
    question: str = Form(...),
    qa_model: str = Form("llama3.2"),
):
    """
    Run extractive compression at every ratio from 0.1 to 0.9
    and return quality scores at each level.
    This generates the quality vs compression tradeoff curve.
    """
    ratios = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    results = []

    for ratio in ratios:
        # Compress at this ratio
        compressed = extractive_compress(
            text,
            query=question,
            compression_ratio=ratio,
        )

        # Evaluate quality
        eval_result = run_full_eval(
            original_text=text,
            compressed_text=compressed["compressed_text"],
            question=question,
            model=qa_model,
        )

        results.append({
            "ratio": ratio,
            "compression_pct": compressed["stats"]["compression_pct"],
            "tokens_saved": compressed["stats"]["tokens_saved"],
            "compressed_tokens": compressed["stats"]["compressed_tokens"],
            "semantic_similarity": eval_result["semantic_similarity"],
            "rouge_l": eval_result["rouge_l"],
            "combined_score": eval_result["combined_score"],
        })

    return {"curve": results}