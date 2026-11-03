from functools import lru_cache

from langchain_ollama import ChatOllama


@lru_cache(maxsize=None)
def get_llm(model: str, think: bool = False, num_predict: int | None = None) -> ChatOllama:
    """One place that builds the local chat model, so every step uses the same settings.
    Temperature 0 keeps replies repeatable. reasoning=False is Ollama's think false."""
    return ChatOllama(model=model, temperature=0, num_predict=num_predict, reasoning=think)
