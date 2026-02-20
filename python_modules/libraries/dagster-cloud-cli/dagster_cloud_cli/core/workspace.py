from collections.abc import Mapping
from typing import Any

from dagster_shared import check
from dagster_shared.record import IHaveNew, LegacyNamedTupleMixin, copy, record, record_custom
from dagster_shared.serdes import whitelist_for_serdes
from dagster_shared.serdes.objects.models.defs_state_info import DefsStateInfo
from dagster_shared.serdes.serdes import serialize_value

from dagster_cloud_cli.core.agent_queue import AgentQueue


@whitelist_for_serdes
@record(kw_only=False)
class GitMetadata:
    commit_hash: str | None = None
    url: str | None = None


@whitelist_for_serdes
@record(kw_only=False)
class PexMetadata:
    # pex_tag is a string like 'deps-234y4384.pex:source-39y3474.pex' that identifies
    # the pex files to execute
    pex_tag: str
    # python_version determines which pex base docker image to use
    # only one of PexMetadata.python_version or CodeLocationDeployData.image should be specified
    python_version: str | None = None


# History of CodeLocationDeployData
# 1. Removal of `enable_metrics` field
# 2. Renamed from `CodeDeploymentMetadata` to `CodeLocationDeployData``
@whitelist_for_serdes(storage_name="CodeDeploymentMetadata")
@record_custom
class CodeLocationDeployData(IHaveNew, LegacyNamedTupleMixin):
    image: str | None
    python_file: str | None
    package_name: str | None
    module_name: str | None
    working_directory: str | None
    executable_path: str | None
    attribute: str | None
    git_metadata: GitMetadata | None
    container_context: Mapping[str, Any]
    cloud_context_env: Mapping[str, Any]
    pex_metadata: PexMetadata | None
    agent_queue: AgentQueue | None
    autoload_defs_module_name: str | None
    defs_state_info: DefsStateInfo | None

    def __new__(
        cls,
        image: str | None = None,
        python_file: str | None = None,
        package_name: str | None = None,
        module_name: str | None = None,
        working_directory: str | None = None,
        executable_path: str | None = None,
        attribute: str | None = None,
        git_metadata: GitMetadata | None = None,
        container_context: Mapping[str, Any] | None = None,
        cloud_context_env: Mapping[str, Any] | None = None,
        pex_metadata: PexMetadata | None = None,
        agent_queue: AgentQueue | None = None,
        autoload_defs_module_name: str | None = None,
        defs_state_info: DefsStateInfo | None = None,
    ):
        check.invariant(
            len(
                [
                    val
                    for val in [
                        python_file,
                        package_name,
                        module_name,
                        autoload_defs_module_name,
                    ]
                    if val
                ]
            )
            == 1,
            "Must supply exactly one of python_file, package_name, module_name, or autoload_defs_module_name.",
        )

        return super().__new__(
            cls,
            image=image,
            python_file=python_file,
            package_name=package_name,
            module_name=module_name,
            working_directory=working_directory,
            executable_path=executable_path,
            attribute=attribute,
            git_metadata=git_metadata,
            container_context=container_context or {},
            cloud_context_env=cloud_context_env or {},
            pex_metadata=pex_metadata,
            agent_queue=agent_queue,
            autoload_defs_module_name=autoload_defs_module_name,
            defs_state_info=defs_state_info,
        )

    def with_cloud_context_env(
        self,
        cloud_context_env: Mapping[str, Any],
    ) -> "CodeLocationDeployData":
        return copy(self, cloud_context_env=cloud_context_env)

    def get_multipex_server_command(
        self,
        port: int | None,
        socket: str | None = None,
        metrics_enabled: bool = False,
    ) -> list[str]:
        return (
            ["dagster-cloud", "pex", "grpc", "--host", "0.0.0.0"]
            + (["--port", str(port)] if port else [])
            + (["--socket", str(socket)] if socket else [])
            + (["--enable-metrics"] if metrics_enabled else [])
            + (
                ["--defs-state-info", serialize_value(self.defs_state_info)]
                if self.defs_state_info
                else []
            )
        )

    def get_multipex_server_env(self) -> dict[str, str]:
        return {"DAGSTER_CURRENT_IMAGE": self.image} if self.image else {}

    def get_grpc_server_command(self, metrics_enabled: bool = False) -> list[str]:
        return (
            ([self.executable_path, "-m"] if self.executable_path else [])
            + [
                "dagster",
                "api",
                "grpc",
            ]
            + (["--enable-metrics"] if metrics_enabled else [])
            + (
                ["--defs-state-info", serialize_value(self.defs_state_info)]
                if self.defs_state_info
                else []
            )
        )
