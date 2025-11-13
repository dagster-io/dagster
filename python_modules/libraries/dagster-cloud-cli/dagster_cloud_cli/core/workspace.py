from collections.abc import Mapping
from typing import Any, Optional

from dagster_shared import check
from dagster_shared.record import IHaveNew, LegacyNamedTupleMixin, copy, record, record_custom
from dagster_shared.serdes import whitelist_for_serdes
from dagster_shared.serdes.objects.models.defs_state_info import DefsStateInfo
from dagster_shared.serdes.serdes import serialize_value

from dagster_cloud_cli.core.agent_queue import AgentQueue


@whitelist_for_serdes
@record(kw_only=False)
class GitMetadata:
    commit_hash: Optional[str] = None
    url: Optional[str] = None


@whitelist_for_serdes
@record(kw_only=False)
class PexMetadata:
    # pex_tag is a string like 'deps-234y4384.pex:source-39y3474.pex' that idenfies
    # the pex files to execute
    pex_tag: str
    # python_version determines which pex base docker image to use
    # only one of PexMetadata.python_version or CodeLocationDeployData.image should be specified
    python_version: Optional[str] = None


# History of CodeLocationDeployData
# 1. Removal of `enable_metrics` field
# 2. Renamed from `CodeDeploymentMetadata` to `CodeLocationDeployData``
@whitelist_for_serdes(storage_name="CodeDeploymentMetadata")
@record_custom
class CodeLocationDeployData(IHaveNew, LegacyNamedTupleMixin):
    image: Optional[str]
    python_file: Optional[str]
    package_name: Optional[str]
    module_name: Optional[str]
    working_directory: Optional[str]
    executable_path: Optional[str]
    attribute: Optional[str]
    git_metadata: Optional[GitMetadata]
    container_context: Mapping[str, Any]
    cloud_context_env: Mapping[str, Any]
    pex_metadata: Optional[PexMetadata]
    agent_queue: Optional[AgentQueue]
    autoload_defs_module_name: Optional[str]
    defs_state_info: Optional[DefsStateInfo]

    def __new__(
        cls,
        image: Optional[str] = None,
        python_file: Optional[str] = None,
        package_name: Optional[str] = None,
        module_name: Optional[str] = None,
        working_directory: Optional[str] = None,
        executable_path: Optional[str] = None,
        attribute: Optional[str] = None,
        git_metadata: Optional[GitMetadata] = None,
        container_context: Optional[Mapping[str, Any]] = None,
        cloud_context_env: Optional[Mapping[str, Any]] = None,
        pex_metadata: Optional[PexMetadata] = None,
        agent_queue: Optional[AgentQueue] = None,
        autoload_defs_module_name: Optional[str] = None,
        defs_state_info: Optional[DefsStateInfo] = None,
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
        port: Optional[int],
        socket: Optional[str] = None,
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
