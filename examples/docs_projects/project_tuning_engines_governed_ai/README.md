## Dagster × Tuning Engines governed AI

This example shows a Dagster asset that calls the Tuning Engines
OpenAI-compatible endpoint. Dagster owns asset orchestration, materializations,
jobs, schedules, and lineage. Tuning Engines owns model routing, policy checks,
approvals, usage attribution, and gateway traces.

## Getting started

```bash
export TE_INFERENCE_KEY=sk-te-your-inference-key
export TE_MODEL=auto
uv sync
dg dev
```

Open Dagster, materialize the `governed_ai_summary` asset, and correlate the
Dagster run with the Tuning Engines `run_id` emitted in the asset metadata.
