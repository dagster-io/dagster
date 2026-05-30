import copy
import socket
import uuid
from collections.abc import Sequence
from contextlib import ExitStack
from functools import lru_cache
from typing import TYPE_CHECKING, Any

import yaml
from dagster import (
    Array,
    Field,
    Map,
    String,
    _check as check,
)
from dagster._config import process_config
from dagster._core.errors import DagsterInvalidConfigError, DagsterInvariantViolationError
from dagster._core.instance import DagsterInstance
from dagster._core.instance.config import config_field_for_configurable_class
from dagster._core.instance.ref import InstanceRef, configurable_class_data
from dagster._core.launcher import DefaultRunLauncher, RunLauncher
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.storage.defs_state.base import DefsStateStorage
from dagster._serdes import ConfigurableClassData
from dagster_cloud_cli.core.graphql_client import (
    RETRY_STATUS_CODES,
    create_agent_graphql_client,
    create_agent_http_client,
    create_graphql_requests_session,
    get_agent_headers,
)
from dagster_cloud_cli.core.headers.auth import DagsterCloudInstanceScope
from urllib3 import Retry

from dagster_cloud.agent import AgentQueuesConfig
from dagster_cloud.auth.constants import decode_agent_token
from dagster_cloud.storage.client import dagster_cloud_api_config
from dagster_cloud.util import get_env_names_from_config, is_isolated_run

if TYPE_CHECKING:
    from requests import Session

    from dagster_cloud.workspace.user_code_launcher.user_code_launcher import (
        DagsterCloudUserCodeLauncher,
    )


class DagsterCloudInstance(DagsterInstance):
    @property
    def telemetry_enabled(self) -> bool:
        return False

    @property
    def run_retries_max_retries(self) -> int:
        raise NotImplementedError(
            "run_retries.max_retries is a deployment setting and can only be accessed by a DeploymentScopedHostInstance"
        )

    @property
    def run_retries_retry_on_asset_or_op_failure(self) -> bool:
        raise NotImplementedError(
            "run_retries.retry_on_asset_or_op_failure is a deployment setting and can only be accessed by a DeploymentScopedHostInstance"
        )

    @property
    def defs_state_storage(self) -> DefsStateStorage | None:
        # only DeploymentScopedHostInstance / DagsterCloudAgentInstance have a defs state storage
        return None


class DagsterCloudAgentInstance(DagsterCloudInstance):
    def __init__(
        self,
        *args,
        dagster_cloud_api,
        user_code_launcher=None,
        agent_replicas=None,
        isolated_agents=None,
        agent_queues=None,
        allowed_full_deployment_locations=None,
        allowed_branch_deployment_locations=None,
        agent_metrics=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self._unprocessed_dagster_cloud_api_config = dagster_cloud_api
        self._dagster_cloud_api_config = check.not_none(
            self._get_processed_config(
                "dagster_cloud_api",
                dagster_cloud_api,
                dagster_cloud_api_config(),
            )
        )

        check.invariant(
            not (
                self._dagster_cloud_api_config.get("deployment")
                and self._dagster_cloud_api_config.get("deployments")
            ),
            "Cannot set both deployment and deployments in `dagster_cloud_api`",
        )

        self._user_code_launcher_data = (
            configurable_class_data(user_code_launcher) if user_code_launcher else None
        )

        if not self._user_code_launcher_data:
            # This is a user facing error. We should have more actionable advice and link to docs here.
            raise DagsterInvariantViolationError(
                "User code launcher is not configured for DagsterCloudAgentInstance. Configure a"
                " user code launcher under the user_code_launcher: key in your dagster.yaml file."
            )

        self._exit_stack = ExitStack()

        self._user_code_launcher = None
        self._graphql_requests_session: Session | None = None
        self._rest_requests_session: Session | None = None
        self._graphql_client = None
        self._http_client = None

        assert self.dagster_cloud_url

        # Handle backcompat between isolated_agents and agent_replicas
        if isolated_agents and agent_replicas:
            raise Exception(
                "Cannot provide both isolated_agents and agent_replicas configuration. Please only"
                " provide one of these."
            )
        if agent_replicas:
            self._isolated_agents = self._get_processed_config(
                "agent_replicas", agent_replicas, self._isolated_agents_config_schema()
            )
        elif isolated_agents:
            self._isolated_agents = self._get_processed_config(
                "isolated_agents", isolated_agents, self._isolated_agents_config_schema()
            )
        else:
            self._isolated_agents = None

        processed_agent_queues_config = self._get_processed_config(
            "agent_queues", agent_queues, self._agent_queues_config_schema()
        )
        self.agent_queues_config = AgentQueuesConfig(**processed_agent_queues_config)

        self._allowed_full_deployment_locations: dict[str, list[str]] | None = (
            allowed_full_deployment_locations
        )
        self._allowed_branch_deployment_locations: list[str] | None = (
            allowed_branch_deployment_locations
        )

        self._instance_uuid = str(uuid.uuid4())

    @property
    def defs_state_storage(self) -> DefsStateStorage | None:
        # temporary hack to avoid cases where the default BlobStorageStateStorage is used
        from dagster_cloud.storage.defs_state.storage import GraphQLDefsStateStorage

        return (
            self._defs_state_storage
            if isinstance(self._defs_state_storage, GraphQLDefsStateStorage)
            else None
        )

    def _get_processed_config(
        self, name: str, config: dict[str, Any] | None, config_type: dict[str, Any]
    ):
        config_dict = check.opt_dict_param(config, "config", key_type=str)
        processed_config = process_config(config_type, config_dict)
        if not processed_config.success:
            raise DagsterInvalidConfigError(
                f"Errors whilst loading {name} config",
                processed_config.errors,
                config_dict,
            )
        return processed_config.value

    def _dagster_cloud_api_config_for_deployment(self, deployment_name: str | None):
        new_api_config = dict(copy.deepcopy(self._dagster_cloud_api_config))
        if deployment_name:
            new_api_config["deployment"] = deployment_name
            if self.includes_branch_deployments:
                del new_api_config["branch_deployments"]
            new_api_config.pop("deployments", None)
            new_api_config.pop("all_serverless_deployments", None)
        else:
            new_api_config.pop("deployment", None)
            new_api_config.pop("deployments", None)

        return new_api_config

    def ref_for_deployment(self, deployment_name: str) -> InstanceRef:
        my_ref = self.get_ref()
        my_custom_instance_class_data = my_ref.custom_instance_class_data
        new_class_data = _cached_inject_deployment(my_custom_instance_class_data, deployment_name)

        return my_ref._replace(custom_instance_class_data=new_class_data)

    def organization_scoped_graphql_client(self):
        return create_agent_graphql_client(
            self.client_managed_retries_requests_session,
            self.dagster_cloud_graphql_url,
            self._dagster_cloud_api_config_for_deployment(None),
            scope=DagsterCloudInstanceScope.ORGANIZATION,
        )

    def graphql_client_for_deployment(self, deployment_name: str | None):
        return create_agent_graphql_client(
            self.client_managed_retries_requests_session,
            self.dagster_cloud_graphql_url,
            self._dagster_cloud_api_config_for_deployment(deployment_name),
            scope=DagsterCloudInstanceScope.DEPLOYMENT,
        )

    def headers_for_deployment(self, deployment_name: str):
        return get_agent_headers(
            self._dagster_cloud_api_config_for_deployment(deployment_name),
            DagsterCloudInstanceScope.DEPLOYMENT,
        )

    def create_graphql_client(
        self, scope: DagsterCloudInstanceScope = DagsterCloudInstanceScope.DEPLOYMENT
    ):
        return create_agent_graphql_client(
            self.client_managed_retries_requests_session,
            self.dagster_cloud_graphql_url,
            self._dagster_cloud_api_config,
            scope=scope,
        )

    def _translate_socket_param(self, socket_option: str | int):
        if isinstance(socket_option, str):
            check.invariant(
                hasattr(socket, socket_option),
                f"socket module does not have an {socket_option} attribute",
            )
            return getattr(socket, socket_option)
        else:
            return socket_option

    def _socket_options(self):
        if self._dagster_cloud_api_config.get("socket_options") is None:
            return None

        translated_socket_options = []
        for socket_option in self._dagster_cloud_api_config["socket_options"]:
            check.invariant(
                len(socket_option) == 3, "Each socket option must be a list of three values"
            )
            socket_param_1, socket_param_2, socket_val = socket_option
            translated_socket_options.append(
                (
                    self._translate_socket_param(socket_param_1),
                    self._translate_socket_param(socket_param_2),
                    socket_val,
                )
            )

        return translated_socket_options

    @property
    def client_managed_retries_requests_session(self):
        """A shared requests Session to use between GraphQL clients.

        Retries handled in GraphQL client layer.
        """
        if self._graphql_requests_session is None:
            self._graphql_requests_session = self._exit_stack.enter_context(
                create_graphql_requests_session(
                    adapter_kwargs=dict(socket_options=self._socket_options())
                )
            )

        return self._graphql_requests_session

    @property
    def requests_managed_retries_session(self):
        """A requests session to use for non-GraphQL Rest API requests.

        Retries handled by requests.
        """
        if self._rest_requests_session is None:
            self._rest_requests_session = self._exit_stack.enter_context(
                create_graphql_requests_session(
                    adapter_kwargs=dict(
                        max_retries=Retry(
                            total=self.dagster_cloud_api_retries,
                            backoff_factor=self._dagster_cloud_api_config["backoff_factor"],
                            status_forcelist=RETRY_STATUS_CODES,
                        ),
                        socket_options=self._socket_options(),
                    )
                )
            )
        return self._rest_requests_session

    @property
    def graphql_client(self):
        if self._graphql_client is None:
            self._graphql_client = self.create_graphql_client(
                scope=DagsterCloudInstanceScope.DEPLOYMENT
            )

        return self._graphql_client

    @property
    def http_client(self):
        if self._http_client is None:
            self._http_client = create_agent_http_client(
                self.client_managed_retries_requests_session,
                self._dagster_cloud_api_config,
                scope=DagsterCloudInstanceScope.DEPLOYMENT,
            )

        return self._http_client

    @property
    def dagster_cloud_url(self):
        if "url" in self._dagster_cloud_api_config:
            return self._dagster_cloud_api_config["url"]

        organization, region = decode_agent_token(self.dagster_cloud_agent_token)
        if not organization:
            raise DagsterInvariantViolationError(
                "Could not derive Dagster Cloud URL from agent token. Create a new agent token or"
                " set the `url` field under `dagster_cloud_api` in your `dagster.yaml`."
            )

        return (
            f"https://{organization}.agent.{region}.dagster.cloud"
            if region
            else f"https://{organization}.agent.dagster.cloud"
        )

    @property
    def organization_name(self) -> str | None:
        organization, _ = decode_agent_token(self.dagster_cloud_agent_token)
        return organization

    @property
    def deployment_name(self) -> str | None:
        deployment_names = self.deployment_names
        check.invariant(
            len(deployment_names) <= 1,
            "Cannot call instance.deployment_name if multiple deployments are set",
        )
        if not deployment_names:
            return None
        return deployment_names[0]

    @property
    def deployment_names(self) -> list[str]:
        if self._dagster_cloud_api_config.get("deployment"):
            return [self._dagster_cloud_api_config["deployment"]]

        return self._dagster_cloud_api_config.get("deployments", [])

    @property
    def include_all_serverless_deployments(self) -> bool:
        return self._dagster_cloud_api_config.get("all_serverless_deployments") or False

    @property
    def dagit_url(self):
        organization, region = decode_agent_token(self.dagster_cloud_agent_token)
        if not organization:
            raise Exception(
                "Could not derive Dagster Cloud URL from agent token to generate a Dagit URL."
                " Generate a new agent token in the Dagit UI."
            )

        deployment = self._dagster_cloud_api_config.get("deployment")
        base_url = (
            f"https://{organization}.{region}.dagster.cloud/"
            if region
            else f"https://{organization}.dagster.cloud/"
        )
        return base_url + (f"{deployment}/" if deployment else "")

    @property
    def dagster_cloud_graphql_url(self):
        return f"{self.dagster_cloud_url}/graphql"

    @property
    def dagster_cloud_store_events_url(self):
        return f"{self.dagster_cloud_url}/store_events"

    @property
    def dagster_cloud_upload_logs_url(self):
        return f"{self.dagster_cloud_url}/upload_logs"

    @property
    def dagster_cloud_gen_logs_url_url(self):
        return f"{self.dagster_cloud_url}/gen_logs_url"

    @property
    def dagster_cloud_gen_insights_url_url(self) -> str:
        return f"{self.dagster_cloud_url}/gen_insights_url"

    @property
    def dagster_cloud_upload_job_snap_url(self):
        return f"{self.dagster_cloud_url}/upload_job_snapshot"

    @property
    def dagster_cloud_upload_workspace_entry_url(self):
        return f"{self.dagster_cloud_url}/upload_workspace_entry"

    @property
    def dagster_cloud_upload_api_response_url(self):
        return f"{self.dagster_cloud_url}/upload_api_response"

    @property
    def dagster_cloud_check_snapshot_url(self):
        return f"{self.dagster_cloud_url}/check_snapshot"

    @property
    def dagster_cloud_confirm_upload_url(self):
        return f"{self.dagster_cloud_url}/confirm_upload"

    @property
    def dagster_cloud_code_location_update_result_url(self):
        return f"{self.dagster_cloud_url}/code_location_update_result"

    def dagster_cloud_api_headers(self, scope: DagsterCloudInstanceScope):
        return get_agent_headers(self._dagster_cloud_api_config, scope=scope)

    @property
    def dagster_cloud_agent_token(self) -> str:
        check.invariant(
            self._dagster_cloud_api_config.get("agent_token") is not None,
            "No agent token found in dagster_cloud_api configuration. An agent token is required"
            " for Dagster Cloud authentication.",
        )
        return self._dagster_cloud_api_config["agent_token"]

    @property
    def dagster_cloud_api_retries(self) -> int:
        return self._dagster_cloud_api_config["retries"]

    @property
    def dagster_cloud_api_timeout(self) -> int:
        return self._dagster_cloud_api_config["timeout"]

    @property
    def dagster_cloud_api_proxies(self) -> dict[str, str] | None:
        # Requests library modifies the proxies key so create a copy
        return (
            self._dagster_cloud_api_config.get("proxies").copy()
            if self._dagster_cloud_api_config.get("proxies")
            else {}
        )

    @property
    def dagster_cloud_api_agent_label(self) -> str | None:
        return self._dagster_cloud_api_config.get("agent_label")

    @property
    def includes_branch_deployments(self) -> bool:
        return self._dagster_cloud_api_config.get("branch_deployments", False)

    @property
    def instance_uuid(self) -> str:
        return self._instance_uuid

    @property
    def allowed_full_deployment_locations(self) -> dict[str, list[str]] | None:
        return self._allowed_full_deployment_locations

    @property
    def allowed_branch_deployment_locations(self) -> list[str] | None:
        return self._allowed_branch_deployment_locations

    def is_location_allowed(
        self, deployment_name: str, location_name: str, is_branch_deployment: bool
    ) -> bool:
        """Check if a location should be allowed based on the allowed locations configuration."""
        if is_branch_deployment:
            # For branch deployments, check the branch deployment locations list
            if self._allowed_branch_deployment_locations is not None:
                return location_name in self._allowed_branch_deployment_locations
        else:
            # For full deployments, check the deployment-specific locations map
            if self._allowed_full_deployment_locations is not None:
                allowed_locations = self._allowed_full_deployment_locations.get(deployment_name)
                if allowed_locations is not None:
                    return location_name in allowed_locations

        # If no restrictions are configured, allow all locations
        return True

    @property
    def agent_display_name(self) -> str:
        if self.dagster_cloud_api_agent_label:
            return f"Agent {self.instance_uuid[:8]} ({self.dagster_cloud_api_agent_label})"
        else:
            return f"Agent {self.instance_uuid[:8]}"

    @property
    def dagster_cloud_api_env_vars(self) -> list[str]:
        return get_env_names_from_config(
            dagster_cloud_api_config(), self._unprocessed_dagster_cloud_api_config
        )

    @property
    def user_code_launcher(self) -> "DagsterCloudUserCodeLauncher":
        # Lazily load in case the user code launcher requires dependencies (like dagster-k8s)
        # that we don't neccesarily need to load in every context that loads a
        # DagsterCloudAgentInstance (for example, a step worker)
        from dagster_cloud.workspace.user_code_launcher.user_code_launcher import (
            DagsterCloudUserCodeLauncher,
        )

        if not self._user_code_launcher:
            self._user_code_launcher = self._exit_stack.enter_context(
                self._user_code_launcher_data.rehydrate(as_type=DagsterCloudUserCodeLauncher)  # type: ignore  # (possible none)
            )
            self._user_code_launcher.register_instance(self)
        return self._user_code_launcher

    @property
    def run_launcher(self) -> RunLauncher:
        """The agent has two run launchers, isolated and non-isolated. Use get_run_launcher_for_run to
        get the appropriate one. This method will always return the isolated run launcher, which
        is required for some OSS peices like the k8s executor.
        """
        return self.user_code_launcher.run_launcher()

    def get_run_launcher_for_run(self, run: DagsterRun) -> RunLauncher:
        # If the run is isolated, use the isolated run launcher, which is specific to whatever agent
        # type we're using- ECS, K8s, etc.
        #
        # If the run is not isolated, use the DefaultRunLauncher to send it to the gRPC server.
        if is_isolated_run(run):
            return self.user_code_launcher.run_launcher()
        else:
            launcher = DefaultRunLauncher()
            launcher.register_instance(self)
            return launcher

    @staticmethod
    def get():
        instance = DagsterInstance.get()
        if not isinstance(instance, DagsterCloudAgentInstance):
            raise DagsterInvariantViolationError(
                """
DagsterInstance.get() did not return a DagsterCloudAgentInstance. Make sure that your"
`dagster.yaml` file is correctly configured to include the following:
instance_class:
  module: dagster_cloud.instance
  class: DagsterCloudAgentInstance
"""
            )
        return instance

    @classmethod
    def config_schema(cls):
        return {
            "dagster_cloud_api": Field(dagster_cloud_api_config(), is_required=True),
            "user_code_launcher": config_field_for_configurable_class(),
            "isolated_agents": Field(cls._isolated_agents_config_schema(), is_required=False),
            "agent_replicas": Field(
                cls._isolated_agents_config_schema(), is_required=False
            ),  # deprecated in favor of isolated_agents
            "agent_queues": Field(cls._agent_queues_config_schema(), is_required=False),
            "allowed_full_deployment_locations": Field(
                Map(String, Array(String)),
                is_required=False,
                description="Mapping of full deployment names to allowed location names",
            ),
            "allowed_branch_deployment_locations": Field(
                Array(String),
                is_required=False,
                description="List of allowed location names for branch deployments",
            ),
        }

    @classmethod
    def _code_server_metrics_config_schema(cls):
        return {"enabled": Field(bool, is_required=False, default_value=False)}

    @classmethod
    def _isolated_agents_config_schema(cls):
        return {"enabled": Field(bool, is_required=False, default_value=False)}

    @classmethod
    def _agent_queues_config_schema(cls):
        return {
            "include_default_queue": Field(bool, default_value=True),
            "additional_queues": Field(Array(String), is_required=False),
        }

    def get_required_daemon_types(self) -> Sequence[str]:
        return []

    @staticmethod
    def config_defaults(base_dir):
        defaults = InstanceRef.config_defaults(base_dir)

        empty_yaml = yaml.dump({})

        # `defaults` is typed `Mapping[...]` upstream but is a mutable dict at runtime.
        defaults["run_storage"] = ConfigurableClassData(  # ty: ignore[invalid-assignment]
            "dagster_cloud.storage.runs",
            "GraphQLRunStorage",
            empty_yaml,
        )
        defaults["event_log_storage"] = ConfigurableClassData(  # ty: ignore[invalid-assignment]
            "dagster_cloud.storage.event_logs",
            "GraphQLEventLogStorage",
            empty_yaml,
        )
        defaults["schedule_storage"] = ConfigurableClassData(  # ty: ignore[invalid-assignment]
            "dagster_cloud.storage.schedules",
            "GraphQLScheduleStorage",
            empty_yaml,
        )
        defaults["storage"] = ConfigurableClassData(  # ty: ignore[invalid-assignment]
            module_name="dagster._core.storage.legacy_storage",
            class_name="CompositeStorage",
            config_yaml=yaml.dump(
                {
                    "run_storage": {
                        "module_name": "dagster_cloud.storage.runs",
                        "class_name": "GraphQLRunStorage",
                        "config_yaml": empty_yaml,
                    },
                    "event_log_storage": {
                        "module_name": "dagster_cloud.storage.event_logs",
                        "class_name": "GraphQLEventLogStorage",
                        "config_yaml": empty_yaml,
                    },
                    "schedule_storage": {
                        "module_name": "dagster_cloud.storage.schedules",
                        "class_name": "GraphQLScheduleStorage",
                        "config_yaml": empty_yaml,
                    },
                },
                default_flow_style=False,
            ),
        )

        defaults["compute_logs"] = ConfigurableClassData(  # ty: ignore[invalid-assignment]
            "dagster_cloud.storage.compute_logs", "CloudComputeLogManager", empty_yaml
        )

        defaults["secrets"] = ConfigurableClassData(  # ty: ignore[invalid-assignment]
            "dagster_cloud.secrets", "DagsterCloudSecretsLoader", empty_yaml
        )

        defaults["defs_state_storage"] = ConfigurableClassData(  # ty: ignore[invalid-assignment]
            "dagster_cloud.storage.defs_state", "GraphQLDefsStateStorage", empty_yaml
        )

        return defaults

    def dispose(self) -> None:
        super().dispose()
        self._exit_stack.close()

    @property
    def should_start_background_run_thread(self) -> bool:
        # If using isolated agents (that is, agents cannot see each other's grpc
        # servers), TERMINATE_RUN requests can't be served by the Dagster Cloud API,
        # which will send requests to any agent. Only the agent with the run can
        # terminate it - so we need to start a background run thread to monitor for
        # runs moved into a canceling state.
        return self.is_using_isolated_agents

    @property
    def is_using_isolated_agents(self) -> bool:
        return self._isolated_agents is not None and self._isolated_agents.get("enabled", False)

    @property
    def dagster_cloud_run_worker_monitoring_interval_seconds(self) -> int:
        # potentially overridden interval in the serverless user code launcher
        return 30


@lru_cache(maxsize=100)  # Scales on order of active branch deployments
def _cached_inject_deployment(
    custom_instance_class_data: ConfigurableClassData,
    deployment_name: str,
) -> ConfigurableClassData:
    # incurs costly yaml parse
    config_dict = custom_instance_class_data.config_dict

    config_dict["dagster_cloud_api"]["deployment"] = deployment_name
    if config_dict["dagster_cloud_api"].get("branch_deployments"):
        del config_dict["dagster_cloud_api"]["branch_deployments"]
    if config_dict["dagster_cloud_api"].get("deployments"):
        del config_dict["dagster_cloud_api"]["deployments"]

    return ConfigurableClassData(
        "dagster_cloud.instance",
        "DagsterCloudAgentInstance",
        # incurs costly yaml dump
        yaml.dump(config_dict),
    )
