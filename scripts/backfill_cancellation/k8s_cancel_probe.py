"""Native local-only K8s run and detached step cancellation acceptance."""

import hashlib
import importlib.metadata
import json
import logging
import os
import time
import traceback
from pathlib import Path

import dagster as dg
import dagster_graphql
import dagster_k8s
import kubernetes.client
import kubernetes.config
import requests
import yaml
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.execution.backfill import PartitionBackfill
from dagster._core.storage.tags import BACKFILL_STOP_PROTOCOL_VERSION
from dagster._core.test_utils import create_test_daemon_workspace_context
from dagster._core.workspace.load_target import ModuleTarget
from dagster._daemon.backfill import execute_backfill_iteration
from dagster._serdes import serialize_value
from dagster_graphql.schema import create_schema
from dagster_k8s.backfill_admission import ADMISSION_ID_ANNOTATION, POD_FINALIZER


def run_view(instance: dg.DagsterInstance) -> list[dict]:
    return [
        {
            "run_id": run.run_id,
            "status": run.status.value,
            "tags": dict(run.tags),
            "parent_run_id": run.parent_run_id,
            "root_run_id": run.root_run_id,
        }
        for run in instance.get_runs()
    ]


def instance_config(namespace: str, image: str, webhook_name: str) -> dict:
    return {
        "storage": {"postgres": {"postgres_url": {"env": "DAGSTER_POSTGRES_URL"}}},
        "run_coordinator": {
            "module": "dagster._core.run_coordinator.sync_in_memory_run_coordinator",
            "class": "SyncInMemoryRunCoordinator",
        },
        "run_launcher": {
            "module": "dagster_k8s.launcher",
            "class": "K8sRunLauncher",
            "config": {
                "service_account_name": "dagster-worker",
                "instance_config_map": "dagster-instance",
                "dagster_home": "/opt/dagster/dagster_home",
                "job_image": image,
                "job_namespace": namespace,
                "load_incluster_config": True,
                "image_pull_policy": "Never",
                "env_secrets": ["dagster-probe-env"],
                "backfill_worker_admission_webhook_name": webhook_name,
                "run_k8s_config": {"pod_spec_config": {"termination_grace_period_seconds": 5}},
            },
        },
        "run_retries": {"enabled": True, "max_retries": 1, "retry_on_asset_or_op_failure": True},
        "telemetry": {"enabled": False},
    }


def main() -> int:
    root = Path("/tmp/probe-evidence")
    root.mkdir()
    home = root / "instance"
    home.mkdir()
    namespace = os.environ["PROBE_NAMESPACE"]
    image = os.environ["PROBE_IMAGE"]
    case = os.environ["PROBE_CASE"]
    admission_url = os.environ["PROBE_ADMISSION_URL"]
    webhook_name = os.environ["PROBE_ADMISSION_WEBHOOK_NAME"]

    def admission_request(method: str, path: str) -> dict:
        response = requests.request(method, admission_url + path, verify="/certs/ca.crt", timeout=3)
        response.raise_for_status()
        return response.json() if response.content else {}

    deadline = time.monotonic() + 90
    while True:
        try:
            admission_request("GET", "/healthz")
            break
        except requests.RequestException:
            assert time.monotonic() < deadline, "Admission service did not become ready"
            time.sleep(0.2)
    (home / "dagster.yaml").write_text(
        yaml.safe_dump(instance_config(namespace, image, webhook_name)), encoding="utf-8"
    )
    os.environ["DAGSTER_HOME"] = str(home)
    kubernetes.config.load_incluster_config()
    core = kubernetes.client.CoreV1Api()
    batch = kubernetes.client.BatchV1Api()
    result = {
        "started_at": time.time(),
        "namespace": namespace,
        "image": image,
        "case": case,
        "protocol_version": BACKFILL_STOP_PROTOCOL_VERSION,
        "timeline": [],
    }
    result["package_versions"] = {
        d.metadata["Name"]: d.version for d in importlib.metadata.distributions()
    }
    result["installed_packages"] = {
        module.__name__: {
            "path": module.__file__,
            "sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        }
        for module in (dg, dagster_graphql, dagster_k8s)
    }
    result["fixture_sha256"] = hashlib.sha256(
        Path("cancel_k8s_fixture.py").read_bytes()
    ).hexdigest()
    exit_code = 0
    with dg.DagsterInstance.get() as instance:
        instance.upgrade()
        assert not instance.get_runs()
        with create_test_daemon_workspace_context(
            ModuleTarget("cancel_k8s_fixture", "defs", "/opt/probe", "k8s_probe"), instance
        ) as workspace:

            def inventory(label: str) -> dict:
                jobs = batch.list_namespaced_job(namespace).items
                pods = core.list_namespaced_pod(namespace).items
                data = {
                    "label": label,
                    "observed_at": time.time(),
                    "backfill_status": (
                        instance.get_backfill("k8s-stop-proof").status.value
                        if instance.get_backfill("k8s-stop-proof")
                        else None
                    ),
                    "runs": run_view(instance),
                    "jobs": [object_view(job) for job in jobs],
                    "worker_pods": [
                        object_view(pod)
                        for pod in pods
                        if pod.metadata.name not in (os.environ["HOSTNAME"], "admission")
                    ],
                    "launches": [
                        {
                            "run_id": value.run_id,
                            "worker_id": value.worker_id,
                            "kind": value.kind.value,
                            "state": value.state.value,
                            "target": serialize_value(value.target),
                        }
                        for value in instance.get_backfill_worker_launches("k8s-stop-proof")
                    ],
                }
                result["timeline"].append(data)
                return data

            def object_view(value) -> dict:
                # Job command arguments contain serialized instance references. Retain
                # identity and termination evidence without exporting those arguments.
                serialized = kubernetes.client.ApiClient().sanitize_for_serialization(value)
                metadata = serialized["metadata"]
                return {
                    "metadata": {
                        key: metadata[key]
                        for key in (
                            "name",
                            "namespace",
                            "uid",
                            "labels",
                            "ownerReferences",
                            "deletionTimestamp",
                            "finalizers",
                        )
                        if key in metadata
                    },
                    "admission_id": metadata.get("annotations", {}).get(ADMISSION_ID_ANNOTATION),
                    "node_name": serialized.get("spec", {}).get("nodeName"),
                    "status": serialized.get("status", {}),
                }

            def tick() -> None:
                errors = [
                    item
                    for item in execute_backfill_iteration(workspace, logging.getLogger("probe"))
                    if item
                ]
                assert not errors, errors

            try:
                graph = workspace.create_request_context().asset_graph
                with partition_loading_context(dynamic_partitions_store=instance):
                    backfill = PartitionBackfill.from_asset_partitions(
                        backfill_id="k8s-stop-proof",
                        asset_graph=graph,
                        partition_names=["one"],
                        asset_selection=[dg.AssetKey("remote_blocked")],
                        backfill_timestamp=time.time(),
                        tags={"dagster/backfill_stop_protocol": BACKFILL_STOP_PROTOCOL_VERSION},
                        dynamic_partitions_store=instance,
                        all_partitions=False,
                        title=None,
                        description=None,
                        run_config={
                            "execution": {
                                "config": {"max_concurrent": 1, "enable_owner_references": False}
                            }
                        },
                    )
                instance.add_backfill(backfill)
                tick()
                deadline = time.monotonic() + 120
                while True:
                    runs = instance.get_runs()
                    assert len(runs) == 1
                    run = runs[0]
                    blocked = any(
                        entry.message == "REMOTE_STEP_BLOCKING"
                        for entry in instance.all_logs(run.run_id)
                    )
                    admission = admission_request("GET", "/qa/status")
                    if (case == "normal" and blocked) or (
                        case != "normal" and admission["held_uid"] is not None
                    ):
                        break
                    assert time.monotonic() < deadline, (
                        "Step worker/admission did not reach requested phase"
                    )
                    assert not run.is_finished, run_view(instance)
                    time.sleep(0.2)
                started = inventory("parent_and_remote_step_running" if case == "normal" else case)
                assert run.status is dg.DagsterRunStatus.STARTED
                assert len(started["jobs"]) == 2, "Expected separate run and step Jobs"
                assert len(started["worker_pods"]) == (2 if case == "normal" else 1)
                assert all(pod["status"]["phase"] == "Running" for pod in started["worker_pods"])
                assert all(
                    POD_FINALIZER in pod["metadata"].get("finalizers", [])
                    for pod in started["worker_pods"]
                )
                assert all(pod["admission_id"] for pod in started["worker_pods"])
                assert len(started["launches"]) == (4 if case != "held-before" else 3)
                held_uid = admission["held_uid"]
                if case == "held-after":
                    assert any(
                        launch["worker_id"] == f"pod:{held_uid}"
                        and launch["kind"] == "CHILD"
                        and launch["state"] == "PENDING"
                        for launch in started["launches"]
                    )
                if case == "held-before":
                    assert not any(
                        launch["worker_id"] == f"pod:{held_uid}" for launch in started["launches"]
                    )
                assert all(not job["metadata"].get("ownerReferences") for job in started["jobs"]), (
                    "Remote step must be independent of parent garbage collection"
                )
                result["launched_job_names"] = [job["metadata"]["name"] for job in started["jobs"]]
                gql = create_schema().execute(
                    """mutation Cancel($id: String!) { cancelPartitionBackfill(backfillId: $id) {
                      __typename ... on CancelBackfillSuccess { backfillId } ... on PythonError { message }
                    }}""",
                    variable_values={"id": backfill.backfill_id},
                    context_value=workspace.create_request_context(),
                )
                assert not gql.errors, gql.errors
                result["cancel_mutation"] = gql.data
                assert gql.data["cancelPartitionBackfill"]["__typename"] == "CancelBackfillSuccess"
                assert inventory("native_cancel_requested")["backfill_status"] == "CANCELING"
                if case == "held-after":
                    for _ in range(2):
                        tick()
                        held = inventory("cancellation_while_child_response_held")
                        assert held["backfill_status"] == "CANCELING"
                        assert any(
                            launch["worker_id"] == f"pod:{held_uid}"
                            and launch["state"] == "PENDING"
                            for launch in held["launches"]
                        )
                        assert not admission_request("GET", "/qa/status")["released"]
                    result["admission_release"] = admission_request("POST", "/qa/release")
                deadline = time.monotonic() + 90
                while True:
                    tick()
                    observed = inventory("cancellation_tick")
                    if observed["backfill_status"] == "CANCELED":
                        assert observed["jobs"] == [], "CANCELED preceded Job deletion"
                        assert observed["worker_pods"] == [], "CANCELED preceded Pod exit"
                        assert observed["launches"] == [], "CANCELED preceded durable launch drain"
                        break
                    assert observed["backfill_status"] == "CANCELING"
                    assert time.monotonic() < deadline, (
                        "Backfill did not converge after workers exited"
                    )
                    time.sleep(0.2)
                if case == "held-before":
                    assert not admission_request("GET", "/qa/status")["released"]
                    result["admission_release"] = admission_request("POST", "/qa/release")
                    deadline = time.monotonic() + 10
                    while True:
                        admission = admission_request("GET", "/qa/status")
                        decisions = [
                            event
                            for event in admission["events"]
                            if event["uid"] == held_uid
                            and event["event"] in ("decision", "decision_error")
                        ]
                        if decisions:
                            assert all(not decision.get("allowed", False) for decision in decisions)
                            break
                        assert time.monotonic() < deadline, (
                            "Held admission did not produce denied decision"
                        )
                        time.sleep(0.2)
                    result["late_admission_denied"] = True
                for _ in range(2):
                    tick()
                    time.sleep(0.2)
                completed = inventory("stable_completed")
                assert completed["jobs"] == [] and completed["worker_pods"] == []
                assert completed["launches"] == []
                assert not [run for run in instance.get_runs() if not run.is_finished]
                result["fully_stopped"] = True
                result["admission_events"] = admission_request("GET", "/qa/status")
            except Exception:
                result["error"] = traceback.format_exc()
                traceback.print_exc()
                exit_code = 1
            finally:
                try:
                    admission_request("POST", "/qa/release")
                except requests.RequestException:
                    result["admission_release_error"] = traceback.format_exc()
                try:
                    inventory("final_before_cleanup")
                except Exception:
                    result["inventory_error"] = traceback.format_exc()
                if exit_code != 0:
                    try:
                        if instance.get_backfill("k8s-stop-proof") is not None:
                            create_schema().execute(
                                """mutation { cancelPartitionBackfill(backfillId: "k8s-stop-proof") {
                                  __typename
                                }}""",
                                context_value=workspace.create_request_context(),
                            )
                            deadline = time.monotonic() + 90
                            while True:
                                tick()
                                cleanup = inventory("failure_cleanup_native_tick")
                                if not (
                                    cleanup["jobs"] or cleanup["worker_pods"] or cleanup["launches"]
                                ):
                                    result["failure_cleanup_drained"] = True
                                    break
                                assert time.monotonic() < deadline, (
                                    "Native failure cleanup did not drain; retain admission service "
                                    "and PostgreSQL for evidence-backed repair"
                                )
                                time.sleep(0.2)
                    except Exception:
                        result["failure_cleanup_error"] = traceback.format_exc()
                result["native_events"] = [
                    serialize_value(entry)
                    for run in instance.get_runs()
                    for entry in instance.all_logs(run.run_id)
                ]
                result["final_runs"] = run_view(instance)
    result["elapsed_seconds"] = time.time() - result["started_at"]
    print("DAGSTER_CANCEL_EVIDENCE=" + json.dumps(result, sort_keys=True), flush=True)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
