from functools import lru_cache

import ollama
from langchain_ollama import ChatOllama


@lru_cache(maxsize=None)
def get_llm(model: str, think: bool = False, num_predict: int | None = None) -> ChatOllama:
    """One place that builds the local chat model, so every step uses the same settings.
    Temperature 0 keeps replies repeatable. reasoning=False is Ollama's think false."""
    return ChatOllama(model=model, temperature=0, num_predict=num_predict, reasoning=think)


class OllamaProblem(Exception):
    """Ollama is not running or a needed model is missing. The message is safe to show a user."""


def check_ollama(models: list[str]) -> None:
    """Fail early with a plain message, instead of a long error from deep inside a library."""
    try:
        installed = {m.model for m in ollama.list().models}
    except Exception:
        raise OllamaProblem("Cannot reach Ollama. Open the Ollama app (or run: ollama serve) and try again.")
    for name in models:
        # Ollama lists a model without a tag as name:latest, for example bge-m3:latest.
        if name not in installed and f"{name}:latest" not in installed:
            raise OllamaProblem(f"The model {name} is not installed. Run: ollama pull {name}")
