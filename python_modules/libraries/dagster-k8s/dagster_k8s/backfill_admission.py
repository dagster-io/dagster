"""Durable admission of Kubernetes Job-controller Pods owned by backfills."""

import base64
import json
from collections.abc import Mapping
from typing import Literal
from uuid import UUID

import dagster._check as check
from dagster import DagsterInstance
from dagster._core.storage.runs.base import (
    ChildWorkerTarget,
    K8sPodWorkerTarget,
    K8sWorkerTarget,
    WorkerLaunchKind,
    WorkerLaunchState,
)
from dagster._core.storage.tags import BACKFILL_ID_TAG, BACKFILL_STOP_PROTOCOL_VERSION
from pydantic import BaseModel, ConfigDict, Field

ADMISSION_WEBHOOK_NAME = "dagster-backfill-worker-admission"
ADMISSION_ROUTE_LABEL = "dagster/backfill-admission"
ADMISSION_ID_ANNOTATION = "dagster/pod-admission-id"
DISPATCH_ID_ANNOTATION = "dagster/worker-dispatch-id"
PROTOCOL_LABEL = "dagster/backfill-stop-protocol"
POD_FINALIZER = "dagster.io/backfill-worker"
WEBHOOK_CONTRACT_ANNOTATION = "dagster/worker-admission-contract"


class OwnerReference(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    kind: str
    name: str = Field(min_length=1)
    uid: str = Field(min_length=1)
    controller: bool = False


class PodMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    namespace: str | None = None
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)
    finalizers: list[str] = Field(default_factory=list)
    owner_references: list[OwnerReference] = Field(default_factory=list, alias="ownerReferences")


class PodObject(BaseModel):
    model_config = ConfigDict(extra="ignore")
    kind: Literal["Pod"]
    apiVersion: Literal["v1"]
    metadata: PodMetadata
    spec: "PodExecutionPolicy"


class ContainerExecutionPolicy(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    restart_policy: None = Field(default=None, alias="restartPolicy")
    restart_policy_rules: list = Field(
        default_factory=list, alias="restartPolicyRules", max_length=0
    )


class PodExecutionPolicy(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    restart_policy: Literal["Never"] = Field(alias="restartPolicy")
    containers: list[ContainerExecutionPolicy] = Field(min_length=1)
    init_containers: list[ContainerExecutionPolicy] = Field(
        default_factory=list, alias="initContainers"
    )


class PodResource(BaseModel):
    group: Literal[""]
    version: Literal["v1"]
    resource: Literal["pods"]


class PodAdmissionRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    uid: UUID
    namespace: str = Field(min_length=1)
    operation: Literal["CREATE"]
    resource: PodResource
    object: PodObject
    dryRun: bool = False
    subResource: Literal[""] = ""


class PodAdmissionReview(BaseModel):
    model_config = ConfigDict(extra="ignore")
    apiVersion: Literal["admission.k8s.io/v1"]
    kind: Literal["AdmissionReview"]
    request: PodAdmissionRequest


def require_backfill_worker_policy(pod_spec: Mapping, container: Mapping) -> None:
    PodExecutionPolicy.model_validate(
        {
            "restart_policy": "Never",
            **pod_spec,
            "containers": [container, *pod_spec.get("containers", [])],
        }
    )


def stamp_backfill_job(job, run_id: str, worker_id: str, webhook_name: str) -> None:
    """Protect the metadata copied by the standard Job controller into each Pod."""
    specification = job.spec.template.spec
    check.invariant(
        specification.restart_policy == "Never"
        and all(
            getattr(container, "restart_policy", None) is None
            and not getattr(container, "restart_policy_rules", None)
            for container in (*specification.containers, *(specification.init_containers or []))
        ),
        "Backfill workers require restartPolicy Never without restarting containers; "
        "Kubernetes Jobs and Dagster retries may create separately admitted replacement Pods.",
    )
    for metadata in (job.metadata, job.spec.template.metadata):
        metadata.labels = {
            **(metadata.labels or {}),
            "dagster/run-id": run_id,
            "dagster/worker-job": job.metadata.name,
            ADMISSION_ROUTE_LABEL: webhook_name,
            PROTOCOL_LABEL: BACKFILL_STOP_PROTOCOL_VERSION,
        }
        metadata.annotations = {
            **(metadata.annotations or {}),
            DISPATCH_ID_ANNOTATION: worker_id,
        }


class BackfillPodAdmission:
    def __init__(self, instance: DagsterInstance, batch_api, webhook_name: str):
        self.instance = instance
        self.batch_api = batch_api
        self.webhook_name = webhook_name

    def admit(self, review: PodAdmissionReview) -> dict:
        request = review.request
        metadata = request.object.metadata
        uid = str(request.uid)
        response = {"uid": uid, "allowed": False, "status": {"message": "Pod admission denied"}}
        if request.dryRun:
            return {"uid": uid, "allowed": True}
        if (
            metadata.namespace not in (None, request.namespace)
            or metadata.labels.get(ADMISSION_ROUTE_LABEL) != self.webhook_name
            or metadata.labels.get(PROTOCOL_LABEL) != BACKFILL_STOP_PROTOCOL_VERSION
        ):
            return response
        run_id = metadata.labels.get("dagster/run-id")
        parent_id = metadata.annotations.get(DISPATCH_ID_ANNOTATION)
        owners = [
            owner for owner in metadata.owner_references if owner.kind == "Job" and owner.controller
        ]
        if not run_id or not parent_id or len(owners) != 1:
            return response
        owner = owners[0]
        if metadata.labels.get("dagster/worker-job") != owner.name:
            return response
        run = self.instance.get_run_by_id(run_id)
        backfill_id = run.tags.get(BACKFILL_ID_TAG) if run is not None else None
        if backfill_id is None:
            return response
        backfill = self.instance.get_backfill(backfill_id)
        if backfill is None or not backfill.uses_stop_protocol:
            return response
        worker_id = f"pod:{uid}"
        resource = K8sPodWorkerTarget(
            pod_name=f"dagster-worker-{uid}",
            namespace=request.namespace,
            admission_id=uid,
            job_name=owner.name,
            job_uid=owner.uid,
        )
        target = ChildWorkerTarget(parent_worker_id=parent_id, resource=resource)
        launches = self.instance.get_backfill_worker_launches(backfill_id)
        existing = next((launch for launch in launches if launch.worker_id == worker_id), None)
        if existing is None:
            parent = next((launch for launch in launches if launch.worker_id == parent_id), None)
            if (
                parent is None
                or parent.kind not in (WorkerLaunchKind.RUN, WorkerLaunchKind.STEP)
                or parent.target
                != K8sWorkerTarget(job_name=owner.name, namespace=request.namespace)
            ):
                return response
            job = self.batch_api.read_namespaced_job(owner.name, request.namespace)
            job_meta = job.metadata
            if (
                job_meta is None
                or job_meta.uid != owner.uid
                or job_meta.name != owner.name
                or job_meta.namespace != request.namespace
                or (job_meta.labels or {}).get("dagster/run-id") != run_id
                or (job_meta.labels or {}).get(ADMISSION_ROUTE_LABEL) != self.webhook_name
                or (job_meta.labels or {}).get(PROTOCOL_LABEL) != BACKFILL_STOP_PROTOCOL_VERSION
                or (job_meta.annotations or {}).get(DISPATCH_ID_ANNOTATION) != parent_id
            ):
                return response
        elif (
            existing.kind != WorkerLaunchKind.CHILD
            or existing.state != WorkerLaunchState.PENDING
            or existing.target != target
        ):
            return response
        if not self.instance.admit_backfill_worker_child(run_id, worker_id, target):
            return response
        annotations = {**metadata.annotations, ADMISSION_ID_ANNOTATION: uid}
        finalizers = list(dict.fromkeys([*metadata.finalizers, POD_FINALIZER]))
        patch = [
            {"op": "add", "path": "/metadata/name", "value": resource.pod_name},
            {"op": "add", "path": "/metadata/annotations", "value": annotations},
            {"op": "add", "path": "/metadata/finalizers", "value": finalizers},
        ]
        return {
            "uid": uid,
            "allowed": True,
            "patchType": "JSONPatch",
            "patch": base64.b64encode(json.dumps(patch).encode()).decode(),
        }
