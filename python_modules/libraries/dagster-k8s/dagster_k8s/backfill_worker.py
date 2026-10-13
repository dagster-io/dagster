"""Kubernetes identity and lifecycle evidence for backfill worker receipts."""

from typing import Literal

import dagster._check as check
from dagster._core.storage.tags import BACKFILL_STOP_PROTOCOL_VERSION
from pydantic import BaseModel, ConfigDict, Field

from dagster_k8s.backfill_admission import (
    ADMISSION_ROUTE_LABEL,
    WEBHOOK_CONTRACT_ANNOTATION,
    OwnerReference,
)


class PodIdentity(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    name: str
    namespace: str
    uid: str = Field(min_length=1)
    resource_version: str = Field(min_length=1, alias="resourceVersion")
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)
    finalizers: list[str] = Field(default_factory=list)
    deletion_timestamp: str | None = Field(default=None, alias="deletionTimestamp")
    owners: list[OwnerReference] = Field(default_factory=list, alias="ownerReferences")


class Container(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str


class PodSpecification(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    containers: list[Container] = Field(min_length=1)
    init_containers: list[Container] = Field(default_factory=list, alias="initContainers")
    ephemeral_containers: list[Container] = Field(default_factory=list, alias="ephemeralContainers")
    node_name: str | None = Field(default=None, alias="nodeName")


class ContainerState(BaseModel):
    model_config = ConfigDict(extra="ignore")
    terminated: dict | None = None


class ContainerStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    state: ContainerState


class PodStatus(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    phase: str | None = None
    containers: list[ContainerStatus] = Field(default_factory=list, alias="containerStatuses")
    init_containers: list[ContainerStatus] = Field(
        default_factory=list, alias="initContainerStatuses"
    )
    ephemeral_containers: list[ContainerStatus] = Field(
        default_factory=list, alias="ephemeralContainerStatuses"
    )


class PodSnapshot(BaseModel):
    model_config = ConfigDict(extra="ignore")
    metadata: PodIdentity
    spec: PodSpecification
    status: PodStatus = Field(default_factory=PodStatus)

    @property
    def all_containers_terminated(self) -> bool:
        expected = {
            container.name
            for container in (
                *self.spec.containers,
                *self.spec.init_containers,
                *self.spec.ephemeral_containers,
            )
        }
        states = {
            container.name: container.state
            for container in (
                *self.status.containers,
                *self.status.init_containers,
                *self.status.ephemeral_containers,
            )
        }
        return expected == states.keys() and all(
            state.terminated is not None for state in states.values()
        )


class Selector(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    labels: dict[str, str] = Field(default_factory=dict, alias="matchLabels")
    expressions: list[dict] = Field(default_factory=list, alias="matchExpressions")


class Rule(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    operations: list[str]
    groups: list[str] = Field(alias="apiGroups")
    versions: list[str] = Field(alias="apiVersions")
    resources: list[str]
    scope: Literal["Namespaced"]


class ServiceReference(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = Field(min_length=1)
    namespace: str = Field(min_length=1)
    path: Literal["/admit"]


class ClientConfiguration(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    service: ServiceReference
    ca_bundle: str = Field(min_length=1, alias="caBundle")


class Webhook(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    failure_policy: Literal["Fail"] = Field(alias="failurePolicy")
    side_effects: Literal["NoneOnDryRun"] = Field(alias="sideEffects")
    reinvocation_policy: Literal["Never"] = Field(alias="reinvocationPolicy")
    review_versions: list[str] = Field(alias="admissionReviewVersions")
    rules: list[Rule]
    selector: Selector = Field(alias="objectSelector")
    namespace_selector: Selector | None = Field(default=None, alias="namespaceSelector")
    client: ClientConfiguration = Field(alias="clientConfig")
    conditions: list[dict] = Field(default_factory=list, alias="matchConditions", max_length=0)


class ConfigurationMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    annotations: dict[str, str]


class WebhookConfiguration(BaseModel):
    model_config = ConfigDict(extra="ignore")
    metadata: ConfigurationMetadata
    webhooks: list[Webhook]

    def require_binding(self, name: str) -> None:
        check.invariant(
            self.metadata.name == name
            and self.metadata.annotations.get(WEBHOOK_CONTRACT_ANNOTATION)
            == BACKFILL_STOP_PROTOCOL_VERSION
            and len(self.webhooks) == 1,
            "Backfill Pod admission configuration has no matching protocol contract.",
        )
        hook = self.webhooks[0]
        check.invariant(
            hook.review_versions == ["v1"]
            and hook.selector.labels == {ADMISSION_ROUTE_LABEL: name}
            and not hook.selector.expressions
            and (
                hook.namespace_selector is None
                or (not hook.namespace_selector.labels and not hook.namespace_selector.expressions)
            )
            and len(hook.rules) == 1
            and hook.rules[0].operations == ["CREATE"]
            and hook.rules[0].groups == [""]
            and hook.rules[0].versions == ["v1"]
            and hook.rules[0].resources == ["pods"],
            "Backfill Pod admission must fail closed for every routed Pod CREATE.",
        )
