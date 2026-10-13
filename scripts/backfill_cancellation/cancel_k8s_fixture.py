"""A real remote step that remains active until Kubernetes termination."""

import os
import time

import dagster as dg
from dagster._core.events import EngineEventData
from dagster_k8s import k8s_job_executor


@dg.asset(partitions_def=dg.StaticPartitionsDefinition(["one"]))
def remote_blocked(context: dg.AssetExecutionContext) -> None:
    context.instance.report_engine_event(
        "REMOTE_STEP_BLOCKING",
        context.run,
        engine_event_data=EngineEventData({"pod": dg.MetadataValue.text(os.environ["HOSTNAME"])}),
    )
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        time.sleep(0.1)
    raise TimeoutError("Cancellation probe did not terminate the remote step")


defs = dg.Definitions(assets=[remote_blocked], executor=k8s_job_executor)
