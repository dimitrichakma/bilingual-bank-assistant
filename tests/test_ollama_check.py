"""The startup check gives plain messages. Ollama itself is faked, so no server is needed."""
from types import SimpleNamespace

import pytest

import src.llm as llm


def fake_list(*names):
    return lambda: SimpleNamespace(models=[SimpleNamespace(model=n) for n in names])


def test_passes_when_models_are_installed_and_latest_tag_is_matched(monkeypatch):
    monkeypatch.setattr(llm.ollama, "list", fake_list("qwen3.5:9b-mlx", "bge-m3:latest"))
    llm.check_ollama(["qwen3.5:9b-mlx", "bge-m3"])


def test_says_to_start_ollama_when_it_cannot_be_reached(monkeypatch):
    def down():
        raise ConnectionError("refused")
    monkeypatch.setattr(llm.ollama, "list", down)
    with pytest.raises(llm.OllamaProblem, match="Cannot reach Ollama"):
        llm.check_ollama(["bge-m3"])


def test_says_which_model_to_pull_when_one_is_missing(monkeypatch):
    monkeypatch.setattr(llm.ollama, "list", fake_list("bge-m3:latest"))
    with pytest.raises(llm.OllamaProblem, match="ollama pull qwen3.5:9b-mlx"):
        llm.check_ollama(["qwen3.5:9b-mlx", "bge-m3"])
