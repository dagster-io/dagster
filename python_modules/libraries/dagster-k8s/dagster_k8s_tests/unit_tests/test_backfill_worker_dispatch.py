from unittest import mock

import kubernetes.client
import pytest
from dagster import DagsterInstance
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.storage.runs.base import K8sWorkerTarget, WorkerLaunchKind, WorkerLaunchState
from dagster._core.storage.tags import BACKFILL_ID_TAG, BACKFILL_STOP_PROTOCOL_TAG
from dagster_k8s.client import DagsterKubernetesClient
from urllib3.exceptions import ReadTimeoutError


def test_single_dispatch_disables_transport_retries_without_mutating_shared_client():
    configuration = kubernetes.client.Configuration()
    configuration.retries = 9
    shared_client = kubernetes.client.ApiClient(configuration=configuration)
    batch_api = kubernetes.client.BatchV1Api(api_client=shared_client)
    client = DagsterKubernetesClient.production_client(batch_api_override=batch_api)
    job = kubernetes.client.V1Job(metadata=kubernetes.client.V1ObjectMeta(name="worker"))
    dispatched_api = mock.Mock()
    with mock.patch("kubernetes.client.BatchV1Api", return_value=dispatched_api) as factory:
        client.create_namespaced_job_once(job, "worker-namespace")
        dedicated_client = factory.call_args.kwargs["api_client"]
        assert dedicated_client.configuration.retries == 0
        assert dedicated_client.rest_client.pool_manager.connection_pool_kw["retries"].total == 0
    assert shared_client.configuration.retries == 9
    assert dispatched_api.create_namespaced_job.call_count == 1
    assert dispatched_api.create_namespaced_job.call_args.kwargs["namespace"] == "worker-namespace"
    shared_client.close()


def test_ambiguous_create_cannot_acknowledge_or_complete_backfill():
    client = DagsterKubernetesClient.production_client()
    job = kubernetes.client.V1Job(metadata=kubernetes.client.V1ObjectMeta(name="worker"))
    deferred_creates = []
    live_jobs = []

    def ambiguous_create(**_):
        deferred_creates.append(lambda: live_jobs.append("worker"))
        raise ReadTimeoutError(None, "/apis/batch/v1/jobs", "response lost")

    dispatched_api = mock.Mock()
    dispatched_api.create_namespaced_job.side_effect = ambiguous_create
    with DagsterInstance.ephemeral() as instance:
        backfill = PartitionBackfill(
            backfill_id="backfill",
            status=BulkActionStatus.REQUESTED,
            from_failure=False,
            tags={BACKFILL_STOP_PROTOCOL_TAG: "v2"},
            backfill_timestamp=1.0,
        )
        instance.add_backfill(backfill)
        run = instance.run_storage.add_run(
            DagsterRun(job_name="job", run_id="run", tags={BACKFILL_ID_TAG: "backfill"})
        )
        assert instance.claim_backfill_worker_launch(
            run.run_id,
            "run",
            WorkerLaunchKind.RUN,
            K8sWorkerTarget(job_name="worker", namespace="worker-namespace"),
        )
        with mock.patch("kubernetes.client.BatchV1Api", return_value=dispatched_api):
            with pytest.raises(ReadTimeoutError):
                client.create_namespaced_job_once(job, "worker-namespace")
                instance.acknowledge_backfill_worker_launch(run.run_id, "run")
        assert dispatched_api.create_namespaced_job.call_count == 1
        instance.request_backfill_stop("backfill")
        instance.report_run_canceled(run)
        instance.resolve_backfill_worker_launch(run.run_id, "run")
        instance.update_backfill(backfill.with_status(BulkActionStatus.CANCELED))
        assert instance.get_backfill("backfill").status == BulkActionStatus.CANCELING
        assert (
            instance.get_backfill_worker_launches("backfill")[0].state == WorkerLaunchState.PENDING
        )
        deferred_creates[0]()
        assert live_jobs == ["worker"]
        assert instance.get_backfill("backfill").status == BulkActionStatus.CANCELING
