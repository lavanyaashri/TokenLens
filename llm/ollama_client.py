"""
ollama_client.py
Handles all communication with the local Ollama server.
"""

import requests

OLLAMA_BASE_URL = "http://localhost:11434"


def generate(prompt: str, model: str = "llama3.2", temperature: float = 0.0) -> str:
    """
    Send a prompt to Ollama and return the response text.
    temperature=0.0 makes outputs deterministic (important for evals).
    """
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": 512,
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()

    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            "Cannot connect to Ollama. Make sure it's running: `ollama serve`"
        )
    except requests.exceptions.Timeout:
        raise TimeoutError("Ollama took too long to respond. Try a smaller model.")
    except Exception as e:
        raise RuntimeError(f"Ollama error: {e}")


def count_tokens(text: str) -> int:
    """
    Rough token count — Ollama uses ~4 chars per token on average.
    """
    return len(text) // 4


def is_ollama_running() -> bool:
    """Check if Ollama server is up."""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def list_models() -> list[str]:
    """Return list of locally available Ollama models."""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        data = r.json()
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []
    
    