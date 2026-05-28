import logging
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
from dagster._serdes import ConfigurableClass
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
    construct_code_location_deployment,
    construct_code_location_service,
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
from dagster_cloud.workspace.user_code_launcher.utils import (
    deterministic_label_for_location,
    get_code_server_port,
)

DEFAULT_DEPLOYMENT_STARTUP_TIMEOUT = 300
DEFAULT_IMAGE_PULL_GRACE_PERIOD = 30

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

    def _list_server_handles(self) -> list[K8sHandle]:
        namespaces: set[str] = set()
        if self._namespace:
            namespaces.add(self._namespace)
        for namespace_items in self._used_namespaces.values():
            for namespace in namespace_items:
                namespaces.add(namespace)
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

    def get_agent_id_for_server(self, handle: K8sHandle) -> str | None:
        return handle.labels.get("agent_id")

    def get_server_create_timestamp(self, handle: K8sHandle) -> float | None:
        return handle.creation_timestamp

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

        self._logger.info(
            f"Removed deployment and service {server_handle.name} in namespace {server_handle.namespace}"
        )

    def __exit__(self, exception_type, exception_value, traceback):
        super().__exit__(exception_value, exception_value, traceback)
        self._launcher.dispose()

    def run_launcher(self):
        return self._launcher
