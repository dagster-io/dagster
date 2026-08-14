"""The 8-asset evaluation graph (Point 2).

Build order (each asset's input already exists by the time it runs):
  1. evaluation_dataset_asset      — questions, reference answers, expected cites
  2. retrieved_contexts_asset      — documents found per question
  3. generated_answers_asset       — what the (simulated) LLM produced
  4. retrieval_metric_results_asset  — retrieval-side scores (id-set math)
  5. generation_metric_results_asset — generation-side scores (deterministic|ragas)
  6. combined_metric_results_asset — merged scores + evidence + metadata
  7. regression_comparison_asset   — current vs previous materialized result
                                      (checked-in baseline only as first-run fallback)
  8. run_summary_asset             — final summary + release decision

Two honesty safeguards are baked in (see the design addenda in
VERSION1A_IMPLEMENTATION_STEPS.md §5):
  - generation includes ``answer_correctness`` (answer vs gold reference) to catch
    "right document, wrong sentence" answers that faithfulness/id-metrics miss.
  - every metric carries a per-metric ``engine`` provenance tag so a run-level
    ``scorer=ragas`` never implies retrieval metrics used RAGAS (they never do).
"""

import hashlib
import json
from datetime import UTC, datetime

from dagster import AssetExecutionContext, MetadataValue, asset

from ragas_evaluation_pipeline.config import CORPUS_PATH, DATASET_PATH, TOP_K
from ragas_evaluation_pipeline.metrics import engine, scorers
from ragas_evaluation_pipeline.resources.runtime_metadata_resource import RuntimeMetadataResource
from ragas_evaluation_pipeline.storage.baseline_store import (
    flatten_metrics,
    load_baseline,
    load_previous_metrics,
)


def _mean(rows: list[dict], keys) -> dict:
    """Mean of each key across per-example rows (rounded)."""
    n = len(rows) or 1
    return {k: round(sum(r[k] for r in rows) / n, 4) for k in keys}


# --- #1 dataset -----------------------------------------------------------
@asset
def evaluation_dataset_asset(context: AssetExecutionContext) -> dict:
    """Load the checked-in questions + gold answers + expected citations."""
    data = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    corpus_hash = hashlib.sha256(CORPUS_PATH.read_bytes()).hexdigest()[:12]
    data["_corpus_hash"] = corpus_hash
    context.add_output_metadata(
        {
            "dataset_id": data["dataset_id"],
            "dataset_semver": data["dataset_semver"],
            "corpus_hash": corpus_hash,
            "num_examples": len(data["examples"]),
        }
    )
    return data


# --- #2 retrieved contexts ------------------------------------------------
@asset
def retrieved_contexts_asset(evaluation_dataset_asset: dict) -> list[dict]:
    """Rank corpus docs per question (offline stand-in for a retriever)."""
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    out = []
    for ex in evaluation_dataset_asset["examples"]:
        docs = scorers.retrieve(ex["question"], corpus, TOP_K)
        out.append(
            {
                "question_id": ex["question_id"],
                "retrieved_context_ids": [d["id"] for d in docs],
                "contexts": docs,
            }
        )
    return out


# --- #3 generated answers -------------------------------------------------
@asset
def generated_answers_asset(
    evaluation_dataset_asset: dict, retrieved_contexts_asset: list[dict]
) -> list[dict]:
    """Simulate a grounded extractive generator over the retrieved contexts."""
    by_qid = {r["question_id"]: r for r in retrieved_contexts_asset}
    out = []
    for ex in evaluation_dataset_asset["examples"]:
        r = by_qid[ex["question_id"]]
        answer = scorers.generate_answer(ex["reference_answer"], r["contexts"])
        out.append(
            {
                "question_id": ex["question_id"],
                "generated_answer": answer,
                "cited_context_ids": r["retrieved_context_ids"][:1],
            }
        )
    return out


# --- #4 retrieval metrics (always deterministic id-set math) --------------
@asset
def retrieval_metric_results_asset(
    context: AssetExecutionContext,
    evaluation_dataset_asset: dict,
    retrieved_contexts_asset: list[dict],
    generated_answers_asset: list[dict],
) -> dict:
    by_ctx = {r["question_id"]: r for r in retrieved_contexts_asset}
    by_ans = {a["question_id"]: a for a in generated_answers_asset}
    rows = []
    for ex in evaluation_dataset_asset["examples"]:
        qid, expected = ex["question_id"], ex["expected_citation_ids"]
        retrieved_ids = by_ctx[qid]["retrieved_context_ids"]
        rows.append(
            {
                "question_id": qid,
                "context_precision": scorers.context_precision(expected, retrieved_ids),
                "context_recall": scorers.context_recall(expected, retrieved_ids),
                "citation_coverage": scorers.citation_coverage(
                    expected, by_ans[qid]["cited_context_ids"]
                ),
            }
        )
    metric_keys = ["context_precision", "context_recall", "citation_coverage"]
    result = {"per_example": rows, "aggregate": _mean(rows, metric_keys)}
    context.add_output_metadata(
        {
            "aggregate": MetadataValue.json(result["aggregate"]),
            "metric_engines": MetadataValue.json(engine.retrieval_metric_engines()),
            "per_example": MetadataValue.json(rows),
        }
    )
    return result


# --- #5 generation metrics (deterministic | ragas, flag-controlled) -------
@asset
def generation_metric_results_asset(
    context: AssetExecutionContext,
    evaluation_dataset_asset: dict,
    retrieved_contexts_asset: list[dict],
    generated_answers_asset: list[dict],
    runtime_metadata: RuntimeMetadataResource,
) -> dict:
    by_ctx = {r["question_id"]: r for r in retrieved_contexts_asset}
    by_ans = {a["question_id"]: a for a in generated_answers_asset}
    rows = []
    for ex in evaluation_dataset_asset["examples"]:
        qid = ex["question_id"]
        scores = engine.score_generation(
            runtime_metadata.scorer,
            ex["question"],
            by_ans[qid]["generated_answer"],
            by_ctx[qid]["contexts"],
            ex["reference_answer"],
        )
        rows.append({"question_id": qid, **scores})
    metric_keys = ["faithfulness", "answer_relevancy", "answer_correctness"]
    result = {"per_example": rows, "aggregate": _mean(rows, metric_keys)}
    context.add_output_metadata(
        {
            "aggregate": MetadataValue.json(result["aggregate"]),
            "metric_engines": MetadataValue.json(
                engine.generation_metric_engines(runtime_metadata.scorer)
            ),
            "per_example": MetadataValue.json(rows),
        }
    )
    return result


# --- #6 combined ----------------------------------------------------------
@asset
def combined_metric_results_asset(
    context: AssetExecutionContext,
    evaluation_dataset_asset: dict,
    retrieval_metric_results_asset: dict,
    generation_metric_results_asset: dict,
    runtime_metadata: RuntimeMetadataResource,
) -> dict:
    combined = {
        "retrieval": retrieval_metric_results_asset["aggregate"],
        "generation": generation_metric_results_asset["aggregate"],
    }
    # Merge run-level lineage tags with per-metric provenance so the dashboard is
    # self-explaining about which engine produced each number.
    metric_engines = {
        **engine.retrieval_metric_engines(),
        **engine.generation_metric_engines(runtime_metadata.scorer),
    }
    context.add_output_metadata(
        {
            **runtime_metadata.as_tags(),
            "corpus_hash": evaluation_dataset_asset["_corpus_hash"],
            "dataset_id": evaluation_dataset_asset["dataset_id"],
            "dataset_semver": evaluation_dataset_asset["dataset_semver"],
            "retrieval": MetadataValue.json(combined["retrieval"]),
            "generation": MetadataValue.json(combined["generation"]),
            "metric_engines": MetadataValue.json(metric_engines),
        }
    )
    return combined


# --- #7 regression --------------------------------------------------------
@asset
def regression_comparison_asset(
    context: AssetExecutionContext,
    combined_metric_results_asset: dict,
    runtime_metadata: RuntimeMetadataResource,
) -> dict:
    """Diff the current run against the PREVIOUS materialized evaluation result.

    Primary path: read the last ``combined_metric_results_asset`` materialization
    from the instance event log (a true run-over-run comparison with lineage).
    Fallback: the checked-in baseline file, used only when the instance has no
    prior materialization (first run / fresh CI checkout). The chosen source is
    recorded in ``baseline_source`` so the comparison is self-explaining.
    """
    # Extract evaluation identity (actual stored values) to ensure regression baseline
    # has compatible config. Get the tags that were just stored by combined_metric_results.
    stored_tags = runtime_metadata.as_tags()
    evaluation_identity = {
        "scorer": stored_tags["scorer"],
        "model_name": stored_tags["model_name"],
        "embedding_model": stored_tags["embedding_model"],
        "prompt_version": stored_tags["prompt_version"],
        "index_version": stored_tags["index_version"],
    }
    previous = load_previous_metrics(
        context.instance, context.run.run_id, evaluation_identity=evaluation_identity
    )
    if previous is not None:
        baseline_source = "previous_materialization"
        baseline = previous
    else:
        baseline_source = "checked_in_baseline"
        baseline = load_baseline()

    base = flatten_metrics(baseline)
    curr = flatten_metrics(combined_metric_results_asset)
    deltas = {m: round(curr[m] - base.get(m, 0.0), 4) for m in curr}
    result = {
        "baseline_source": baseline_source,
        "baseline_run_id": baseline.get("baseline_run_id"),
        "deltas": deltas,
        "current": curr,
        "baseline": base,
    }
    context.add_output_metadata(
        {
            "baseline_source": baseline_source,
            "baseline_run_id": str(baseline.get("baseline_run_id")),
            "deltas": MetadataValue.json(deltas),
            "worst_delta": min(deltas.values(), default=0.0),
        }
    )
    return result


# --- #8 run summary + release decision ------------------------------------
@asset
def run_summary_asset(
    context: AssetExecutionContext,
    combined_metric_results_asset: dict,
    regression_comparison_asset: dict,
    runtime_metadata: RuntimeMetadataResource,
) -> dict:
    summary = {
        "metrics": combined_metric_results_asset,
        "deltas": regression_comparison_asset["deltas"],
        "baseline_run_id": regression_comparison_asset["baseline_run_id"],
        "metadata": runtime_metadata.as_tags(),
        "evaluation_timestamp": datetime.now(UTC).isoformat(),
    }
    context.add_output_metadata(
        {
            **runtime_metadata.as_tags(),
            "evaluation_timestamp": summary["evaluation_timestamp"],
            "baseline_run_id": str(summary["baseline_run_id"]),
        }
    )
    return summary
