import random
import string
from contextlib import contextmanager
from typing import Any, Iterator, Mapping, Optional, Sequence, Union

import kubernetes
from dagster import OpExecutionContext
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.ext.context import (
    ExtOrchestrationContext,
)
from dagster._core.ext.resource import (
    ExtContextInjector,
    ExtMessageReader,
    ExtParams,
    ExtResource,
)
from dagster._core.ext.utils import (
    ExtEnvContextInjector,
    extract_message_or_forward_to_stdout,
    io_params_as_env_vars,
)
from dagster_ext import (
    ExtDefaultMessageWriter,
    ExtExtras,
)
from pydantic import Field

from dagster_k8s.utils import get_common_labels

from .client import DagsterKubernetesClient, WaitForPodState
from .models import k8s_model_from_dict, k8s_snake_case_dict


def get_pod_name(run_id: str, op_name: str):
    clean_op_name = op_name.replace("_", "-")
    suffix = "".join(random.choice(string.digits) for i in range(10))
    return f"dagster-{run_id[:18]}-{clean_op_name[:20]}-{suffix}"


DEFAULT_CONTAINER_NAME = "dagster-ext-execution"


class K8sPodLogsMessageReader(ExtMessageReader):
    @contextmanager
    def read_messages(
        self,
        _context: ExtOrchestrationContext,
    ) -> Iterator[ExtParams]:
        yield {ExtDefaultMessageWriter.STDIO_KEY: ExtDefaultMessageWriter.STDERR}

    def consume_pod_logs(
        self,
        ext_context: ExtOrchestrationContext,
        client: DagsterKubernetesClient,
        pod_name: str,
        namespace: str,
    ):
        for line in client.core_api.read_namespaced_pod_log(
            pod_name,
            namespace,
            follow=True,
            _preload_content=False,  # avoid JSON processing
        ).stream():
            log_chunk = line.decode("utf-8")
            for log_line in log_chunk.split("\n"):
                extract_message_or_forward_to_stdout(ext_context, log_line)


class ExtK8sPod(ExtResource):
    """An ext protocol compliant resource for launching kubernetes pods.

    By default context is injected via environment variables and messages are parsed out of
    the pod logs, with other logs forwarded to stdout of the orchestration process.

    The first container within the containers list of the pod spec is expected (or set) to be
    the container prepared for ext protocol communication.
    """

    env: Optional[Mapping[str, str]] = Field(
        default=None,
        description="An optional dict of environment variables to set on the container.",
    )

    def run(
        self,
        *,
        context: OpExecutionContext,
        image: Optional[str] = None,
        command: Optional[Union[str, Sequence[str]]] = None,
        namespace: Optional[str] = None,
        env: Optional[Mapping[str, str]] = None,
        base_pod_meta: Optional[Mapping[str, Any]] = None,
        base_pod_spec: Optional[Mapping[str, Any]] = None,
        extras: Optional[ExtExtras] = None,
        context_injector: Optional[ExtContextInjector] = None,
        message_reader: Optional[ExtMessageReader] = None,
    ) -> None:
        """Publish a kubernetes pod and wait for it to complete, enriched with the ext protocol.

        Args:
            image (Optional[str]):
                The image to set the first container in the pod spec to use.
            command (Optional[Union[str, Sequence[str]]]):
                The command to set the first container in the pod spec to use.
            namespace (Optional[str]):
                Which kubernetes namespace to use, defaults to "default"
            env (Optional[Mapping[str,str]]):
                A mapping of environment variable names to values to set on the first
                container in the pod spec, on top of those configured on resource.
            base_pod_meta (Optional[Mapping[str, Any]]:
                Raw k8s config for the k8s pod's metadata
                (https://kubernetes.io/docs/reference/kubernetes-api/common-definitions/object-meta/#ObjectMeta)
                Keys can either snake_case or camelCase. The name value will be overridden.
            base_pod_spec (Optional[Mapping[str, Any]]:
                Raw k8s config for the k8s pod's pod spec
                (https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-v1/#PodSpec).
                Keys can either snake_case or camelCase.
            extras (Optional[ExtExtras]):
                Extra values to pass along as part of the ext protocol.
            context_injector (Optional[ExtContextInjector]):
                Override the default ext protocol context injection.
            message_Reader (Optional[ExtMessageReader]):
                Override the default ext protocol message reader.
        """
        client = DagsterKubernetesClient.production_client()

        ext_context = ExtOrchestrationContext(context=context, extras=extras)
        with _setup_ext_protocol(ext_context, context_injector, message_reader) as (
            protocol_env_vars,
            resolved_msg_reader,
        ):
            namespace = namespace or "default"
            pod_name = get_pod_name(context.run_id, context.op.name)
            pod_body = build_pod_body(
                pod_name=pod_name,
                image=image,
                command=command,
                env_vars={
                    **self.get_base_env(),
                    **protocol_env_vars,
                    **(self.env or {}),
                    **(env or {}),
                },
                base_pod_meta=base_pod_meta,
                base_pod_spec=base_pod_spec,
            )
            client.core_api.create_namespaced_pod(namespace, pod_body)
            try:
                # if were doing direct pod reading, wait for pod to start and then stream logs out
                if isinstance(resolved_msg_reader, K8sPodLogsMessageReader):
                    client.wait_for_pod(
                        pod_name,
                        namespace,
                        wait_for_state=WaitForPodState.Ready,
                    )
                    resolved_msg_reader.consume_pod_logs(
                        ext_context=ext_context,
                        client=client,
                        pod_name=pod_name,
                        namespace=namespace,
                    )
                else:
                    # if were not doing direct log reading, just wait for pod to finish
                    client.wait_for_pod(
                        pod_name,
                        namespace,
                        wait_for_state=WaitForPodState.Terminated,
                    )
            finally:
                client.core_api.delete_namespaced_pod(pod_name, namespace)


def build_pod_body(
    pod_name: str,
    image: Optional[str],
    command: Optional[Union[str, Sequence[str]]],
    env_vars: Mapping[str, str],
    base_pod_meta: Optional[Mapping[str, Any]],
    base_pod_spec: Optional[Mapping[str, Any]],
):
    meta = {
        **(k8s_snake_case_dict(kubernetes.client.V1ObjectMeta, base_pod_meta or {})),
        "name": pod_name,
    }
    if "labels" in meta:
        meta["labels"] = {**get_common_labels(), **meta["labels"]}
    else:
        meta["labels"] = get_common_labels()

    spec = {**k8s_snake_case_dict(kubernetes.client.V1PodSpec, base_pod_spec or {})}
    if "containers" not in spec:
        spec["containers"] = [{}]

    if "image" not in spec["containers"][0] and not image:
        raise DagsterInvariantViolationError(
            "Must specify image property or provide base_pod_spec with one set."
        )

    if "name" not in spec["containers"][0]:
        spec["containers"][0]["name"] = DEFAULT_CONTAINER_NAME

    if image:
        spec["containers"][0]["image"] = image

    if command:
        spec["containers"][0]["command"] = command

    if "env" not in spec["containers"][0]:
        spec["containers"][0]["env"] = []

    spec["containers"][0]["env"].extend({"name": k, "value": v} for k, v in env_vars.items())

    return k8s_model_from_dict(
        kubernetes.client.V1Pod,
        {
            "metadata": meta,
            "spec": spec,
        },
    )


@contextmanager
def _setup_ext_protocol(
    external_context: ExtOrchestrationContext,
    context_injector: Optional[ExtContextInjector],
    message_reader: Optional[ExtMessageReader],
):
    context_injector = context_injector or ExtEnvContextInjector()
    message_reader = message_reader or K8sPodLogsMessageReader()

    with context_injector.inject_context(
        external_context,
    ) as ci_params, message_reader.read_messages(
        external_context,
    ) as mr_params:
        protocol_envs = io_params_as_env_vars(ci_params, mr_params)
        yield protocol_envs, message_reader
