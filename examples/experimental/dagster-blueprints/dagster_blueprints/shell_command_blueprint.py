import shlex
from typing import AbstractSet, Literal, Mapping, Optional, Sequence, Union

from dagster import AssetExecutionContext
from pydantic import Field

from dagster_blueprints.blueprint_assets_definition import BlueprintAssetsDefinition


class ShellCommandBlueprint(BlueprintAssetsDefinition):
    """A blueprint for one or more assets whose shared materialization function is a shell command.

    Requires the code location to include a "pipes_subprocess_client" resource with type
    dagster.PipesSubprocessClient.
    """

    type: Literal["dagster/shell_command"] = "dagster/shell_command"
    command: Union[str, Sequence[str]] = Field(
        ..., description="The command to run. Will be passed to `subprocess.Popen()`."
    )
    env: Optional[Mapping[str, str]] = Field(
        default=None,
        description="An optional dict of environment variables to pass to the subprocess.",
    )
    cwd: Optional[str] = Field(
        default=None, description="Working directory in which to launch the subprocess command."
    )
    extras: Optional[Mapping[str, str]] = Field(
        default=None, description="An optional dict of extra parameters to pass to the subprocess."
    )

    @staticmethod
    def get_required_resource_keys() -> AbstractSet[str]:
        return {"pipes_subprocess_client"}

    def materialize(self, context: AssetExecutionContext):
        if isinstance(self.command, str):
            command = shlex.split(self.command)
        else:
            command = self.command

        return context.resources.pipes_subprocess_client.run(
            context=context, command=command, env=self.env, cwd=self.cwd, extras=self.extras
        ).get_results()
