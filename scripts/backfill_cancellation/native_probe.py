"""Explicitly-run local probe. No patches, services, credentials, or production calls.

Usage: python probe.py OUTPUT_DIRECTORY
"""

import argparse
import hashlib
import importlib.metadata
import json
import logging
import os
import platform
import signal
import subprocess
import sys
import time
import traceback
from pathlib import Path

import dagster as dg
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.execution.backfill import PartitionBackfill
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.storage.tags import BACKFILL_ID_TAG, WILL_RETRY_TAG
from dagster._core.test_utils import create_test_daemon_workspace_context
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._core.workspace.load_target import PythonFileTarget
from dagster._daemon.auto_run_reexecution.event_log_consumer import EventLogConsumerDaemon
from dagster._daemon.backfill import execute_backfill_iteration
from dagster._serdes import serialize_value
from dagster_graphql.schema import create_schema
from pydantic import BaseModel, Field


class Worker(BaseModel):
    run_id: str = Field(min_length=1)
    pid: int = Field(gt=0)
    partition: str = Field(min_length=1)


def process_table() -> dict[int, tuple[int, str]]:
    result = subprocess.run(
        ["ps", "-axo", "pid=,ppid=,command="], check=True, capture_output=True, text=True
    )
    table = {}
    for line in result.stdout.splitlines():
        parts = line.strip().split(maxsplit=2)
        if len(parts) == 3:
            table[int(parts[0])] = (int(parts[1]), parts[2])
    return table


def capture_descendants(owned: dict[int, str]) -> None:
    table = process_table()
    parents = {os.getpid()}
    while True:
        children = {pid for pid, (ppid, _) in table.items() if ppid in parents}
        if children <= parents:
            break
        parents |= children
    for pid in parents - {os.getpid()}:
        if pid in table and not table[pid][1].startswith("ps "):
            owned[pid] = table[pid][1]


def wait_until(predicate, description: str, owned: dict[int, str], timeout: float = 45) -> None:
    deadline = time.monotonic() + timeout
    while True:
        capture_descendants(owned)
        if predicate():
            return
        if time.monotonic() >= deadline:
            raise TimeoutError(description)
        time.sleep(0.05)


def graphql(workspace: IWorkspaceProcessContext, query: str, variables: dict) -> dict:
    result = create_schema().execute(
        query, variable_values=variables, context_value=workspace.create_request_context()
    )
    if result.errors:
        raise RuntimeError(str(result.errors))
    assert result.data is not None
    return result.data


def tick(workspace: IWorkspaceProcessContext) -> None:
    errors = [
        value
        for value in execute_backfill_iteration(workspace, logging.getLogger("probe"))
        if value
    ]
    assert not errors, errors


def backfill_status(workspace: IWorkspaceProcessContext, backfill_id: str) -> str:
    backfill = workspace.instance.get_backfill(backfill_id)
    assert backfill is not None
    return backfill.status.value


def run_summary(run: DagsterRun) -> dict:
    return {
        "run_id": run.run_id,
        "status": run.status.value,
        "parent_run_id": run.parent_run_id,
        "root_run_id": run.root_run_id,
        "tags": dict(run.tags),
    }


def snapshot(workspace: IWorkspaceProcessContext, backfill_id: str) -> dict:
    runs = list(workspace.instance.get_runs())
    return {
        "backfill_status": backfill_status(workspace, backfill_id),
        "all_runs": [run_summary(run) for run in runs],
        "backfill_tagged_run_ids": [
            run.run_id for run in runs if run.tags.get(BACKFILL_ID_TAG) == backfill_id
        ],
    }


def terminate(workspace: IWorkspaceProcessContext, run_id: str) -> dict:
    return graphql(
        workspace,
        """mutation Stop($id: String!) {
          terminateRun(runId: $id, terminatePolicy: SAFE_TERMINATE) {
            __typename
            ... on TerminateRunSuccess { run { runId status } }
            ... on TerminateRunFailure { message }
            ... on PythonError { message }
          }
        }""",
        {"id": run_id},
    )


def provenance() -> dict:
    modules = [
        "dagster._daemon.auto_run_reexecution.auto_run_reexecution",
        "dagster._daemon.auto_run_reexecution.event_log_consumer",
        "dagster._core.instance.runs.run_domain",
        "dagster._core.execution.asset_backfill",
        "dagster_graphql.implementation.execution.backfill",
    ]
    source = {}
    for name in modules:
        module = importlib.import_module(name)
        path = Path(module.__file__)
        source[name] = {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "packages": {
            dist.metadata["Name"]: dist.version for dist in importlib.metadata.distributions()
        },
        "source": source,
    }


def main(
    root: Path,
    expect_contained: bool,
    allow_unproven_default_launcher: bool,
    enable_stop_protocol: bool,
) -> int:
    protocol_tags = {}
    if enable_stop_protocol:
        from dagster._core.storage.tags import BACKFILL_STOP_PROTOCOL_VERSION

        protocol_tags = {"dagster/backfill_stop_protocol": BACKFILL_STOP_PROTOCOL_VERSION}
    root.mkdir(parents=True, exist_ok=False)
    os.environ["DAGSTER_CANCEL_PROBE_DIR"] = str(root)
    result = {
        "started_at": time.time(),
        "provenance": provenance(),
        "snapshots": {},
        "expect_contained": expect_contained,
        "allow_unproven_default_launcher": allow_unproven_default_launcher,
        "enable_stop_protocol": enable_stop_protocol,
    }
    owned: dict[int, str] = {}
    exit_code = 0
    try:
        target = PythonFileTarget(
            str(Path(__file__).with_name("fixture.py")),
            "defs",
            str(Path(__file__).parent),
            "stock_probe",
        )
        (root / "instance").mkdir()
        with dg.instance_for_test(
            temp_dir=str(root / "instance"),
            synchronous_run_coordinator=True,
            overrides={
                "run_retries": {
                    "enabled": True,
                    "max_retries": 1,
                    "retry_on_asset_or_op_failure": True,
                }
            },
        ) as instance:
            with create_test_daemon_workspace_context(target, instance) as workspace:
                try:
                    consumer = EventLogConsumerDaemon()
                    assert all(value is None for value in consumer.run_iteration(workspace))
                    graph = workspace.create_request_context().asset_graph
                    with partition_loading_context(dynamic_partitions_store=instance):
                        backfill = PartitionBackfill.from_asset_partitions(
                            backfill_id="stock_cancel_probe",
                            asset_graph=graph,
                            partition_names=["one"],
                            asset_selection=[dg.AssetKey("cancellation_probe")],
                            backfill_timestamp=time.time(),
                            tags=protocol_tags,
                            dynamic_partitions_store=instance,
                            all_partitions=False,
                            title=None,
                            description=None,
                            run_config=None,
                        )
                    instance.add_backfill(backfill)
                    tick(workspace)
                    wait_until(
                        (root / "parent-worker.json").exists,
                        "Parent never entered asset",
                        owned,
                    )
                    parent_worker = Worker.model_validate_json(
                        (root / "parent-worker.json").read_text(encoding="utf-8")
                    )
                    wait_until(
                        lambda: instance.get_run_by_id(parent_worker.run_id).is_finished,
                        "Parent did not finish",
                        owned,
                    )
                    wait_until(
                        lambda: parent_worker.pid not in process_table(),
                        "Parent worker did not exit",
                        owned,
                    )
                    parent = instance.get_run_by_id(parent_worker.run_id)
                    assert parent.status is dg.DagsterRunStatus.FAILURE
                    assert parent.tags.get(WILL_RETRY_TAG) == "true", parent.tags
                    result["parent_worker"] = parent_worker.model_dump()
                    result["snapshots"]["parent_failed_worker_exited"] = snapshot(
                        workspace, backfill.backfill_id
                    )
                    result["cancel_mutation"] = graphql(
                        workspace,
                        """mutation Cancel($id: String!) {
                      cancelPartitionBackfill(backfillId: $id) {
                        __typename ... on CancelBackfillSuccess { backfillId }
                        ... on PythonError { message }
                      }
                    }""",
                        {"id": backfill.backfill_id},
                    )
                    assert backfill_status(workspace, backfill.backfill_id) == "CANCELING"
                    result["snapshots"]["cancel_requested"] = snapshot(
                        workspace, backfill.backfill_id
                    )
                    assert all(value is None for value in consumer.run_iteration(workspace))
                    if expect_contained:
                        result["snapshots"]["consumer_while_canceling"] = snapshot(
                            workspace, backfill.backfill_id
                        )
                        assert len(instance.get_runs()) == 1, (
                            "Retry escaped cancellation: see result.json"
                        )
                        tick(workspace)
                        result["snapshots"]["after_cancellation_tick"] = snapshot(
                            workspace, backfill.backfill_id
                        )
                        status_after_tick = backfill_status(workspace, backfill.backfill_id)
                        if allow_unproven_default_launcher:
                            assert type(instance.run_launcher).__name__ == "DefaultRunLauncher"
                            assert status_after_tick in {"CANCELED", "CANCELING"}
                        else:
                            assert status_after_tick == "CANCELED"
                        result["aggregate_terminal"] = status_after_tick == "CANCELED"
                        result["unproven_default_launcher"] = status_after_tick == "CANCELING"
                        for _ in range(2):
                            assert all(value is None for value in consumer.run_iteration(workspace))
                        result["snapshots"]["consumer_after_backfill_tick"] = snapshot(
                            workspace, backfill.backfill_id
                        )
                        assert len(instance.get_runs()) == 1
                        result["contained"] = True
                        result["reproduced"] = False
                        return 0
                    wait_until(
                        (root / "retry-worker.json").exists,
                        "Consumer did not launch retry",
                        owned,
                    )
                    retry_worker = Worker.model_validate_json(
                        (root / "retry-worker.json").read_text(encoding="utf-8")
                    )
                    retry = instance.get_run_by_id(retry_worker.run_id)
                    assert retry.status is dg.DagsterRunStatus.STARTED
                    assert retry.parent_run_id == parent.run_id
                    assert retry.root_run_id == parent.run_id
                    result["retry_worker"] = retry_worker.model_dump()
                    result["snapshots"]["retry_started_while_canceling"] = snapshot(
                        workspace, backfill.backfill_id
                    )
                    tick(workspace)
                    result["snapshots"]["after_cancellation_tick"] = snapshot(
                        workspace, backfill.backfill_id
                    )
                    result["run_group_query"] = graphql(
                        workspace,
                        """query Group($id: ID!) {
                      runGroupOrError(runId: $id) {
                        __typename
                        ... on RunGroup { rootRunId runs { runId status parentRunId rootRunId tags { key value } } }
                        ... on PythonError { message }
                      }
                    }""",
                        {"id": parent.run_id},
                    )
                    result["reproduced"] = (
                        backfill_status(workspace, backfill.backfill_id) == "CANCELED"
                        and instance.get_run_by_id(retry.run_id).status
                        is dg.DagsterRunStatus.STARTED
                        and BACKFILL_ID_TAG not in retry.tags
                    )
                    result["safe_terminate_mutation"] = terminate(workspace, retry.run_id)
                    wait_until(
                        lambda: instance.get_run_by_id(retry.run_id).is_finished,
                        "Retry did not reach terminal status",
                        owned,
                    )
                    wait_until(
                        lambda: retry_worker.pid not in process_table(),
                        "Retry worker did not exit",
                        owned,
                    )
                    result["snapshots"]["safe_terminate_verified"] = snapshot(
                        workspace, backfill.backfill_id
                    )
                    assert not [run for run in instance.get_runs() if not run.is_finished]
                    assert result["reproduced"], "Hypothesis not reproduced: see result.json"
                finally:
                    for run in instance.get_runs():
                        if not run.is_finished:
                            result.setdefault("emergency_termination", []).append(
                                terminate(workspace, run.run_id)
                            )
                    (root / "release-retry").touch()
                    wait_until(
                        lambda: all(run.is_finished for run in instance.get_runs()),
                        "Cleanup left active runs",
                        owned,
                    )
                    with (root / "native-events.jsonl").open("w", encoding="utf-8") as events:
                        for run in instance.get_runs():
                            for entry in instance.all_logs(run.run_id):
                                events.write(serialize_value(entry) + "\n")
                    result["final_runs"] = [run_summary(run) for run in instance.get_runs()]
    except Exception:
        result["error"] = traceback.format_exc()
        traceback.print_exc()
        exit_code = 1
    finally:
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            table = process_table()
            remaining = {
                pid: command
                for pid, command in owned.items()
                if pid in table and table[pid][1] == command
            }
            if not remaining:
                break
            time.sleep(0.1)
        result["process_cleanup"] = {
            "recorded_descendants": owned,
            "remaining_before_fallback": remaining,
            "fallback_signals": [],
        }
        for pid in remaining:
            if pid in process_table() and process_table()[pid][1] == owned[pid]:
                os.kill(pid, signal.SIGTERM)
                result["process_cleanup"]["fallback_signals"].append(
                    {"pid": pid, "signal": "SIGTERM"}
                )
        if remaining:
            time.sleep(1)
        table = process_table()
        for pid in remaining:
            if pid in table and table[pid][1] == owned[pid]:
                os.kill(pid, signal.SIGKILL)
                result["process_cleanup"]["fallback_signals"].append(
                    {"pid": pid, "signal": "SIGKILL"}
                )
        table = process_table()
        result["process_cleanup"]["remaining_after_cleanup"] = {
            pid: command
            for pid, command in owned.items()
            if pid in table and table[pid][1] == command
        }
        result["finished_at"] = time.time()
        result["elapsed_seconds"] = result["finished_at"] - result["started_at"]
        (root / "result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    "reproduced": result.get("reproduced", False),
                    "contained": result.get("contained", False),
                    "elapsed_seconds": result["elapsed_seconds"],
                    "result": str(root / "result.json"),
                    "remaining_processes": result["process_cleanup"]["remaining_after_cleanup"],
                }
            ),
            flush=True,
        )
    return exit_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--expect-contained", action="store_true")
    parser.add_argument("--allow-unproven-default-launcher", action="store_true")
    parser.add_argument("--enable-stop-protocol", action="store_true")
    args = parser.parse_args()
    if args.allow_unproven_default_launcher and not args.expect_contained:
        parser.error("--allow-unproven-default-launcher requires --expect-contained")
    raise SystemExit(
        main(
            args.output_directory.resolve(),
            args.expect_contained,
            args.allow_unproven_default_launcher,
            args.enable_stop_protocol,
        )
    )
