import logging
import time
from collections import defaultdict
from collections.abc import Collection, Mapping
from contextlib import contextmanager
from typing import Any, NamedTuple

import kubernetes
import kubernetes.client as client
from dagster import (
    Array,
    Field,
    IntSource,
    Map,
    Noneable,
    Permissive,
    Shape,
    StringSource,
    _check as check,
)
from dagster._serdes import ConfigurableClass, serialize_value
from dagster._serdes.config_class import ConfigurableClassData
from dagster._utils.merger import merge_dicts
from dagster_cloud_cli.core.workspace import CodeLocationDeployData
from dagster_k8s.client import PatchedApiClient
from dagster_k8s.container_context import K8sContainerContext
from dagster_k8s.job import UserDefinedDagsterK8sConfig
from dagster_k8s.models import k8s_snake_case_dict
from dagster_k8s.utils import load_kubernetes_config
from kubernetes.client.rest import ApiException
from typing_extensions import Self

from dagster_cloud.api.dagster_cloud_api import UserCodeDeploymentType
from dagster_cloud.constants import RESERVED_ENV_VAR_NAMES
from dagster_cloud.execution.cloud_run_launcher.k8s import CloudK8sRunLauncher
from dagster_cloud.execution.monitoring import CloudContainerResourceLimits
from dagster_cloud.workspace.kubernetes.utils import (
    DEFS_STATE_CONFIG_MAP_NAME_PREFIX,
    SERVER_SPEC_VERSION_LABEL_KEY,
    SERVER_SPEC_VERSION_V2,
    construct_code_location_deployment,
    construct_code_location_service,
    construct_defs_state_config_map,
    defs_state_config_map_name,
    get_deployment_failure_debug_info,
    unique_k8s_resource_name,
    wait_for_deployment_complete,
)
from dagster_cloud.workspace.user_code_launcher import (
    DEFAULT_SERVER_PROCESS_STARTUP_TIMEOUT,
    SHARED_USER_CODE_LAUNCHER_CONFIG,
    DagsterCloudGrpcServer,
    DagsterCloudUserCodeLauncher,
    ServerEndpoint,
    UserCodeLauncherEntry,
)
from dagster_cloud.workspace.user_code_launcher.user_code_launcher import DeploymentAndLocation
from dagster_cloud.workspace.user_code_launcher.utils import (
    deterministic_label_for_location,
    get_code_server_port,
)

DEFAULT_DEPLOYMENT_STARTUP_TIMEOUT = 300
DEFAULT_IMAGE_PULL_GRACE_PERIOD = 30

# Orphan defs-state ConfigMaps younger than this are skipped by the GC sweep:
# spinup deliberately creates the CM before its Deployment, so a concurrent
# sweep could otherwise delete a CM whose Deployment is about to appear. Must
# comfortably exceed the CM-create → Deployment-create window (one API call).
ORPHAN_DEFS_STATE_CONFIG_MAP_GRACE_PERIOD_SECONDS = 300

from dagster_cloud.workspace.config_schema.kubernetes import SHARED_K8S_CONFIG


class K8sHandle(NamedTuple):
    namespace: str
    name: str
    labels: Mapping[str, str]
    creation_timestamp: float | None

    def __str__(self):
        return f"{self.namespace}/{self.name}"


class K8sUserCodeLauncher(DagsterCloudUserCodeLauncher[K8sHandle], ConfigurableClass):
    def __init__(
        self,
        dagster_home,
        instance_config_map,
        inst_data=None,
        namespace=None,
        kubeconfig_file=None,
        k8s_api_ssl_ca_cert_file=None,
        pull_policy=None,
        env_config_maps=None,
        env_secrets=None,
        env_vars=None,
        service_account_name=None,
        volume_mounts=None,
        volumes=None,
        image_pull_secrets=None,
        deployment_startup_timeout=None,
        image_pull_grace_period=None,
        labels=None,
        resources=None,
        scheduler_name=None,
        server_k8s_config=None,
        run_k8s_config=None,
        k8s_apps_api_client=None,
        k8s_core_api_client=None,
        security_context=None,
        only_allow_user_defined_k8s_config_fields=None,
        only_allow_user_defined_env_vars=None,
        fail_pod_on_run_failure=None,
        **kwargs,
    ):
        self._inst_data = inst_data
        self._logger = logging.getLogger("K8sUserCodeLauncher")
        self._dagster_home = check.str_param(dagster_home, "dagster_home")
        self._instance_config_map = check.str_param(instance_config_map, "instance_config_map")
        self._namespace = namespace

        self._pull_policy = pull_policy
        self._env_config_maps = check.opt_list_param(
            env_config_maps, "env_config_maps", of_type=str
        )
        self._env_secrets = check.opt_list_param(env_secrets, "env_secrets", of_type=str)
        self._env_vars = check.opt_list_param(env_vars, "env_vars", of_type=str)
        self._service_account_name = check.str_param(service_account_name, "service_account_name")
        self._volume_mounts = [
            k8s_snake_case_dict(kubernetes.client.V1VolumeMount, mount)
            for mount in check.opt_list_param(volume_mounts, "volume_mounts")
        ]
        self._volumes = [
            k8s_snake_case_dict(kubernetes.client.V1Volume, volume)
            for volume in check.opt_list_param(volumes, "volumes")
        ]
        self._image_pull_secrets = check.opt_list_param(
            image_pull_secrets, "image_pull_secrets", of_type=dict
        )
        self._deployment_startup_timeout = check.opt_int_param(
            deployment_startup_timeout,
            "deployment_startup_timeout",
            DEFAULT_DEPLOYMENT_STARTUP_TIMEOUT,
        )
        self._image_pull_grace_period = check.opt_int_param(
            image_pull_grace_period,
            "image_pull_grace_period",
            DEFAULT_IMAGE_PULL_GRACE_PERIOD,
        )
        self._labels = check.opt_dict_param(labels, "labels", key_type=str, value_type=str)
        self._resources = check.opt_dict_param(resources, "resources", key_type=str)

        self._scheduler_name = check.opt_str_param(scheduler_name, "scheduler_name")

        self._server_k8s_config = check.opt_dict_param(server_k8s_config, "server_k8s_config")
        self._run_k8s_config = check.opt_dict_param(run_k8s_config, "run_k8s_config")

        load_kubernetes_config(
            load_incluster_config=not kubeconfig_file,
            kubeconfig_file=kubeconfig_file,
            k8s_api_ssl_ca_cert_file=k8s_api_ssl_ca_cert_file,
        )

        self._k8s_apps_api_client = k8s_apps_api_client
        self._k8s_core_api_client = k8s_core_api_client

        self._security_context = security_context

        if only_allow_user_defined_k8s_config_fields is not None:
            # Dagster Cloud always sets some environment variables whenever it launched code.
            # If only_allow_user_defined_k8s_config_fields is being used to lock down which
            # k8s config can be set by the control plane and "container_config.env" is not
            # in that allowlist, add it to that allowlist so that we don't fail every pod that
            # is launched, but restrict the set of env vars that can be configured to only
            # a fixed set of known Dagster Cloud environment variables, defined in code.

            if not only_allow_user_defined_k8s_config_fields.get("container_config", {}).get("env"):
                only_allow_user_defined_k8s_config_fields = {
                    **only_allow_user_defined_k8s_config_fields,
                    "container_config": {
                        **only_allow_user_defined_k8s_config_fields.get("container_config", {}),
                        "env": True,
                    },
                }

                if only_allow_user_defined_env_vars is None:
                    only_allow_user_defined_env_vars = []

        if only_allow_user_defined_env_vars is not None:
            only_allow_user_defined_env_vars = (
                only_allow_user_defined_env_vars + RESERVED_ENV_VAR_NAMES
            )

        self._only_allow_user_defined_k8s_config_fields = only_allow_user_defined_k8s_config_fields
        self._only_allow_user_defined_env_vars = only_allow_user_defined_env_vars

        super().__init__(**kwargs)

        self._launcher = CloudK8sRunLauncher(
            dagster_home=self._dagster_home,
            instance_config_map=self._instance_config_map,
            postgres_password_secret=None,
            job_image=None,
            image_pull_policy=self._pull_policy,
            image_pull_secrets=self._image_pull_secrets,
            service_account_name=self._service_account_name,
            env_config_maps=self._env_config_maps,
            env_secrets=self._env_secrets,
            env_vars=self._env_vars,
            job_namespace=self._namespace,
            volume_mounts=self._volume_mounts,
            volumes=self._volumes,
            labels=self._labels,
            resources=self._resources,
            scheduler_name=self._scheduler_name,
            run_k8s_config=self._run_k8s_config,
            fail_pod_on_run_failure=fail_pod_on_run_failure,
            kubeconfig_file=kubeconfig_file,
            k8s_api_ssl_ca_cert_file=k8s_api_ssl_ca_cert_file,
            load_incluster_config=not kubeconfig_file,
            security_context=self._security_context,
            # leave out the code server specific fields from only_allow_user_defined_k8s_config_fields
            only_allow_user_defined_k8s_config_fields=(
                {
                    key: val
                    for key, val in only_allow_user_defined_k8s_config_fields.items()
                    if key not in {"service_metadata", "deployment_metadata", "service_spec_config"}
                }
                if only_allow_user_defined_k8s_config_fields
                else only_allow_user_defined_k8s_config_fields
            ),
            only_allow_user_defined_env_vars=self._only_allow_user_defined_env_vars,
        )

        # mutable set of observed namespaces to assist with cleanup
        self._used_namespaces: dict[tuple[str, str], set[str]] = defaultdict(set)

    @property
    def requires_images(self):
        return True

    def register_instance(self, instance):
        super().register_instance(instance)
        self._launcher.register_instance(instance)

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        container_context_config = SHARED_K8S_CONFIG.copy()
        del container_context_config["image_pull_policy"]  # uses 'pull_policy'
        del container_context_config["namespace"]  # default is different

        return merge_dicts(
            container_context_config,
            {
                "dagster_home": Field(StringSource, is_required=True),
                "instance_config_map": Field(StringSource, is_required=True),
                "kubeconfig_file": Field(StringSource, is_required=False),
                "k8s_api_ssl_ca_cert_file": Field(
                    StringSource,
                    is_required=False,
                    description=(
                        "Path to a custom CA bundle file for TLS verification when connecting to "
                        "the Kubernetes API. Use this in enterprise environments with custom CA "
                        "chains where the default service account CA cert is not sufficient."
                    ),
                ),
                "deployment_startup_timeout": Field(
                    IntSource,
                    is_required=False,
                    default_value=DEFAULT_DEPLOYMENT_STARTUP_TIMEOUT,
                    description=(
                        "Timeout when creating a new Kubernetes deployment for a code server"
                    ),
                ),
                "server_process_startup_timeout": Field(
                    IntSource,
                    is_required=False,
                    default_value=DEFAULT_SERVER_PROCESS_STARTUP_TIMEOUT,
                    description=(
                        "Timeout when waiting for a code server to be ready after it is created"
                    ),
                ),
                "image_pull_grace_period": Field(
                    IntSource,
                    is_required=False,
                    default_value=DEFAULT_IMAGE_PULL_GRACE_PERIOD,
                ),
                "pull_policy": Field(
                    Noneable(StringSource),
                    is_required=False,
                    description="Image pull policy to set on launched Pods.",
                ),
                "namespace": Field(StringSource, is_required=False, default_value="default"),
                "scheduler_name": Field(StringSource, is_required=False),
                "run_k8s_config": Field(
                    Shape(
                        {
                            "container_config": Permissive(),
                            "pod_template_spec_metadata": Permissive(),
                            "pod_spec_config": Permissive(),
                            "job_config": Permissive(),
                            "job_metadata": Permissive(),
                            "job_spec_config": Permissive(),
                        }
                    ),
                    is_required=False,
                    description="Raw Kubernetes configuration for launched runs.",
                ),
                "fail_pod_on_run_failure": Field(
                    bool,
                    is_required=False,
                    description=(
                        "Whether the launched Kubernetes Jobs and Pods should fail if the Dagster"
                        " run fails"
                    ),
                ),
                "server_k8s_config": Field(
                    Shape(
                        {
                            "container_config": Permissive(),
                            "pod_spec_config": Permissive(),
                            "pod_template_spec_metadata": Permissive(),
                            "deployment_metadata": Permissive(),
                            "service_metadata": Permissive(),
                            "service_spec_config": Permissive(),
                        }
                    ),
                    is_required=False,
                    description="Raw Kubernetes configuration for launched code servers.",
                ),
                "only_allow_user_defined_k8s_config_fields": Field(
                    Shape(
                        {
                            "container_config": Field(
                                Map(key_type=str, inner_type=bool), is_required=False
                            ),
                            "pod_spec_config": Field(
                                Map(key_type=str, inner_type=bool), is_required=False
                            ),
                            "pod_template_spec_metadata": Field(
                                Map(key_type=str, inner_type=bool), is_required=False
                            ),
                            "job_metadata": Field(
                                Map(key_type=str, inner_type=bool), is_required=False
                            ),
                            "job_spec_config": Field(
                                Map(key_type=str, inner_type=bool), is_required=False
                            ),
                            "deployment_metadata": Field(
                                Map(key_type=str, inner_type=bool), is_required=False
                            ),
                            "service_metadata": Field(
                                Map(key_type=str, inner_type=bool), is_required=False
                            ),
                            "service_spec_config": Field(
                                Map(key_type=str, inner_type=bool), is_required=False
                            ),
                            "namespace": Field(bool, is_required=False),
                        }
                    ),
                    is_required=False,
                    description="Dictionary of fields that are allowed to be configured on a "
                    "per-run or per-code-location basis - e.g. using tags on the run. "
                    "Can be used to prevent user code or the Dagster Cloud control plane from "
                    "being able to set arbitrary kubernetes config on the resources launched "
                    "by the agent.",
                ),
                "only_allow_user_defined_env_vars": Field(
                    Array(str),
                    is_required=False,
                    description="List of environment variable names that are allowed to be set on "
                    "a per-run or per-code-location basis - e.g. using tags on the run. ",
                ),
                "code_server_metrics": Field(
                    {"enabled": Field(bool, is_required=False, default_value=False)},
                    is_required=False,
                ),
                "agent_metrics": Field(
                    {"enabled": Field(bool, is_required=False, default_value=False)},
                    is_required=False,
                ),
            },
            SHARED_USER_CODE_LAUNCHER_CONFIG,
        )

    @property
    def user_code_deployment_type(self) -> UserCodeDeploymentType:
        return UserCodeDeploymentType.K8S

    @classmethod
    def from_config_value(cls, inst_data: ConfigurableClassData, config_value: Any) -> Self:
        return cls(
            inst_data=inst_data,
            **config_value,
        )

    def _get_core_api_client(self):
        return (
            self._k8s_core_api_client
            if self._k8s_core_api_client
            else client.CoreV1Api(api_client=PatchedApiClient())
        )

    @contextmanager
    def _get_apps_api_instance(self):
        if self._k8s_apps_api_client:
            yield self._k8s_apps_api_client
            return

        with PatchedApiClient() as api_client:
            yield client.AppsV1Api(api_client)

    def _resolve_container_context(self, metadata: CodeLocationDeployData) -> K8sContainerContext:
        user_defined_container_context = K8sContainerContext.create_from_config(
            metadata.container_context
        ).validate_user_k8s_config_for_code_server(
            self._only_allow_user_defined_k8s_config_fields, self._only_allow_user_defined_env_vars
        )
        return K8sContainerContext(
            image_pull_policy=self._pull_policy,
            image_pull_secrets=self._image_pull_secrets,
            service_account_name=self._service_account_name,
            env_config_maps=self._env_config_maps,
            env_secrets=self._env_secrets,
            env_vars=self._env_vars
            + [f"{k}={v}" for k, v in (metadata.cloud_context_env or {}).items()],
            volume_mounts=self._volume_mounts,
            volumes=self._volumes,
            labels=self._labels,
            namespace=self._namespace,
            resources=self._resources,
            scheduler_name=self._scheduler_name,
            security_context=self._security_context,
            server_k8s_config=UserDefinedDagsterK8sConfig.from_dict(self._server_k8s_config),
            run_k8s_config=UserDefinedDagsterK8sConfig.from_dict(self._run_k8s_config),
        ).merge(user_defined_container_context)

    def get_code_server_resource_limits(
        self, deployment_name: str, location_name: str
    ) -> CloudContainerResourceLimits:
        metadata = self._actual_entries[(deployment_name, location_name)].code_location_deploy_data
        k8s_container_context = metadata.container_context.get("k8s", {})
        resources = (
            k8s_container_context.get("server_k8s_config", {})
            .get("container_config", {})
            .get("resources", {})
        )
        if not resources:
            resources = k8s_container_context.get("resources", {})

        self._logger.info(
            f"Getting resource limits for deployment {deployment_name} in location {location_name}: {resources}"
        )
        return {
            "k8s": {
                "cpu_limit": resources.get("limits", {}).get("cpu"),
                "cpu_request": resources.get("requests", {}).get("cpu"),
                "memory_limit": resources.get("limits", {}).get("memory"),
                "memory_request": resources.get("requests", {}).get("memory"),
            }
        }

    def _supports_defs_state_config_map(
        self, container_context: K8sContainerContext, metadata: CodeLocationDeployData
    ) -> bool:
        """N=1, non-pex gate for the per-location defs_state override ConfigMap.

        Multi-replica configurations stay on full destroy-and-recreate (no
        coordinated multi-replica fan-out yet). Multipex pods get pins via
        CreatePexServerArgs at spawn time, not from a CM-mounted file.
        """
        if metadata.pex_metadata is not None:
            return False
        rc = container_context.server_replica_count
        return rc is None or rc == 1

    def _create_or_replace_defs_state_config_map(
        self,
        deployment_name: str,
        location_name: str,
        k8s_deployment_name: str,
        namespace: str,
        *,
        serialized_defs_state_info: str,
        server_timestamp: float,
    ) -> None:
        """Idempotent upsert of the per-incarnation defs-state ConfigMap.

        The name is deterministic from ``k8s_deployment_name``, so a repeat
        write for the same incarnation (e.g. an in-place pin reload) hits 409
        and we ``replace``. Always-write semantics: the CM tracks the pin we
        last asked the server to hold, so a racing pod respawn boots correctly.
        """
        body = construct_defs_state_config_map(
            deployment_name,
            location_name,
            k8s_deployment_name,
            self._instance,
            server_timestamp,
            serialized_defs_state_info,
        )
        core = self._get_core_api_client()
        try:
            core.create_namespaced_config_map(namespace, body)
        except ApiException as e:
            if e.status != 409:
                raise
            core.replace_namespaced_config_map(
                defs_state_config_map_name(k8s_deployment_name),
                namespace,
                body,
            )

    def _start_new_server_spinup(
        self,
        deployment_name: str,
        location_name: str,
        desired_entry: UserCodeLauncherEntry,
    ) -> DagsterCloudGrpcServer:
        metadata = desired_entry.code_location_deploy_data

        args = metadata.get_grpc_server_command(
            metrics_enabled=self._instance.user_code_launcher.code_server_metrics_enabled
        )

        resource_name = unique_k8s_resource_name(deployment_name, location_name)

        container_context = self._resolve_container_context(metadata)

        mount_defs_state = self._supports_defs_state_config_map(container_context, metadata)

        if mount_defs_state:
            # Create the CM BEFORE the Deployment so a racing new pod sees the
            # current pin at mount time. Allowed to be ahead of the running
            # server's in-memory state — that's the safety property.
            self._create_or_replace_defs_state_config_map(
                deployment_name,
                location_name,
                resource_name,
                check.not_none(container_context.namespace),
                serialized_defs_state_info=(
                    serialize_value(metadata.defs_state_info) if metadata.defs_state_info else ""
                ),
                server_timestamp=desired_entry.update_timestamp,
            )

        deployment_reponse = None

        try:
            with self._get_apps_api_instance() as api_instance:
                deployment_reponse = api_instance.create_namespaced_deployment(
                    namespace=container_context.namespace,
                    body=construct_code_location_deployment(
                        self._instance,
                        deployment_name=deployment_name,
                        location_name=location_name,
                        k8s_deployment_name=resource_name,
                        metadata=metadata,
                        container_context=container_context,
                        args=args,
                        server_timestamp=desired_entry.update_timestamp,
                        server_replica_count=container_context.server_replica_count,
                        mount_defs_state_config_map=mount_defs_state,
                    ),
                )
            self._logger.info(
                f"Created deployment {deployment_reponse.metadata.name} in namespace {container_context.namespace}"
            )
        except ApiException as e:
            self._logger.error(
                f"Exception when calling AppsV1Api->create_namespaced_deployment: {e}\n"
            )
            raise e

        namespace = check.not_none(container_context.namespace)

        self._used_namespaces[(deployment_name, location_name)].add(namespace)

        try:
            service_response = self._get_core_api_client().create_namespaced_service(
                namespace,
                construct_code_location_service(
                    deployment_name,
                    location_name,
                    resource_name,
                    container_context,
                    self._instance,
                    server_timestamp=desired_entry.update_timestamp,
                ),
            )
            self._logger.info(
                f"Created service {service_response.metadata.name} in namespace {namespace}"
            )
        except ApiException as e:
            self._logger.error(
                f"Exception when calling AppsV1Api->create_namespaced_service: {e}\n"
            )
            raise e

        # use namespace scoped host name
        host = f"{resource_name}.{namespace}"

        endpoint = ServerEndpoint(
            host=host,
            port=get_code_server_port(),
            socket=None,
        )

        return DagsterCloudGrpcServer(
            K8sHandle(
                namespace=namespace,
                name=resource_name,
                labels=deployment_reponse.metadata.labels,
                creation_timestamp=deployment_reponse.metadata.creation_timestamp.timestamp()
                if deployment_reponse.metadata.creation_timestamp
                else None,
            ),
            endpoint,
            metadata,
        )

    def _get_timeout_debug_info(
        self,
        server_handle,
    ):
        core_api = self._get_core_api_client()
        k8s_deployment_name = server_handle.name
        namespace = server_handle.namespace

        pod_list = core_api.list_namespaced_pod(
            namespace, label_selector=f"user-deployment={k8s_deployment_name}"
        ).items

        with self._get_apps_api_instance() as apps_api_client:
            return get_deployment_failure_debug_info(
                k8s_deployment_name,
                namespace,
                core_api,
                pod_list,
                self._logger,
                apps_api_client=apps_api_client,
            )

    @property
    def _default_sentinel_dir(self) -> str:
        return "/tmp"

    async def _wait_for_new_server_ready(  # ty: ignore[invalid-method-override], fix me!
        self,
        deployment_name: str,
        location_name: str,
        user_code_launcher_entry: UserCodeLauncherEntry,
        server_handle: K8sHandle,
        server_endpoint: ServerEndpoint,
    ) -> None:
        metadata = user_code_launcher_entry.code_location_deploy_data

        await wait_for_deployment_complete(
            server_handle.name,
            server_handle.namespace,
            self._logger,
            location_name,
            metadata,
            timeout=self._deployment_startup_timeout,
            image_pull_grace_period=self._image_pull_grace_period,
            core_api=self._get_core_api_client(),
        )

        await self._wait_for_dagster_server_process(
            client=server_endpoint.create_client(),
            timeout=self._server_process_startup_timeout,
            get_timeout_debug_info=lambda: self._get_timeout_debug_info(server_handle),
        )

    def _get_standalone_dagster_server_handles_for_location(
        self,
        deployment_name: str,
        location_name: str,
    ) -> Collection[K8sHandle]:
        handles = []
        namespaces_to_search = self._used_namespaces.get(
            (deployment_name, location_name),
            [self._namespace],
        )
        with self._get_apps_api_instance() as api_instance:
            for namespace in namespaces_to_search:
                deployments = api_instance.list_namespaced_deployment(
                    namespace,
                    label_selector=(
                        f"location_hash={deterministic_label_for_location(deployment_name, location_name)},agent_id={self._instance.instance_uuid}"
                    ),
                ).items
                handles.extend(
                    K8sHandle(
                        namespace=namespace,  # ty: ignore[invalid-argument-type]
                        name=deployment.metadata.name,
                        labels=deployment.metadata.labels,
                        creation_timestamp=deployment.metadata.creation_timestamp.timestamp()
                        if deployment.metadata.creation_timestamp
                        else None,
                    )
                    for deployment in deployments
                )

        return handles

    def _known_namespaces(self) -> set[str]:
        namespaces: set[str] = set()
        if self._namespace:
            namespaces.add(self._namespace)
        for namespace_items in self._used_namespaces.values():
            for namespace in namespace_items:
                namespaces.add(namespace)
        return namespaces

    def _list_server_handles(self) -> list[K8sHandle]:
        namespaces = self._known_namespaces()
        handles: list[K8sHandle] = []
        with self._get_apps_api_instance() as api_instance:
            for namespace in namespaces:
                deployments = api_instance.list_namespaced_deployment(
                    namespace,
                    label_selector="managed_by=K8sUserCodeLauncher",
                ).items
                handles.extend(
                    K8sHandle(
                        namespace,
                        deployment.metadata.name,
                        deployment.metadata.labels,
                        deployment.metadata.creation_timestamp.timestamp()
                        if deployment.metadata.creation_timestamp
                        else None,
                    )
                    for deployment in deployments
                )
        self._logger.info(f"Listing server handles: {handles}")
        return handles

    def _cleanup_orphan_defs_state_config_maps(self) -> None:
        """Delete defs-state ConfigMaps whose owning Deployment incarnation is gone.

        CMs are named per incarnation (``defs_state_config_map_name(handle.name)``),
        so a CM is an orphan iff no live managed Deployment's derived CM name
        matches it. Sources of orphans:
        - Agent crashed between CM-create and Deployment-create (the CM is
          deliberately written first).
        - Operator manually `kubectl delete`'d a Deployment without deleting
          its CM (the normal launcher path deletes the CM alongside the
          Deployment via ``_remove_server_handle``).

        Filtered by ``managed_by=K8sUserCodeLauncher`` AND the
        ``DEFS_STATE_CONFIG_MAP_NAME_PREFIX`` prefix as belt-and-suspenders
        so we never touch a user-owned ConfigMap. CMs younger than the grace
        period are skipped: spinup creates the CM *before* its Deployment, so
        a concurrent sweep would otherwise see a just-created CM as orphaned.
        """
        # Build the set of CM names owned by still-live managed Deployments.
        # Use the same listing the per-server cleanup uses so we agree with it
        # on what "live" means.
        try:
            live_handles = self._list_server_handles()
        except Exception:
            self._logger.exception("Failed to list server handles during orphan ConfigMap cleanup.")
            return
        live_cm_names = {defs_state_config_map_name(h.name) for h in live_handles}

        core = self._get_core_api_client()
        now = time.time()
        for namespace in self._known_namespaces():
            try:
                cms = core.list_namespaced_config_map(
                    namespace, label_selector="managed_by=K8sUserCodeLauncher"
                ).items
            except ApiException:
                self._logger.exception(
                    f"Failed to list defs-state ConfigMaps in namespace {namespace} during cleanup."
                )
                continue
            for cm in cms:
                name = cm.metadata.name
                if not name.startswith(DEFS_STATE_CONFIG_MAP_NAME_PREFIX):
                    # Not one of ours; defensive — selector should already exclude these.
                    continue
                if name in live_cm_names:
                    continue
                creation_timestamp = cm.metadata.creation_timestamp
                if (
                    creation_timestamp is not None
                    and now - creation_timestamp.timestamp()
                    < ORPHAN_DEFS_STATE_CONFIG_MAP_GRACE_PERIOD_SECONDS
                ):
                    # Too young to judge: its Deployment may not exist YET.
                    continue
                try:
                    core.delete_namespaced_config_map(name, namespace)
                    self._logger.info(
                        f"Cleaned up orphan defs-state ConfigMap {name} in namespace {namespace}."
                    )
                except ApiException as e:
                    if e.status != 404:
                        self._logger.exception(
                            f"Failed to delete orphan defs-state ConfigMap {name} in namespace {namespace}."
                        )

    def _graceful_cleanup_servers(self, include_own_servers: bool) -> None:
        super()._graceful_cleanup_servers(include_own_servers=include_own_servers)
        try:
            self._cleanup_orphan_defs_state_config_maps()
        except Exception:
            self._logger.exception("Failed to clean up orphan defs-state ConfigMaps.")

    def get_agent_id_for_server(self, handle: K8sHandle) -> str | None:
        return handle.labels.get("agent_id")

    def get_server_create_timestamp(self, handle: K8sHandle) -> float | None:
        return handle.creation_timestamp

    def supports_in_place_pin_reload(
        self,
        key: DeploymentAndLocation,
        desired_entry: UserCodeLauncherEntry,
    ) -> bool:
        """Fast-path the defs_state_info-only reload via gRPC ReloadCodeWithState.

        Only safe when the running Deployment was created with v2 spec
        (ConfigMap mount + DAGSTER_DEFS_STATE_INFO_OVERRIDE_PATH env var) so
        that a platform-induced pod restart re-reads the current pin from
        etcd, not from stale spec args. Legacy (pre-v2) Deployments stay on
        destroy-and-recreate forever, or until the customer's next code push
        naturally rolls them to v2.
        """
        metadata = desired_entry.code_location_deploy_data
        container_context = self._resolve_container_context(metadata)
        if not self._supports_defs_state_config_map(container_context, metadata):
            return False
        with self._grpc_servers_lock:
            server = self._grpc_servers.get(key)
        if not isinstance(server, DagsterCloudGrpcServer):
            return False
        labels = getattr(server.server_handle, "labels", None) or {}
        return labels.get(SERVER_SPEC_VERSION_LABEL_KEY) == SERVER_SPEC_VERSION_V2

    def _reload_pin_in_place(
        self,
        key: DeploymentAndLocation,
        desired_entry: UserCodeLauncherEntry,
    ) -> None:
        """Write the ConfigMap first, then delegate to the base RPC path.

        Order matters: if a pod restart races with the in-place reload, the
        new pod mounts the *latest* ConfigMap contents and boots correct.
        The base class advances ``_actual_entries`` only on RPC success
        (user_code_launcher.py: ``_actual_entries[key] = desired_entry``
        runs AFTER the gRPC reply); if the RPC fails, the cache does not
        advance and the next reconcile tick retries. The ConfigMap being
        ahead of in-memory state is the safety property — that's the whole
        point.

        The CM is written for the *running* incarnation (named from the
        cached server handle), so the update targets exactly the Deployment
        whose pod mounts it.

        Known residual window: a brand-new pod mounts the CM fresh from etcd,
        but a container restart *within* an existing pod may read the
        pre-update projection for up to the kubelet sync period (~1 min)
        after this write, booting with the previous pin while actual ==
        desired. Closing it requires the server to report its live pin (e.g.
        on heartbeat) so the reconciler can compare; tracked as a follow-up.
        """
        deployment_name, location_name = key
        with self._grpc_servers_lock:
            server = self._grpc_servers.get(key)
        if not isinstance(server, DagsterCloudGrpcServer):
            raise Exception(
                f"No running server for {deployment_name}:{location_name}; cannot reload in place."
            )
        handle = server.server_handle
        metadata = desired_entry.code_location_deploy_data
        serialized = serialize_value(metadata.defs_state_info) if metadata.defs_state_info else ""
        self._create_or_replace_defs_state_config_map(
            deployment_name,
            location_name,
            handle.name,
            handle.namespace,
            serialized_defs_state_info=serialized,
            server_timestamp=desired_entry.update_timestamp,
        )
        super()._reload_pin_in_place(key, desired_entry)

    def _remove_server_handle(self, server_handle: K8sHandle) -> None:
        # Since we track which servers to delete by listing the k8s deployments,
        # delete the k8s service first to ensure that it can't be left dangling
        try:
            self._get_core_api_client().delete_namespaced_service(
                server_handle.name, server_handle.namespace
            )
        except ApiException as e:
            if e.status == 404:
                self._logger.exception(
                    f"Tried to delete service {server_handle.name} but it was not found"
                )
            else:
                raise

        with self._get_apps_api_instance() as api_instance:
            try:
                api_instance.delete_namespaced_deployment(
                    server_handle.name, server_handle.namespace
                )
            except ApiException as e:
                if e.status == 404:
                    self._logger.exception(
                        f"Tried to delete deployment {server_handle.name} but it was not found"
                    )
                else:
                    raise

        # Each incarnation owns exactly one defs-state ConfigMap, named
        # deterministically from its own k8s Deployment name — so this delete
        # can never touch the CM of a live replacement server for the same
        # location. Pre-v2 Deployments lack the CM entirely → the 404 path is
        # the no-op.
        cm_name = defs_state_config_map_name(server_handle.name)
        try:
            self._get_core_api_client().delete_namespaced_config_map(
                cm_name, server_handle.namespace
            )
        except ApiException as e:
            if e.status != 404:
                self._logger.exception(
                    f"Failed to delete defs-state ConfigMap {cm_name} in namespace "
                    f"{server_handle.namespace} during server removal."
                )

        self._logger.info(
            f"Removed deployment and service {server_handle.name} in namespace {server_handle.namespace}"
        )

    def __exit__(self, exception_type, exception_value, traceback):
        super().__exit__(exception_value, exception_value, traceback)
        self._launcher.dispose()

    def run_launcher(self):
        return self._launcher
