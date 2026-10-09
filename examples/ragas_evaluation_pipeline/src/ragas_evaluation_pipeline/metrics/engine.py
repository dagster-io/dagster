"""Scoring engine dispatch: deterministic (default) vs ragas (opt-in).

Selects the scoring backend behind the metric assets via a ``scorer`` flag:
  - ``"deterministic"`` — pure-Python offline scorers in :mod:`.scorers`.
    No API key, no network; CI-safe and reproducible (the default).
  - ``"ragas"`` — real ``ragas.evaluate()`` + an LLM judge. Opt-in; needs a key.

The asset graph, checks, regression, and metadata are identical for both modes —
only the engine behind the metric assets changes. This module is the single
place RAGAS "steps in": flip ``mode`` to ``"ragas"`` and the exact same pipeline
runs real RAGAS, with everything downstream unchanged.
"""

from __future__ import annotations

import os

from ragas_evaluation_pipeline.metrics import scorers

DETERMINISTIC = "deterministic"
RAGAS = "ragas"

# --- Groq (OpenAI-compatible) config for scorer="ragas" -------------------
# Groq exposes an OpenAI-compatible endpoint, so RAGAS's OpenAI client works by
# pointing base_url at Groq and reading the key from GROQ_API_KEY. Groq has no
# embeddings endpoint, so only the LLM-only metric (faithfulness) runs through
# real RAGAS here; answer_relevancy/answer_correctness stay deterministic.
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_API_KEY_ENV = "GROQ_API_KEY"
GROQ_MODEL_ENV = "RAGAS_LLM_MODEL"
GROQ_DEFAULT_MODEL = "llama-3.3-70b-versatile"


# --- Public dispatch -------------------------------------------------------
def score_generation(
    mode: str,
    question: str,
    answer: str,
    contexts: list[dict],
    reference: str,
) -> dict:
    """Return generation-side metrics ({faithfulness, answer_relevancy}) in 0..1.

    ``mode="deterministic"`` uses the offline scorers; ``mode="ragas"`` calls
    real RAGAS. Both honor the same 0..1 metric contract.
    """
    if mode == RAGAS:
        scores = _ragas_generation(question, answer, contexts, reference)
    else:
        scores = {
            "faithfulness": scorers.faithfulness_score(answer, contexts),
            "answer_relevancy": scorers.answer_relevancy_score(question, answer),
        }
    # answer_correctness is ALWAYS deterministic — a reference-vs-answer check
    # that closes the "right document, wrong sentence" blind spot regardless of
    # which engine produced faithfulness/relevancy. Its provenance reflects this.
    scores["answer_correctness"] = scorers.answer_correctness_score(answer, reference)
    return scores


def generation_metric_engines(mode: str) -> dict:
    """Per-metric provenance for the generation asset (Risk 2 safeguard).

    In ragas mode only faithfulness (LLM-only) switches to RAGAS via Groq;
    answer_relevancy needs embeddings Groq doesn't provide, so it — like
    answer_correctness — stays deterministic. Surfacing this per metric prevents
    a run-level ``scorer=ragas`` tag from implying that *every* number is RAGAS.
    """
    return {
        "faithfulness": RAGAS if mode == RAGAS else DETERMINISTIC,
        "answer_relevancy": DETERMINISTIC,
        "answer_correctness": DETERMINISTIC,
    }


def retrieval_metric_engines() -> dict:
    """Retrieval metrics are deterministic id-set math in BOTH modes."""
    return {
        "context_precision": DETERMINISTIC,
        "context_recall": DETERMINISTIC,
        "citation_coverage": DETERMINISTIC,
    }


# --- RAGAS backend (opt-in) ------------------------------------------------
def _ragas_generation(
    question: str,
    answer: str,
    contexts: list[dict],
    reference: str,
) -> dict:
    """Real RAGAS generation scoring.

    OPT-IN: requires ``pip install ragas`` (+ its LLM client) and an API key.
    Kept import-local so the default deterministic mode never pays for these
    heavy deps and the package imports cleanly without them installed.
    """
    try:
        from langchain_openai import ChatOpenAI
        from pydantic import SecretStr
        from ragas import EvaluationDataset, SingleTurnSample, evaluate
        from ragas.llms import LangchainLLMWrapper
        from ragas.metrics import faithfulness
    except ImportError as exc:  # pragma: no cover - exercised only in ragas mode
        raise RuntimeError(
            "scorer='ragas' could not import the RAGAS stack "
            f"({type(exc).__name__}: {exc}). "
            "Install the optional extra with: uv sync --extra ragas "
            "and see INSTALLED_PACKAGES.md for the known-good version set "
            "(ragas 0.4.3 needs the langchain 0.3.x generation, not 1.x)."
        ) from exc

    api_key = os.environ.get(GROQ_API_KEY_ENV)
    if not api_key:
        raise RuntimeError(
            f"scorer='ragas' needs a Groq key in ${GROQ_API_KEY_ENV}. "
            f"Set it first, e.g.  $env:{GROQ_API_KEY_ENV} = 'gsk_...'  (PowerShell)."
        )

    # OpenAI-compatible client pointed at Groq; temperature 0 for reproducibility.
    llm = LangchainLLMWrapper(
        ChatOpenAI(
            model=os.environ.get(GROQ_MODEL_ENV, GROQ_DEFAULT_MODEL),
            base_url=GROQ_BASE_URL,
            api_key=SecretStr(api_key),
            temperature=0,
        )
    )

    # ragas 0.4.x schema: user_input / response / retrieved_contexts.
    dataset = EvaluationDataset(
        samples=[
            SingleTurnSample(
                user_input=question,
                response=answer,
                retrieved_contexts=[c["text"] for c in contexts],
            )
        ]
    )
    # Only faithfulness (LLM-only) runs through RAGAS — Groq has no embeddings,
    # so answer_relevancy stays on the deterministic scorer.
    result = evaluate(dataset, metrics=[faithfulness], llm=llm, raise_exceptions=True)
    return {
        "faithfulness": _ragas_mean(result, "faithfulness"),
        "answer_relevancy": scorers.answer_relevancy_score(question, answer),
    }


def _ragas_mean(result, key: str) -> float:
    """Mean of a RAGAS metric across samples as a plain float (NaN -> 0.0).

    Uses the pandas view (stable across ragas 0.4.x); falls back to the raw
    per-sample scores list if pandas is unavailable.
    """
    try:
        series = result.to_pandas()[key].dropna()
        value = float(series.mean()) if len(series) else 0.0
    except Exception:
        vals = [s[key] for s in result.scores if s.get(key) is not None]
        value = sum(vals) / len(vals) if vals else 0.0
    if value != value:  # NaN guard
        value = 0.0
    return round(value, 4)
