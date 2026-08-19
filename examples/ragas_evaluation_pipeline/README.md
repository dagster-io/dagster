# RAG Evaluation Pipeline (Dagster + RAGAS)

This example shows how to evaluate Retrieval-Augmented Generation quality as a
Dagster pipeline artifact, not a one-off notebook script.

The goal is repeatable evaluation with lineage, thresholds, regression tracking,
and release-gate style checks.

## Why this example exists

Most RAG demos focus on building retrieval and generation.
This one focuses on measuring quality over time.

It gives you:

- a materializable asset graph for evaluation
- separate retrieval and generation metrics
- threshold checks and an aggregate release gate
- run-over-run regression comparison
- metadata and provenance for auditability
- local deterministic mode for CI and offline development

## Pipeline graph

```text
                         ┌-> retrieval metrics ───────┐
dataset -> contexts -> answers                          ├-> combined -> regression -> summary
    │          │          │                             │                  │
    └──────────┴──────────┴-> generation metrics ──────┘                  └-> regression check

combined -> threshold checks
combined -> release gate check
```

## What is evaluated

Retrieval-side metrics:

- context_precision
- context_recall
- citation_coverage

Generation-side metrics:

- faithfulness
- answer_relevancy
- answer_correctness

Retrieval and generation stay separate on purpose, because they fail for
different reasons and need different debugging workflows.

## Quick start

Requirements: Python 3.11+

```bash
uv sync --dev
dagster dev -m ragas_evaluation_pipeline.definitions
```

Open http://localhost:3000, materialize all assets, and inspect Asset
Checks to see if the release gate passes.

Run tests:

```bash
pytest -q
```

## Scoring modes

### 1) Deterministic (default)

- no API key
- no network dependency
- stable and CI-friendly

### 2) RAGAS (opt-in)

- uses real `ragas.evaluate()`
- requires Groq API key
- only faithfulness uses RAGAS in this setup
- answer_relevancy and answer_correctness remain deterministic

Enable RAGAS mode:

```bash
uv sync --dev --extra ragas
```

Set environment variables:

```text
RAGAS_SCORER=ragas
GROQ_API_KEY=your_groq_key
```

## Release gate and regression checks

Checks are defined against combined and regression outputs. Thresholds are
centralized in config.

Current checks include:

- faithfulness minimum
- answer relevancy minimum
- answer correctness minimum
- context recall minimum
- citation coverage non-regression
- aggregate release gate
- regression tolerance versus baseline

## Run metadata and provenance

Each run captures metadata such as:

- model name
- embedding model
- index version
- prompt version
- corpus hash
- dataset id/version
- timestamp

Per-metric engine provenance is also recorded so mixed-mode runs are explicit
about which metric came from which engine.

## Automation

- daily schedule to run evaluation automatically
- sensor to re-run when index version changes

## Project layout

```text
src/ragas_evaluation_pipeline/
    assets/
    checks/
    data/
    jobs/
    metrics/
    resources/
    schedules/
    sensors/
    storage/
    config.py
    definitions.py
tests/
```


Note:
- Baseline values in this example were generated with deterministic scoring.
- Real RAGAS values vary by judge model and runtime context.
