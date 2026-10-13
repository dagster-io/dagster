from types import SimpleNamespace
from unittest import mock

import pytest
from dagster._check import CheckError
from dagster._core.launcher.base import BackfillWorkerCreationStatus, BackfillWorkerExitStatus
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus
from dagster._core.storage.runs.base import (
    BackfillWorkerLaunch,
    ChildWorkerTarget,
    K8sPodWorkerTarget,
    K8sWorkerTarget,
    UnknownWorkerTarget,
    WorkerLaunchKind,
    WorkerLaunchState,
)
from dagster._core.storage.tags import BACKFILL_STOP_PROTOCOL_VERSION
from dagster_k8s import K8sRunLauncher
from dagster_k8s.backfill_admission import (
    ADMISSION_ID_ANNOTATION,
    ADMISSION_ROUTE_LABEL,
    ADMISSION_WEBHOOK_NAME,
    DISPATCH_ID_ANNOTATION,
    POD_FINALIZER,
    PROTOCOL_LABEL,
)
from kubernetes.client import (
    ApiClient,
    V1ContainerState,
    V1ContainerStateTerminated,
    V1ContainerStatus,
    V1DeleteOptions,
    V1Job,
    V1JobCondition,
    V1JobStatus,
    V1ObjectMeta,
    V1OwnerReference,
    V1Pod,
    V1PodStatus,
    V1Preconditions,
)
from kubernetes.client.rest import ApiException


@pytest.fixture
def launcher(kubeconfig_file):
    return K8sRunLauncher(
        service_account_name="service-account",
        instance_config_map="instance-config",
        dagster_home="/opt/dagster",
        job_image="image",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock.Mock(),
        k8s_client_core_api=mock.Mock(),
    )


def dispatch(target=None, kind=WorkerLaunchKind.STEP):
    return BackfillWorkerLaunch(
        run_id="run-id",
        worker_id="step:my_step:1",
        kind=kind,
        target=target
        or K8sWorkerTarget(
            job_name="step-job",
            namespace="overridden-namespace",
            admission_webhook_name="dagster-backfill-worker-admission",
        ),
        state=WorkerLaunchState.ACKNOWLEDGED,
    )


def worker_metadata(name, uid):
    return V1ObjectMeta(
        name=name,
        uid=uid,
        namespace="overridden-namespace",
        labels={
            "dagster/run-id": "run-id",
            "dagster/worker-job": "step-job",
            ADMISSION_ROUTE_LABEL: ADMISSION_WEBHOOK_NAME,
            PROTOCOL_LABEL: BACKFILL_STOP_PROTOCOL_VERSION,
        },
        owner_references=[
            V1OwnerReference(api_version="batch/v1", kind="Job", name="step-job", uid="job-uid")
        ],
    )


@pytest.mark.parametrize("status", [DagsterRunStatus.STARTED, DagsterRunStatus.CANCELED])
def test_pod_presence_prevents_exit_after_job_deletion(launcher, status):
    run = DagsterRun(job_name="job", run_id="run-id", status=status)
    launcher._api_client.batch_api.read_namespaced_job.side_effect = ApiException(status=404)  # noqa: SLF001
    launcher._api_client.core_api.list_namespaced_pod.return_value = SimpleNamespace(  # noqa: SLF001
        items=[V1Pod(metadata=worker_metadata("step-pod", "pod-uid"))]
    )
    assert (
        launcher.get_backfill_worker_exit_status(run, dispatch())
        == BackfillWorkerExitStatus.RUNNING
    )


def test_job_presence_prevents_exit_even_without_active_pods(launcher):
    run = DagsterRun(job_name="job", run_id="run-id", status=DagsterRunStatus.CANCELED)
    launcher._api_client.batch_api.read_namespaced_job.return_value = SimpleNamespace(  # noqa: SLF001
        metadata=worker_metadata("step-job", "job-uid"), status=SimpleNamespace(conditions=[])
    )
    assert (
        launcher.get_backfill_worker_exit_status(run, dispatch())
        == BackfillWorkerExitStatus.RUNNING
    )
    launcher._api_client.core_api.list_namespaced_pod.assert_not_called()  # noqa: SLF001


def test_exit_requires_job_and_pods_absent_in_persisted_namespace(launcher):
    run = DagsterRun(job_name="job", run_id="run-id", status=DagsterRunStatus.CANCELED)
    launcher._api_client.batch_api.read_namespaced_job.side_effect = ApiException(status=404)  # noqa: SLF001
    launcher._api_client.core_api.list_namespaced_pod.return_value = SimpleNamespace(items=[])  # noqa: SLF001
    assert (
        launcher.get_backfill_worker_exit_status(run, dispatch()) == BackfillWorkerExitStatus.EXITED
    )
    launcher._api_client.batch_api.read_namespaced_job.assert_called_once_with(  # noqa: SLF001
        name="step-job", namespace="overridden-namespace"
    )
    launcher._api_client.core_api.list_namespaced_pod.assert_called_once_with(  # noqa: SLF001
        namespace="overridden-namespace", label_selector="dagster/worker-job=step-job"
    )


def test_inventory_error_and_unsupported_targets_are_unknown(launcher):
    run = DagsterRun(job_name="job", run_id="run-id", status=DagsterRunStatus.CANCELED)
    launcher._api_client.batch_api.read_namespaced_job.side_effect = ApiException(status=403)  # noqa: SLF001
    assert (
        launcher.get_backfill_worker_exit_status(run, dispatch())
        == BackfillWorkerExitStatus.UNKNOWN
    )
    assert (
        launcher.get_backfill_worker_exit_status(
            run, dispatch(UnknownWorkerTarget(handler_name="unsupported"))
        )
        == BackfillWorkerExitStatus.UNKNOWN
    )


def test_stop_deletes_recorded_step_job_and_detached_pods_with_foreground_gc(launcher):
    run = DagsterRun(job_name="job", run_id="run-id", status=DagsterRunStatus.FAILURE)
    pod = V1Pod(metadata=worker_metadata("detached-step-pod", "pod-uid"))
    launcher._api_client.batch_api.read_namespaced_job.return_value = V1Job(  # noqa: SLF001
        metadata=worker_metadata("step-job", "job-uid")
    )
    launcher._api_client.core_api.list_namespaced_pod.return_value = SimpleNamespace(items=[pod])  # noqa: SLF001
    launcher.request_backfill_worker_stop(run, dispatch())
    launcher._api_client.batch_api.delete_namespaced_job.assert_called_once_with(  # noqa: SLF001
        name="step-job",
        namespace="overridden-namespace",
        body=V1DeleteOptions(
            propagation_policy="Foreground", preconditions=V1Preconditions(uid="job-uid")
        ),
    )
    launcher._api_client.core_api.delete_namespaced_pod.assert_called_once_with(  # noqa: SLF001
        name="detached-step-pod",
        namespace="overridden-namespace",
        body=V1DeleteOptions(preconditions=V1Preconditions(uid="pod-uid")),
    )


@pytest.mark.parametrize("condition_type", ["Complete", "Failed"])
def test_terminal_job_and_terminated_pods_prove_exit_without_waiting_for_ttl(
    launcher, condition_type
):
    run = DagsterRun(job_name="job", run_id="run-id", status=DagsterRunStatus.SUCCESS)
    launcher._api_client.batch_api.read_namespaced_job.return_value = V1Job(  # noqa: SLF001
        metadata=worker_metadata("step-job", "job-uid"),
        status=V1JobStatus(conditions=[V1JobCondition(type=condition_type, status="True")]),
    )
    pod = V1Pod(
        metadata=worker_metadata("step-pod", "pod-uid"),
        status=V1PodStatus(
            phase="Succeeded",
            container_statuses=[
                V1ContainerStatus(
                    name="dagster",
                    image="image",
                    image_id="image-id",
                    ready=False,
                    restart_count=0,
                    state=V1ContainerState(terminated=V1ContainerStateTerminated(exit_code=0)),
                )
            ],
        ),
    )
    launcher._api_client.core_api.list_namespaced_pod.return_value = SimpleNamespace(items=[pod])  # noqa: SLF001
    assert (
        launcher.get_backfill_worker_exit_status(run, dispatch()) == BackfillWorkerExitStatus.EXITED
    )


@pytest.mark.parametrize("condition_type", ["FailureTarget", "SuccessCriteriaMet"])
def test_preterminal_job_condition_does_not_prove_exit(launcher, condition_type):
    run = DagsterRun(job_name="job", run_id="run-id", status=DagsterRunStatus.SUCCESS)
    launcher._api_client.batch_api.read_namespaced_job.return_value = V1Job(  # noqa: SLF001
        metadata=worker_metadata("step-job", "job-uid"),
        status=V1JobStatus(conditions=[V1JobCondition(type=condition_type, status="True")]),
    )
    assert (
        launcher.get_backfill_worker_exit_status(run, dispatch())
        == BackfillWorkerExitStatus.RUNNING
    )


@pytest.mark.parametrize("wrong_field", ["run_id", "namespace", "owner_uid"])
def test_terminal_objects_with_wrong_worker_identity_are_unknown(launcher, wrong_field):
    run = DagsterRun(job_name="job", run_id="run-id", status=DagsterRunStatus.SUCCESS)
    job = V1Job(
        metadata=worker_metadata("step-job", "job-uid"),
        status=V1JobStatus(conditions=[V1JobCondition(type="Complete", status="True")]),
    )
    pod = V1Pod(
        metadata=worker_metadata("step-pod", "pod-uid"), status=V1PodStatus(phase="Succeeded")
    )
    if wrong_field == "run_id":
        job.metadata.labels["dagster/run-id"] = "different-run"
    elif wrong_field == "namespace":
        pod.metadata.namespace = "different-namespace"
    else:
        pod.metadata.owner_references[0].uid = "different-job-uid"
    launcher._api_client.batch_api.read_namespaced_job.return_value = job  # noqa: SLF001
    launcher._api_client.core_api.list_namespaced_pod.return_value = SimpleNamespace(items=[pod])  # noqa: SLF001
    assert (
        launcher.get_backfill_worker_exit_status(run, dispatch())
        == BackfillWorkerExitStatus.UNKNOWN
    )


def test_stop_refuses_to_delete_a_replaced_job(launcher):
    run = DagsterRun(job_name="job", run_id="run-id", status=DagsterRunStatus.CANCELED)
    job = V1Job(metadata=worker_metadata("step-job", "job-uid"))
    job.metadata.labels["dagster/run-id"] = "different-run"
    launcher._api_client.batch_api.read_namespaced_job.return_value = job  # noqa: SLF001
    with pytest.raises(CheckError, match="identity does not match"):
        launcher.request_backfill_worker_stop(run, dispatch())
    launcher._api_client.batch_api.delete_namespaced_job.assert_not_called()  # noqa: SLF001


def physical_dispatch(state=WorkerLaunchState.ACKNOWLEDGED):
    return BackfillWorkerLaunch(
        run_id="run-id",
        worker_id="pod:admission",
        kind=WorkerLaunchKind.CHILD,
        target=ChildWorkerTarget(
            parent_worker_id="step:my_step:1",
            resource=K8sPodWorkerTarget(
                pod_name="dagster-worker-admission",
                namespace="overridden-namespace",
                admission_id="admission",
                job_name="step-job",
                job_uid="job-uid",
            ),
        ),
        state=state,
    )


def persisted_pod(launcher):
    pod = {
        "metadata": {
            "name": "dagster-worker-admission",
            "namespace": "overridden-namespace",
            "uid": "pod-uid",
            "resourceVersion": "42",
            "labels": {
                "dagster/run-id": "run-id",
                "dagster/worker-job": "step-job",
                ADMISSION_ROUTE_LABEL: ADMISSION_WEBHOOK_NAME,
                PROTOCOL_LABEL: BACKFILL_STOP_PROTOCOL_VERSION,
            },
            "annotations": {
                ADMISSION_ID_ANNOTATION: "admission",
                DISPATCH_ID_ANNOTATION: "step:my_step:1",
            },
            "ownerReferences": [
                {"kind": "Job", "name": "step-job", "uid": "job-uid", "controller": True}
            ],
            "finalizers": [POD_FINALIZER, "another.example/retained"],
        },
        "spec": {"containers": [{"name": "dagster"}], "nodeName": "node"},
        "status": {
            "phase": "Succeeded",
            "containerStatuses": [{"name": "dagster", "state": {"terminated": {"exitCode": 0}}}],
        },
    }
    api = launcher._api_client.core_api  # noqa: SLF001
    api.read_namespaced_pod.return_value = pod
    api.api_client.sanitize_for_serialization.side_effect = ApiClient().sanitize_for_serialization
    return pod


def test_pending_physical_receipt_requires_retained_persistence_witness(launcher):
    pod = persisted_pod(launcher)
    run = DagsterRun(job_name="job", run_id="run-id")
    claim = physical_dispatch(WorkerLaunchState.PENDING)
    assert (
        launcher.get_backfill_worker_creation_status(run, claim)
        == BackfillWorkerCreationStatus.CREATED
    )
    pod["metadata"]["finalizers"] = []
    assert (
        launcher.get_backfill_worker_creation_status(run, claim)
        == BackfillWorkerCreationStatus.UNKNOWN
    )
    launcher._api_client.core_api.read_namespaced_pod.side_effect = ApiException(status=404)  # noqa: SLF001
    assert launcher.get_backfill_worker_exit_status(run, claim) == BackfillWorkerExitStatus.UNKNOWN
    assert (
        launcher.get_backfill_worker_exit_status(run, physical_dispatch())
        == BackfillWorkerExitStatus.EXITED
    )


@pytest.mark.parametrize("field", ["namespace", "run", "admission", "parent", "owner", "version"])
def test_physical_identity_mismatch_cannot_acknowledge_or_resolve(launcher, field):
    pod = persisted_pod(launcher)
    metadata = pod["metadata"]
    if field == "namespace":
        metadata["namespace"] = "other"
    elif field == "owner":
        metadata["ownerReferences"][0]["uid"] = "other"
    elif field in ("parent", "admission"):
        metadata["annotations"][
            DISPATCH_ID_ANNOTATION if field == "parent" else ADMISSION_ID_ANNOTATION
        ] = "other"
    else:
        metadata["labels"][PROTOCOL_LABEL if field == "version" else "dagster/run-id"] = "other"
    run = DagsterRun(job_name="job", run_id="run-id")
    assert (
        launcher.get_backfill_worker_creation_status(run, physical_dispatch())
        == BackfillWorkerCreationStatus.UNKNOWN
    )
    assert (
        launcher.get_backfill_worker_exit_status(run, physical_dispatch())
        == BackfillWorkerExitStatus.UNKNOWN
    )


def test_exit_checks_every_declared_container_and_terminal_phase(launcher):
    pod = persisted_pod(launcher)
    run = DagsterRun(job_name="job", run_id="run-id")
    assert (
        launcher.get_backfill_worker_exit_status(run, physical_dispatch())
        == BackfillWorkerExitStatus.EXITED
    )
    pod["spec"]["initContainers"] = [{"name": "init"}]
    assert (
        launcher.get_backfill_worker_exit_status(run, physical_dispatch())
        == BackfillWorkerExitStatus.RUNNING
    )
    pod["status"]["initContainerStatuses"] = [
        {"name": "init", "state": {"terminated": {"exitCode": 0}}}
    ]
    assert (
        launcher.get_backfill_worker_exit_status(run, physical_dispatch())
        == BackfillWorkerExitStatus.EXITED
    )
    pod["status"]["phase"] = "Running"
    assert (
        launcher.get_backfill_worker_exit_status(run, physical_dispatch())
        == BackfillWorkerExitStatus.RUNNING
    )


def test_deleting_unscheduled_pod_has_definitive_nonexecution_evidence(launcher):
    pod = persisted_pod(launcher)
    pod["status"] = {"phase": "Pending"}
    pod["spec"].pop("nodeName")
    run = DagsterRun(job_name="job", run_id="run-id")
    assert (
        launcher.get_backfill_worker_exit_status(run, physical_dispatch())
        == BackfillWorkerExitStatus.RUNNING
    )
    pod["metadata"]["deletionTimestamp"] = "2026-10-12T12:00:00Z"
    assert (
        launcher.get_backfill_worker_exit_status(run, physical_dispatch())
        == BackfillWorkerExitStatus.EXITED
    )


def test_finalizer_cleanup_preserves_other_owners_and_fences_the_observed_version(launcher):
    persisted_pod(launcher)
    run = DagsterRun(job_name="job", run_id="run-id")
    launcher.cleanup_backfill_worker_launch(run, physical_dispatch())
    body = launcher._api_client.core_api.patch_namespaced_pod.call_args.kwargs["body"]  # noqa: SLF001
    assert body == [
        {"op": "test", "path": "/metadata/uid", "value": "pod-uid"},
        {"op": "test", "path": "/metadata/resourceVersion", "value": "42"},
        {"op": "replace", "path": "/metadata/finalizers", "value": ["another.example/retained"]},
    ]


def test_physical_stop_is_uid_fenced_without_force_deletion(launcher):
    persisted_pod(launcher)
    run = DagsterRun(job_name="job", run_id="run-id")
    launcher.request_backfill_worker_stop(run, physical_dispatch())
    launcher._api_client.core_api.delete_namespaced_pod.assert_called_once_with(  # noqa: SLF001
        name="dagster-worker-admission",
        namespace="overridden-namespace",
        body=V1DeleteOptions(preconditions=V1Preconditions(uid="pod-uid")),
    )
    launcher._api_client.batch_api.delete_namespaced_job.assert_not_called()  # noqa: SLF001
