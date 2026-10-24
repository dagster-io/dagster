"""Central configuration: file paths, thresholds, and regression tolerance.

Keeping these in one place makes the release-gate policy auditable and easy to
tune in code review.
"""

from __future__ import annotations

from pathlib import Path

# --- Paths -----------------------------------------------------------------
DATA_DIR = Path(__file__).parent / "data"
CORPUS_PATH = DATA_DIR / "corpus.json"
DATASET_PATH = DATA_DIR / "evaluation_dataset.json"
BASELINE_PATH = DATA_DIR / "baseline_metrics.json"
INDEX_VERSION_PATH = DATA_DIR / "index_version.txt"

# --- Retrieval config ------------------------------------------------------
TOP_K = 2

# --- Threshold gates (absolute) -------------------------------------------
# Generation metrics fail for generation reasons (hallucination, off-topic).
FAITHFULNESS_MIN = 0.80
# NOTE: calibrated for the DETERMINISTIC scorer. It measures question-word echo,
# which extractive answers score low on (~0.44 here) even when correct — so the
# floor is set to what offline mode genuinely achieves. Real RAGAS relevancy
# (embedding-based) scores such answers far higher; raise this toward ~0.75 when
# running scorer="ragas".
ANSWER_RELEVANCY_MIN = 0.40
# Reference-based correctness catches the "right document, wrong sentence" case
# that faithfulness (grounding-only) and the id-set retrieval metrics miss.
ANSWER_CORRECTNESS_MIN = 0.60
# Retrieval metrics fail for retrieval reasons (bad search / indexing).
CONTEXT_RECALL_MIN = 0.75
# Citation coverage must not drop below the recorded baseline.
CITATION_COVERAGE_MIN_VS_BASELINE = True

# --- Regression policy -----------------------------------------------------
# Fail if any required metric drops by more than this vs the baseline.
REGRESSION_TOLERANCE = 0.05

# Metrics that participate in the release gate and regression check.
REQUIRED_RETRIEVAL_METRICS = ("context_recall", "citation_coverage")
REQUIRED_GENERATION_METRICS = ("faithfulness", "answer_relevancy", "answer_correctness")
