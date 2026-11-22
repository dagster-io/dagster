"""Deterministic, offline stand-ins for RAGAS metrics.

WHY NOT REAL RAGAS HERE:
  Real RAGAS metrics (faithfulness, answer relevancy, context recall) are
  computed with an LLM judge + embeddings, which require network access and API
  keys. Version 1's hard requirements are "runs locally with no external
  infrastructure" and "deterministic for CI". These pure-Python scorers satisfy
  that while preserving the SAME metric *contract* (a 0..1 score per metric).

  To use real RAGAS instead, replace the bodies of `faithfulness_score`,
  `answer_relevancy_score`, and the retrieval scorers with calls into
  `ragas.evaluate(...)` and keep the asset graph unchanged. The orchestration,
  lineage, checks, and regression logic do not care how the numbers are produced.
"""

from __future__ import annotations

import re

_WORD_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "of",
    "in",
    "on",
    "at",
    "to",
    "and",
    "or",
    "it",
    "its",
    "be",
    "by",
    "as",
    "that",
    "this",
    "with",
    "for",
    "how",
    "where",
    "what",
    "when",
    "who",
    "does",
    "do",
}


def tokenize(text: str) -> list[str]:
    """Lowercase content-word tokens (stopwords removed)."""
    return [w for w in _WORD_RE.findall(text.lower()) if w not in _STOPWORDS]


def _coverage(target: str, source: str) -> float:
    """Fraction of target's content words that appear in source. 1.0 if empty."""
    target_tokens = set(tokenize(target))
    if not target_tokens:
        return 1.0
    source_tokens = set(tokenize(source))
    return len(target_tokens & source_tokens) / len(target_tokens)


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


# --- Retrieval -------------------------------------------------------------
def retrieve(question: str, corpus: list[dict], top_k: int) -> list[dict]:
    """Rank corpus docs by content-word overlap with the question; return top_k.

    Stand-in for an embedding retriever. Stable tie-break by corpus order.
    """
    q_tokens = set(tokenize(question))
    scored = []
    for idx, doc in enumerate(corpus):
        overlap = len(q_tokens & set(tokenize(doc["text"])))
        scored.append((overlap, -idx, doc))
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [doc for _, _, doc in scored[:top_k]]


def context_precision(expected_ids: list[str], retrieved_ids: list[str]) -> float:
    if not retrieved_ids:
        return 0.0
    relevant = sum(1 for cid in retrieved_ids if cid in set(expected_ids))
    return relevant / len(retrieved_ids)


def context_recall(expected_ids: list[str], retrieved_ids: list[str]) -> float:
    if not expected_ids:
        return 1.0
    found = sum(1 for cid in set(expected_ids) if cid in set(retrieved_ids))
    return found / len(set(expected_ids))


def citation_coverage(expected_ids: list[str], cited_ids: list[str]) -> float:
    """Fraction of expected citations actually cited by the generated answer."""
    if not expected_ids:
        return 1.0
    covered = sum(1 for cid in set(expected_ids) if cid in set(cited_ids))
    return covered / len(set(expected_ids))


# --- Generation ------------------------------------------------------------
def generate_answer(reference_answer: str, contexts: list[dict]) -> str:
    """Simulate an extractive generator grounded in retrieved context.

    Picks the context sentence most overlapping the reference; falls back to the
    reference answer when nothing useful was retrieved (low-faithfulness case).
    """
    best_sentence = ""
    best_score = -1.0
    for ctx in contexts:
        for sentence in _split_sentences(ctx["text"]):
            score = _coverage(reference_answer, sentence)
            if score > best_score:
                best_score = score
                best_sentence = sentence
    return best_sentence if best_score > 0 else reference_answer


def faithfulness_score(answer: str, contexts: list[dict]) -> float:
    """How well the answer is grounded in the retrieved context (0..1)."""
    joined = " ".join(c["text"] for c in contexts)
    return round(_coverage(answer, joined), 4)


def answer_relevancy_score(question: str, answer: str) -> float:
    """How well the answer covers the question's key terms (0..1)."""
    return round(_coverage(question, answer), 4)


def answer_correctness_score(answer: str, reference_answer: str) -> float:
    """Token-F1 agreement between the answer and the gold reference (0..1).

    WHY THIS EXISTS: retrieval metrics only check *which document ids* were found,
    and ``faithfulness_score`` only checks that the answer is grounded *somewhere*
    in the retrieved text. Neither catches an answer that quotes the WRONG sentence
    from the RIGHT document — it stays "grounded" but is factually wrong. Comparing
    the answer against the reference answer closes that blind spot.

    F1 (not one-way coverage) so both a too-short and a padded answer are penalized.
    """
    answer_tokens = set(tokenize(answer))
    reference_tokens = set(tokenize(reference_answer))
    if not answer_tokens and not reference_tokens:
        return 1.0
    overlap = len(answer_tokens & reference_tokens)
    if overlap == 0:
        return 0.0
    precision = overlap / len(answer_tokens)
    recall = overlap / len(reference_tokens)
    return round(2 * precision * recall / (precision + recall), 4)
