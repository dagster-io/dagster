from typing import AbstractSet, Literal, Mapping, Optional, Sequence, Union

from dagster import AssetExecutionContext, MaterializeResult
from dagster._core.blueprints.base_asset_blueprint import (
    BaseAssetBlueprint,
    BaseMultiAssetBlueprint,
)


class ShellCommandAssetBlueprint(BaseAssetBlueprint):
    """A blueprint for an asset definition whose materialization function is a shell command.

    Requires the code location to include a "pipes_subprocess_client" resource with type
    dagster.PipesSubprocessClient.

    Attributes:
        command (Union[str, Sequence[str]]): The command to run. Will be passed to `subprocess.Popen()`.
        env (Optional[Mapping[str, str]]): An optional dict of environment variables to pass to the subprocess.
        cwd (Optional[str]): Working directory in which to launch the subprocess command.
    """

    type: Literal["shell_command_asset"] = "shell_command_asset"
    command: Union[str, Sequence[str]]
    env: Optional[Mapping[str, str]] = None
    cwd: Optional[str] = None

    @staticmethod
    def get_required_resource_keys() -> AbstractSet[str]:
        return {"pipes_subprocess_client"}

    def materialize(self, context: AssetExecutionContext) -> MaterializeResult:
        return context.resources.pipes_subprocess_client.run(
            context=context, env=self.env, cwd=self.cwd, command=self.command
        ).get_materialize_result()


class ShellCommandMultiAssetBlueprint(BaseMultiAssetBlueprint):
    """A blueprint for an asset definition whose materialization function is a shell command.

    Requires the code location to include a "pipes_subprocess_client" resource with type
    dagster.PipesSubprocessClient.

    Attributes:
        command (Union[str, Sequence[str]]): The command to run. Will be passed to `subprocess.Popen()`.
        env (Optional[Mapping[str, str]]): An optional dict of environment variables to pass to the subprocess.
        cwd (Optional[str]): Working directory in which to launch the subprocess command.
    """

    type: Literal["shell_command_multi_asset"] = "shell_command_multi_asset"
    command: Union[str, Sequence[str]]
    env: Optional[Mapping[str, str]] = None
    cwd: Optional[str] = None

    @staticmethod
    def get_required_resource_keys() -> AbstractSet[str]:
        return {"pipes_subprocess_client"}

    def materialize(self, context: AssetExecutionContext):
        return context.resources.pipes_subprocess_client.run(
            context=context, env=self.env, cwd=self.cwd, command=self.command
        ).get_results()
