"""Scoring-engine dispatch + provenance tests (Step 12).

All offline — the ragas backend is only checked via its no-key guard, so the
suite never makes a network call.
"""

import pytest
from ragas_evaluation_pipeline.metrics import engine

_CTX = [{"id": "doc1", "text": "The Eiffel Tower stands 330 meters tall."}]
_ARGS = (
    "How tall is the Eiffel Tower?",
    "The Eiffel Tower stands 330 meters tall.",
    _CTX,
    "The Eiffel Tower stands 330 meters tall.",
)


def test_deterministic_dispatch_returns_all_three_metrics():
    scores = engine.score_generation("deterministic", *_ARGS)
    assert set(scores) == {"faithfulness", "answer_relevancy", "answer_correctness"}
    assert all(0.0 <= v <= 1.0 for v in scores.values())


def test_provenance_deterministic_mode_all_deterministic():
    prov = engine.generation_metric_engines("deterministic")
    assert set(prov.values()) == {"deterministic"}


def test_provenance_ragas_mode_only_faithfulness_is_ragas():
    prov = engine.generation_metric_engines("ragas")
    assert prov["faithfulness"] == "ragas"
    assert prov["answer_relevancy"] == "deterministic"
    assert prov["answer_correctness"] == "deterministic"


def test_retrieval_metrics_always_deterministic():
    assert set(engine.retrieval_metric_engines().values()) == {"deterministic"}


def test_ragas_mode_without_key_raises_clear_error(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match=r"GROQ_API_KEY|could not import the RAGAS stack"):
        engine.score_generation("ragas", *_ARGS)
