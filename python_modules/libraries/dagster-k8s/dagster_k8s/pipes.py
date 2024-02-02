import os
import random
import string
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping, Optional, Sequence, Set, Union

import kubernetes
from dagster import (
    OpExecutionContext,
    _check as check,
)
from dagster._annotations import experimental
from dagster._core.definitions.resource_annotation import ResourceParam
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.pipes.client import (
    PipesClient,
    PipesClientCompletedInvocation,
    PipesContextInjector,
    PipesMessageReader,
    PipesParams,
)
from dagster._core.pipes.context import (
    PipesMessageHandler,
)
from dagster._core.pipes.utils import (
    PipesEnvContextInjector,
    extract_message_or_forward_to_stdout,
    open_pipes_session,
)
from dagster_pipes import (
    DAGSTER_PIPES_CONTEXT_ENV_VAR,
    DAGSTER_PIPES_MESSAGES_ENV_VAR,
    PipesDefaultMessageWriter,
    PipesExtras,
    encode_env_var,
)

from dagster_k8s.client import DEFAULT_WAIT_BETWEEN_ATTEMPTS
from dagster_k8s.utils import get_common_labels

from .client import DagsterKubernetesClient, WaitForPodState
from .models import k8s_model_from_dict, k8s_snake_case_dict


def get_pod_name(run_id: str, op_name: str):
    clean_op_name = op_name.replace("_", "-")
    suffix = "".join(random.choice(string.digits) for i in range(10))
    return f"dagster-{run_id[:18]}-{clean_op_name[:20]}-{suffix}"


DEFAULT_CONTAINER_NAME = "dagster-pipes-execution"
_NAMESPACE_SECRET_PATH = Path("/var/run/secrets/kubernetes.io/serviceaccount/namespace")
_DEV_NULL_MESSAGE_WRITER = encode_env_var({"path": "/dev/null"})


@experimental
class PipesK8sPodLogsMessageReader(PipesMessageReader):
    """Message reader that reads messages from kubernetes pod logs."""

    @contextmanager
    def read_messages(
        self,
        handler: PipesMessageHandler,
    ) -> Iterator[PipesParams]:
        self._handler = handler
        try:
            yield {PipesDefaultMessageWriter.STDIO_KEY: PipesDefaultMessageWriter.STDERR}
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

    def no_messages_debug_text(self) -> str:
        return "Attempted to read messages by extracting them from kubernetes pod logs directly."


@experimental
class _PipesK8sClient(PipesClient):
    """A pipes client for launching kubernetes pods.

    By default context is injected via environment variables and messages are parsed out of
    the pod logs, with other logs forwarded to stdout of the orchestration process.

    The first container within the containers list of the pod spec is expected (or set) to be
    the container prepared for pipes protocol communication.

    Args:
        env (Optional[Mapping[str, str]]): An optional dict of environment variables to pass to the
            subprocess.
        context_injector (Optional[PipesContextInjector]): A context injector to use to inject
            context into the k8s container process. Defaults to :py:class:`PipesEnvContextInjector`.
        message_reader (Optional[PipesMessageReader]): A message reader to use to read messages
            from the k8s container process. Defaults to :py:class:`PipesK8sPodLogsMessageReader`.
        load_incluster_config (Optional[bool]): Whether this client is expected to be running from inside
            a kubernetes cluster and should load config using ``kubernetes.config.load_incluster_config``.
            Otherwise ``kubernetes.config.load_kube_config`` is used with the kubeconfig_file argument.
            Default: None
        kubeconfig_file (Optional[str]): The value to pass as the config_file argument to
            ``kubernetes.config.load_kube_config``.
            Default: None.
        kube_context (Optional[str]): The value to pass as the context argument to
            ``kubernetes.config.load_kube_config``.
            Default: None.
        poll_interval (Optional[float]): How many seconds to wait between requests when
            polling the kubernetes API
            Default: 10.
    """

    def __init__(
        self,
        env: Optional[Mapping[str, str]] = None,
        context_injector: Optional[PipesContextInjector] = None,
        message_reader: Optional[PipesMessageReader] = None,
        load_incluster_config: Optional[bool] = None,
        kubeconfig_file: Optional[str] = None,
        kube_context: Optional[str] = None,
        poll_interval: Optional[float] = DEFAULT_WAIT_BETWEEN_ATTEMPTS,
    ):
        self.env = check.opt_mapping_param(env, "env", key_type=str, value_type=str)
        self.context_injector = (
            check.opt_inst_param(
                context_injector,
                "context_injector",
                PipesContextInjector,
            )
            or PipesEnvContextInjector()
        )
        self.message_reader = (
            check.opt_inst_param(message_reader, "message_reader", PipesMessageReader)
            or PipesK8sPodLogsMessageReader()
        )

        if load_incluster_config:
            check.invariant(
                kube_context is None and kubeconfig_file is None,
                "kubeconfig_file and kube_context should not be set when load_incluster_config is"
                " True ",
            )

        self.load_incluster_config = check.opt_bool_param(
            load_incluster_config, "load_incluster_config"
        )
        self.kubeconfig_file = check.opt_str_param(kubeconfig_file, "kubeconfig_file")
        self.kube_context = check.opt_str_param(kube_context, "kube_context")
        self.poll_interval = check.float_param(poll_interval, "poll_interval")

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def _load_k8s_config(self):
        # when nothing is specified
        if (
            self.load_incluster_config is None
            and self.kubeconfig_file is None
            and self.kube_context is None
        ):
            # check for env var that is always set by kubernetes and if present use in cluster
            if os.getenv("KUBERNETES_SERVICE_HOST"):
                kubernetes.config.load_incluster_config()
            # otherwise do default load
            else:
                kubernetes.config.load_kube_config()

        elif self.load_incluster_config:
            kubernetes.config.load_incluster_config()
        else:
            kubernetes.config.load_kube_config(
                config_file=self.kubeconfig_file,
                context=self.kube_context,
            )

    def run(
        self,
        *,
        context: OpExecutionContext,
        extras: Optional[PipesExtras] = None,
        image: Optional[str] = None,
        command: Optional[Union[str, Sequence[str]]] = None,
        namespace: Optional[str] = None,
        env: Optional[Mapping[str, str]] = None,
        base_pod_meta: Optional[Mapping[str, Any]] = None,
        base_pod_spec: Optional[Mapping[str, Any]] = None,
        ignore_containers: Optional[Set] = None,
    ) -> PipesClientCompletedInvocation:
        """Publish a kubernetes pod and wait for it to complete, enriched with the pipes protocol.

        Args:
            image (Optional[str]):
                The image to set the first container in the pod spec to use.
            command (Optional[Union[str, Sequence[str]]]):
                The command to set the first container in the pod spec to use.
            namespace (Optional[str]):
                Which kubernetes namespace to use, defaults to the current namespace if
                running inside a kubernetes cluster or falling back to "default".
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
                Keys can either snake_case or camelCase. The dagster context will be readable
                from any container within the pod, but only the first container in the
                `pod.spec.containers` will be able to communicate back to Dagster.
            extras (Optional[PipesExtras]):
                Extra values to pass along as part of the ext protocol.
            context_injector (Optional[PipesContextInjector]):
                Override the default ext protocol context injection.
            message_reader (Optional[PipesMessageReader]):
                Override the default ext protocol message reader.
            ignore_containers (Optional[Set]): Ignore certain containers from waiting for termination. Defaults to
                None.

        Returns:
            PipesClientCompletedInvocation: Wrapper containing results reported by the external
                process.
        """
        self._load_k8s_config()
        client = DagsterKubernetesClient.production_client()

        with open_pipes_session(
            context=context,
            extras=extras,
            context_injector=self.context_injector,
            message_reader=self.message_reader,
        ) as pipes_session:
            namespace = namespace or _detect_current_namespace(self.kubeconfig_file) or "default"
            pod_name = get_pod_name(context.run_id, context.op.name)
            pod_body = build_pod_body(
                pod_name=pod_name,
                image=image,
                command=command,
                env_vars={
                    **pipes_session.get_bootstrap_env_vars(),
                    **(self.env or {}),
                    **(env or {}),
                },
                base_pod_meta=base_pod_meta,
                base_pod_spec=base_pod_spec,
            )
            client.core_api.create_namespaced_pod(namespace, pod_body)
            try:
                # if were doing direct pod reading, wait for pod to start and then stream logs out
                if isinstance(self.message_reader, PipesK8sPodLogsMessageReader):
                    client.wait_for_pod(
                        pod_name,
                        namespace,
                        wait_for_state=WaitForPodState.Ready,
                        wait_time_between_attempts=self.poll_interval,
                    )
                    self.message_reader.consume_pod_logs(
                        core_api=client.core_api,
                        pod_name=pod_name,
                        namespace=namespace,
                    )

                client.wait_for_pod(
                    pod_name,
                    namespace,
                    wait_for_state=WaitForPodState.Terminated,
                    ignore_containers=ignore_containers,
                    wait_time_between_attempts=self.poll_interval,
                )
            finally:
                client.core_api.delete_namespaced_pod(pod_name, namespace)
        return PipesClientCompletedInvocation(pipes_session)


def _detect_current_namespace(
    kubeconfig_file: Optional[str], namespace_secret_path: Path = _NAMESPACE_SECRET_PATH
) -> Optional[str]:
    """Get the current in-cluster namespace when operating within the cluster.

    First attempt to read it from the `serviceaccount` secret or get it from the kubeconfig_file if it is possible.
    It will attempt to take from the active context if it exists and returns None if it does not exist.
    """
    if namespace_secret_path.exists():
        with namespace_secret_path.open() as f:
            # We only need to read the first line, this guards us against bad input.
            return f.read().strip()

    if not kubeconfig_file:
        return None

    try:
        _, active_context = kubernetes.config.list_kube_config_contexts(kubeconfig_file)
        return active_context["context"]["namespace"]
    except KeyError:
        return None


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

    containers = spec["containers"]
    init_containers = spec.get("init_containers") or []

    if "image" not in spec["containers"][0] and not image:
        raise DagsterInvariantViolationError(
            "Must specify image property or provide base_pod_spec with one set."
        )

    # We set the container name for the first container in the list if it is not set.
    # There will be a validation error below for other containers.
    if "name" not in containers[0]:
        containers[0]["name"] = DEFAULT_CONTAINER_NAME

    if not init_containers and len(containers) == 1:
        if image:
            containers[0]["image"] = image

        if command:
            containers[0]["command"] = command
    else:
        if image:
            raise DagsterInvariantViolationError(
                "Should specify 'image' via 'base_pod_spec' when specifying multiple containers"
            )

        if command:
            raise DagsterInvariantViolationError(
                "Should specify 'command' via 'base_pod_spec' when specifying multiple containers"
            )

        for container_type, containers_ in {
            "containers": containers,
            "init_containers": init_containers,
        }.items():
            for i, container in enumerate(containers_):
                for key in ["name", "image"]:
                    if key not in container:
                        raise DagsterInvariantViolationError(
                            f"Must provide base_pod_spec with {container_type}[{i}].{key} property set."
                        )

    if "env" not in containers[0]:
        containers[0]["env"] = []

    # Extend the env variables for the first container
    containers[0]["env"].extend({"name": k, "value": v} for k, v in env_vars.items())

    if DAGSTER_PIPES_CONTEXT_ENV_VAR in env_vars:
        # Add the dagster context to the remaining containers
        for container in containers[1:] + init_containers:
            if "env" not in container:
                container["env"] = []

            container["env"].append(
                {
                    "name": DAGSTER_PIPES_CONTEXT_ENV_VAR,
                    "value": env_vars[DAGSTER_PIPES_CONTEXT_ENV_VAR],
                }
            )

            for env_var in container["env"]:
                # If the user configures DAGSTER_PIPES_MESSAGES env var, don't replace it as
                # they may want to configure writing messages to a file and store it somewhere
                # or pass it within a container through a shared volume.
                if env_var["name"] == DAGSTER_PIPES_MESSAGES_ENV_VAR:
                    break
            else:
                # Default to writing messages to /dev/null within the pipes session so that
                # they don't need to do anything special if the want to read the pipes context
                # by using `with open_dagster_pipes()`.
                container["env"].append(
                    {
                        "name": DAGSTER_PIPES_MESSAGES_ENV_VAR,
                        "value": _DEV_NULL_MESSAGE_WRITER,
                    }
                )

    return k8s_model_from_dict(
        kubernetes.client.V1Pod,
        {
            "metadata": meta,
            "spec": spec,
        },
    )


PipesK8sClient = ResourceParam[_PipesK8sClient]
