import random
import string
from contextlib import contextmanager
from typing import Any, Iterator, Mapping, Optional, Sequence, Union

import kubernetes
from dagster import (
    OpExecutionContext,
    _check as check,
)
from dagster._core.definitions.resource_annotation import ResourceParam
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.ext.client import (
    ExtClient,
    ExtContextInjector,
    ExtMessageReader,
    ExtParams,
)
from dagster._core.ext.context import (
    ExtMessageHandler,
)
from dagster._core.ext.utils import (
    ExtEnvContextInjector,
    ext_protocol,
    extract_message_or_forward_to_stdout,
)
from dagster_ext import (
    ExtDefaultMessageWriter,
    ExtExtras,
)

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
        handler: ExtMessageHandler,
    ) -> Iterator[ExtParams]:
        self._handler = handler
        try:
            yield {ExtDefaultMessageWriter.STDIO_KEY: ExtDefaultMessageWriter.STDERR}
        finally:
            self._handler = None

    def consume_pod_logs(
        self,
        core_api: kubernetes.client.CoreV1Api,
        pod_name: str,
        namespace: str,
    ):
        handler = check.not_none(
            self._handler, "can only consume logs within scope of context manager"
        )
        for line in core_api.read_namespaced_pod_log(
            pod_name,
            namespace,
            follow=True,
            _preload_content=False,  # avoid JSON processing
        ).stream():
            log_chunk = line.decode("utf-8")
            for log_line in log_chunk.split("\n"):
                extract_message_or_forward_to_stdout(handler, log_line)


class _ExtK8sPod(ExtClient):
    """An ext protocol compliant resource for launching kubernetes pods.

    By default context is injected via environment variables and messages are parsed out of
    the pod logs, with other logs forwarded to stdout of the orchestration process.

    The first container within the containers list of the pod spec is expected (or set) to be
    the container prepared for ext protocol communication.

    Args:
        env (Optional[Mapping[str, str]]): An optional dict of environment variables to pass to the subprocess.
    """

    def __init__(self, env: Optional[Mapping[str, str]] = None):
        self.env = check.opt_mapping_param(env, "env", key_type=str, value_type=str)

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

        context_injector = context_injector or ExtEnvContextInjector()
        message_reader = message_reader or K8sPodLogsMessageReader()

        with ext_protocol(
            context=context,
            extras=extras,
            context_injector=context_injector,
            message_reader=message_reader,
        ) as ext_process:
            namespace = namespace or "default"
            pod_name = get_pod_name(context.run_id, context.op.name)
            pod_body = build_pod_body(
                pod_name=pod_name,
                image=image,
                command=command,
                env_vars={
                    **ext_process.get_external_process_env_vars(),
                    **(self.env or {}),
                    **(env or {}),
                },
                base_pod_meta=base_pod_meta,
                base_pod_spec=base_pod_spec,
            )
            client.core_api.create_namespaced_pod(namespace, pod_body)
            try:
                # if were doing direct pod reading, wait for pod to start and then stream logs out
                if isinstance(message_reader, K8sPodLogsMessageReader):
                    client.wait_for_pod(
                        pod_name,
                        namespace,
                        wait_for_state=WaitForPodState.Ready,
                    )
                    message_reader.consume_pod_logs(
                        core_api=client.core_api,
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

    if "restart_policy" not in spec:
        spec["restart_policy"] = "Never"
    elif spec["restart_policy"] == "Always":
        raise DagsterInvariantViolationError(
            "A restart policy of Always is not allowed, computations are expected to complete."
        )

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


ExtK8sPod = ResourceParam[_ExtK8sPod]
