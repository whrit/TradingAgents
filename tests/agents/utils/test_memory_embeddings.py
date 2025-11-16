from types import SimpleNamespace

import pytest

from tradingagents.agents.utils import memory
from tradingagents.agents.utils.memory import FinancialSituationMemory


class DummyEmbeddingsAPI:
    def __init__(self):
        self.calls = []

    def create(self, model, input):
        self.calls.append((model, input))
        return SimpleNamespace(data=[SimpleNamespace(embedding=[1.0, 2.0])])


class DummyOpenAI:
    def __init__(self, base_url):
        self.base_url = base_url
        self.embeddings = DummyEmbeddingsAPI()


class DummyVoyageClient:
    def __init__(self):
        self.calls = []

    def embed(self, texts, model, input_type=None, output_dimension=None):
        self.calls.append((texts, model, input_type, output_dimension))
        return SimpleNamespace(embeddings=[[0.5, 0.6, 0.7]])


def test_memory_uses_openai_embeddings(monkeypatch):
    monkeypatch.setattr(memory, "OpenAI", DummyOpenAI)

    mem = FinancialSituationMemory(
        "test-memory-openai",
        {"backend_url": "https://api.openai.com/v1"},
    )

    vec = mem.get_embedding("hello world")

    assert vec == [1.0, 2.0]
    assert mem.embedding_provider == "openai"
    assert mem.embedding_model == "text-embedding-3-small"
    assert mem.client.embeddings.calls == [("text-embedding-3-small", "hello world")]


def test_memory_supports_voyage_embeddings(monkeypatch):
    monkeypatch.setattr(memory, "OpenAI", DummyOpenAI)
    monkeypatch.setattr(memory, "voyageai", SimpleNamespace(Client=DummyVoyageClient))

    mem = FinancialSituationMemory(
        "test-memory-voyage",
        {
            "backend_url": "https://api.openai.com/v1",
            "embedding_provider": "voyage",
            "embedding_model": "voyage-3.5",
        },
    )

    vec = mem.get_embedding("market outlook")

    assert vec == [0.5, 0.6, 0.7]
    assert mem.embedding_provider == "voyage"
    assert mem.embedding_model == "voyage-3.5"
    assert mem.voyage_client.calls == [
        (["market outlook"], "voyage-3.5", None, 1024)
    ]


def test_memory_voyage_custom_dimension(monkeypatch):
    monkeypatch.setattr(memory, "OpenAI", DummyOpenAI)
    monkeypatch.setattr(memory, "voyageai", SimpleNamespace(Client=DummyVoyageClient))

    mem = FinancialSituationMemory(
        "test-memory-voyage-512",
        {
            "backend_url": "https://api.openai.com/v1",
            "embedding_provider": "voyage",
            "embedding_model": "voyage-3.5-lite",
            "embedding_output_dimension": 512,
        },
    )

    vec = mem.get_embedding("macro outlook")
    assert vec == [0.5, 0.6, 0.7]
    assert mem.voyage_client.calls == [
        (["macro outlook"], "voyage-3.5-lite", None, 512)
    ]


def test_memory_voyage_invalid_dimension(monkeypatch):
    monkeypatch.setattr(memory, "OpenAI", DummyOpenAI)
    monkeypatch.setattr(memory, "voyageai", SimpleNamespace(Client=DummyVoyageClient))

    with pytest.raises(ValueError):
        FinancialSituationMemory(
            "test-memory-voyage-invalid",
            {
                "backend_url": "https://api.openai.com/v1",
                "embedding_provider": "voyage",
                "embedding_model": "voyage-finance-2",
                "embedding_output_dimension": 512,
            },
        )


def test_memory_truncates_long_text(monkeypatch):
    monkeypatch.setattr(memory, "OpenAI", DummyOpenAI)

    mem = FinancialSituationMemory(
        "test-memory-truncate",
        {
            "backend_url": "https://api.openai.com/v1",
            "embedding_max_tokens": 5,
        },
    )
    mem._token_encoder = None  # force fallback path

    long_text = "market commentary " * 50
    mem.get_embedding(long_text)

    _, captured_input = mem.client.embeddings.calls[0]
    assert len(captured_input) <= 5 * 4
    assert len(captured_input) < len(long_text)
