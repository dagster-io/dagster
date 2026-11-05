"""One failing partition; its automatic retry waits for native termination."""

import json
import os
import time
from pathlib import Path

import dagster as dg


@dg.asset(partitions_def=dg.StaticPartitionsDefinition(["one"]))
def cancellation_probe(context: dg.AssetExecutionContext) -> None:
    root = Path(os.environ["DAGSTER_CANCEL_PROBE_DIR"])
    retry = context.run.tags.get("dagster/retry_number") is not None
    marker = root / ("retry-worker.json" if retry else "parent-worker.json")
    marker.write_text(
        json.dumps(
            {"run_id": context.run_id, "pid": os.getpid(), "partition": context.partition_key}
        ),
        encoding="utf-8",
    )
    if not retry:
        raise dg.Failure("Intentional first-run failure", allow_retries=False)
    deadline = time.monotonic() + 90
    while not (root / "release-retry").exists():
        if time.monotonic() >= deadline:
            raise TimeoutError("Probe did not terminate the retry within 90 seconds")
        time.sleep(0.05)


defs = dg.Definitions(assets=[cancellation_probe], executor=dg.in_process_executor)
