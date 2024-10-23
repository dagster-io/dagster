## Many dags example

This is used to time various airlift components.

## Installation

From the Dagster directory

```bash
cd experimental/dagster-airlift/examples/perf-harness
pip install uv
uv pip install -e .
```

Sanity check run

```bash
perf-harness 1 1
```

Then check `experimental/dagster-airlift/examples/perf-harness/perf_harness/shared`. You should see a file
`1_dags_1_tasks_perf_output.txt` with airlift timings.

The first argument to `perf-harness` is the number of dags, the second is the number of tasks.
