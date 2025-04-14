import os
from typing import Any, NamedTuple, Optional

from dagster_shared import check
from dagster_shared.serdes import whitelist_for_serdes

from .agent_queue import AgentQueue

# Python 3.8 is EOL and support will be removed soon.
# Dagster 1.9 onwards there is no support for 3.8 so we use an older base image.
# Defaults to a base image tag for  1.8.13
_PYTHON_38_BASE_IMAGE_TAG = os.getenv("PYTHON_38_BASE_IMAGE_TAG", "1be1105a-626d7d2a")


@whitelist_for_serdes
class GitMetadata(
    NamedTuple(
        "_GitMetadata",
        [("commit_hash", Optional[str]), ("url", Optional[str])],
    )
):
    def __new__(cls, commit_hash=None, url=None):
        return super().__new__(
            cls,
            check.opt_str_param(commit_hash, "commit_hash"),
            check.opt_str_param(url, "url"),
        )


@whitelist_for_serdes
class PexMetadata(
    NamedTuple(
        "_PexMetadata",
        [
            # pex_tag is a string like 'deps-234y4384.pex:source-39y3474.pex' that idenfies
            # the pex files to execute
            ("pex_tag", str),
            # python_version determines which pex base docker image to use
            # only one of PexMetadata.python_version or CodeLocationDeployData.image should be specified
            ("python_version", Optional[str]),
        ],
    )
):
    def __new__(cls, pex_tag, python_version=None):
        return super().__new__(
            cls,
            check.str_param(pex_tag, "pex_tag"),
            check.opt_str_param(python_version, "python_version"),
        )

    def resolve_image(self) -> Optional[str]:
        if not self.python_version:
            return None
        agent_image_tag = os.getenv("DAGSTER_CLOUD_AGENT_IMAGE_TAG")
        serverless_service_name = os.getenv("SERVERLESS_SERVICE_NAME")
        if not agent_image_tag or not serverless_service_name:
            return None
        image_tag = agent_image_tag if self.python_version != "3.8" else _PYTHON_38_BASE_IMAGE_TAG
        if serverless_service_name in ["serverless-agents", "serverless-agents-public-demo"]:
            return f"657821118200.dkr.ecr.us-west-2.amazonaws.com/dagster-cloud-serverless-base-py{self.python_version}:{image_tag}"
        else:
            return f"878483074102.dkr.ecr.us-west-2.amazonaws.com/dagster-cloud-serverless-base-py{self.python_version}:{image_tag}"


# History of CodeLocationDeployData
# 1. Removal of `enable_metrics` field
# 2. Renamed from `CodeDeploymentMetadata` to `CodeLocationDeployData``
@whitelist_for_serdes(storage_name="CodeDeploymentMetadata")
class CodeLocationDeployData(
    NamedTuple(
        "_CodeDeploymentMetadata",
        [
            ("image", Optional[str]),
            ("python_file", Optional[str]),
            ("package_name", Optional[str]),
            ("module_name", Optional[str]),
            ("working_directory", Optional[str]),
            ("executable_path", Optional[str]),
            ("attribute", Optional[str]),
            ("git_metadata", Optional[GitMetadata]),
            ("container_context", dict[str, Any]),
            ("cloud_context_env", dict[str, Any]),
            ("pex_metadata", Optional[PexMetadata]),
            ("agent_queue", Optional[AgentQueue]),
        ],
    )
):
    def __new__(
        cls,
        image=None,
        python_file=None,
        package_name=None,
        module_name=None,
        working_directory=None,
        executable_path=None,
        attribute=None,
        git_metadata=None,
        container_context=None,
        cloud_context_env=None,
        pex_metadata=None,
        agent_queue=None,
    ):
        check.invariant(
            len([val for val in [python_file, package_name, module_name] if val]) == 1,
            "Must supply exactly one of a file name, a package name, or a module name",
        )

        return super().__new__(
            cls,
            check.opt_str_param(image, "image"),
            check.opt_str_param(python_file, "python_file"),
            check.opt_str_param(package_name, "package_name"),
            check.opt_str_param(module_name, "module_name"),
            check.opt_str_param(working_directory, "working_directory"),
            check.opt_str_param(executable_path, "executable_path"),
            check.opt_str_param(attribute, "attribute"),
            check.opt_inst_param(git_metadata, "git_metadata", GitMetadata),
            check.opt_dict_param(container_context, "container_context", key_type=str),
            check.opt_dict_param(cloud_context_env, "cloud_context_env", key_type=str),
            check.opt_inst_param(pex_metadata, "pex_metadata", PexMetadata),
            check.opt_str_param(agent_queue, "agent_queue"),
        )

    def with_cloud_context_env(self, cloud_context_env: dict[str, Any]) -> "CodeLocationDeployData":
        return self._replace(cloud_context_env=cloud_context_env)

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
        )
