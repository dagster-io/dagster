import base64
import copy
import json
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from threading import Thread
from unittest import mock
from uuid import uuid4

import pytest
from dagster import DagsterInstance
from dagster._check import CheckError
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.storage.runs.base import K8sWorkerTarget, WorkerLaunchKind, WorkerLaunchState
from dagster._core.storage.tags import (
    BACKFILL_ID_TAG,
    BACKFILL_STOP_PROTOCOL_TAG,
    BACKFILL_STOP_PROTOCOL_VERSION,
)
from dagster_k8s.backfill_admission import (
    ADMISSION_ID_ANNOTATION,
    ADMISSION_ROUTE_LABEL,
    ADMISSION_WEBHOOK_NAME,
    DISPATCH_ID_ANNOTATION,
    POD_FINALIZER,
    PROTOCOL_LABEL,
    WEBHOOK_CONTRACT_ANNOTATION,
    BackfillPodAdmission,
    PodAdmissionReview,
    stamp_backfill_job,
)
from dagster_k8s.backfill_admission_server import AdmissionHandler
from dagster_k8s.backfill_worker import WebhookConfiguration
from dagster_k8s.job import (
    DagsterK8sJobConfig,
    UserDefinedDagsterK8sConfig,
    construct_dagster_k8s_job,
)
from kubernetes.client import ApiClient, V1Job, V1ObjectMeta
from pydantic import ValidationError


def review_payload():
    return {
        "apiVersion": "admission.k8s.io/v1",
        "kind": "AdmissionReview",
        "request": {
            "uid": str(uuid4()),
            "namespace": "workers",
            "operation": "CREATE",
            "resource": {"group": "", "version": "v1", "resource": "pods"},
            "object": {
                "apiVersion": "v1",
                "kind": "Pod",
                "metadata": {
                    "generateName": "job-",
                    "labels": {
                        "dagster/run-id": "run",
                        "dagster/worker-job": "job",
                        ADMISSION_ROUTE_LABEL: ADMISSION_WEBHOOK_NAME,
                        PROTOCOL_LABEL: BACKFILL_STOP_PROTOCOL_VERSION,
                    },
                    "annotations": {DISPATCH_ID_ANNOTATION: "step"},
                    "ownerReferences": [
                        {"kind": "Job", "name": "job", "uid": "job-uid", "controller": True}
                    ],
                    "finalizers": ["another.example/finalizer"],
                },
                "spec": {"restartPolicy": "Never", "containers": [{"name": "dagster"}]},
            },
        },
    }


@pytest.fixture
def admission():
    with DagsterInstance.ephemeral() as instance:
        instance.add_backfill(
            PartitionBackfill(
                backfill_id="backfill",
                status=BulkActionStatus.REQUESTED,
                from_failure=False,
                tags={BACKFILL_STOP_PROTOCOL_TAG: BACKFILL_STOP_PROTOCOL_VERSION},
                backfill_timestamp=1.0,
            )
        )
        instance.run_storage.add_run(
            DagsterRun(job_name="job", run_id="run", tags={BACKFILL_ID_TAG: "backfill"})
        )
        assert instance.claim_backfill_worker_launch(
            "run",
            "step",
            WorkerLaunchKind.STEP,
            K8sWorkerTarget(
                job_name="job",
                namespace="workers",
                admission_webhook_name="dagster-backfill-worker-admission",
            ),
        )
        metadata = review_payload()["request"]["object"]["metadata"]
        batch = mock.Mock()
        batch.read_namespaced_job.return_value = V1Job(
            metadata=V1ObjectMeta(
                name="job",
                namespace="workers",
                uid="job-uid",
                labels=metadata["labels"],
                annotations=metadata["annotations"],
            )
        )
        yield BackfillPodAdmission(instance, batch, ADMISSION_WEBHOOK_NAME)


def children(admission):
    return [
        claim
        for claim in admission.instance.get_backfill_worker_launches("backfill")
        if claim.kind == WorkerLaunchKind.CHILD
    ]


def test_admission_commits_a_pending_identity_before_allowing_persistence(admission):
    payload = review_payload()
    result = admission.admit(PodAdmissionReview.model_validate(payload))
    assert result["allowed"]
    claim = children(admission)[0]
    assert claim.state == WorkerLaunchState.PENDING
    assert claim.target.parent_worker_id == "step"
    assert claim.target.resource.job_uid == "job-uid"
    patches = {
        item["path"]: item["value"] for item in json.loads(base64.b64decode(result["patch"]))
    }
    assert patches["/metadata/name"] == claim.target.resource.pod_name
    assert patches["/metadata/annotations"][ADMISSION_ID_ANNOTATION] == payload["request"]["uid"]
    assert patches["/metadata/finalizers"] == ["another.example/finalizer", POD_FINALIZER]


def test_pending_callback_replay_preserves_one_receipt_after_closure(admission):
    request = PodAdmissionReview.model_validate(review_payload())
    first = admission.admit(request)
    admission.instance.request_backfill_stop("backfill")
    admission.batch_api.read_namespaced_job.side_effect = RuntimeError("Job already deleted")
    assert admission.admit(request) == first
    assert len(children(admission)) == 1
    admission.instance.acknowledge_backfill_worker_launch("run", children(admission)[0].worker_id)
    assert not admission.admit(request)["allowed"]


def test_controller_replacements_receive_independent_receipts(admission):
    first = PodAdmissionReview.model_validate(review_payload())
    second = PodAdmissionReview.model_validate(review_payload())
    assert admission.admit(first)["allowed"]
    assert admission.admit(second)["allowed"]
    receipts = children(admission)
    assert len(receipts) == 2
    assert {claim.target.resource.admission_id for claim in receipts} == {
        str(first.request.uid),
        str(second.request.uid),
    }
    assert len({claim.target.resource.pod_name for claim in receipts}) == 2
    assert {claim.target.parent_worker_id for claim in receipts} == {"step"}


def test_new_admission_after_close_is_denied_without_a_receipt(admission):
    admission.instance.request_backfill_stop("backfill")
    assert not admission.admit(PodAdmissionReview.model_validate(review_payload()))["allowed"]
    assert children(admission) == []


def test_dry_run_does_not_persist_or_consult_the_owner(admission):
    payload = review_payload()
    payload["request"]["dryRun"] = True
    admission.batch_api.read_namespaced_job.side_effect = RuntimeError("Must not consult owner")
    assert admission.admit(PodAdmissionReview.model_validate(payload))["allowed"]
    assert children(admission) == []


def test_http_admission_accepts_the_api_servers_timeout_query(admission):
    class TestServer(ThreadingHTTPServer):
        def __init__(self):
            self.admission = admission
            super().__init__(("127.0.0.1", 0), AdmissionHandler)

    server = TestServer()
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
    try:
        payload = review_payload()
        connection.request(
            "POST",
            "/admit?timeout=30s",
            body=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        assert response.status == 200
        result = json.loads(response.read())["response"]
        assert result["uid"] == payload["request"]["uid"] and result["allowed"]
        assert len(children(admission)) == 1
        connection.request("GET", "/healthz?probe=true")
        response = connection.getresponse()
        assert response.status == 200
        response.read()
        connection.request("POST", "/other?path=/admit", body="{}")
        response = connection.getresponse()
        assert response.status == 404
        response.read()
        assert len(children(admission)) == 1
    finally:
        connection.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.parametrize("field", ["namespace", "run", "job_uid", "dispatch", "route", "version"])
def test_mismatched_job_identity_denies_creation(admission, field):
    metadata = admission.batch_api.read_namespaced_job.return_value.metadata
    if field == "namespace":
        metadata.namespace = "other"
    elif field == "job_uid":
        metadata.uid = "other"
    elif field == "dispatch":
        metadata.annotations[DISPATCH_ID_ANNOTATION] = "other"
    else:
        label = {
            "run": "dagster/run-id",
            "route": ADMISSION_ROUTE_LABEL,
            "version": PROTOCOL_LABEL,
        }[field]
        metadata.labels[label] = "other"
    assert not admission.admit(PodAdmissionReview.model_validate(review_payload()))["allowed"]
    assert children(admission) == []


def test_native_job_with_restarting_init_sidecar_gets_a_physical_receipt(admission):
    job = construct_dagster_k8s_job(
        job_config=DagsterK8sJobConfig(job_image="image"),
        args=["execute"],
        job_name="job",
        user_defined_k8s_config=UserDefinedDagsterK8sConfig(
            pod_spec_config={
                "init_containers": [
                    {"name": "sql-proxy", "image": "proxy", "restart_policy": "Always"}
                ]
            }
        ),
    )
    stamp_backfill_job(job, "run", "step", ADMISSION_WEBHOOK_NAME)
    payload = review_payload()
    payload["request"]["object"]["spec"] = ApiClient().sanitize_for_serialization(
        job.spec.template.spec
    )
    assert admission.admit(PodAdmissionReview.model_validate(payload))["allowed"]
    assert len(children(admission)) == 1


def webhook_configuration():
    return {
        "metadata": {
            "name": ADMISSION_WEBHOOK_NAME,
            "annotations": {WEBHOOK_CONTRACT_ANNOTATION: BACKFILL_STOP_PROTOCOL_VERSION},
        },
        "webhooks": [
            {
                "failurePolicy": "Fail",
                "sideEffects": "NoneOnDryRun",
                "reinvocationPolicy": "Never",
                "admissionReviewVersions": ["v1"],
                "objectSelector": {"matchLabels": {ADMISSION_ROUTE_LABEL: ADMISSION_WEBHOOK_NAME}},
                "rules": [
                    {
                        "operations": ["CREATE"],
                        "apiGroups": [""],
                        "apiVersions": ["v1"],
                        "resources": ["pods"],
                        "scope": "Namespaced",
                    }
                ],
                "clientConfig": {
                    "service": {"name": "admission", "namespace": "workers", "path": "/admit"},
                    "caBundle": "certificate",
                },
            }
        ],
    }


def test_exact_fail_closed_webhook_binding_is_required():
    configuration = webhook_configuration()
    WebhookConfiguration.model_validate(configuration).require_binding(ADMISSION_WEBHOOK_NAME)
    for field, value in [("failurePolicy", "Ignore"), ("reinvocationPolicy", "IfNeeded")]:
        invalid = copy.deepcopy(configuration)
        invalid["webhooks"][0][field] = value
        with pytest.raises(ValidationError):
            WebhookConfiguration.model_validate(invalid)
    invalid = copy.deepcopy(configuration)
    invalid["webhooks"][0]["matchConditions"] = [{"name": "skip", "expression": "false"}]
    with pytest.raises(ValidationError):
        WebhookConfiguration.model_validate(invalid)
    for changes in [
        {"namespaceSelector": {"matchLabels": {"namespace": "somewhere"}}},
        {"objectSelector": {"matchLabels": {ADMISSION_ROUTE_LABEL: "other"}}},
    ]:
        invalid = copy.deepcopy(configuration)
        invalid["webhooks"][0].update(changes)
        with pytest.raises(CheckError):
            WebhookConfiguration.model_validate(invalid).require_binding(ADMISSION_WEBHOOK_NAME)
