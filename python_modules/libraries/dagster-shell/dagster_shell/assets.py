from typing import AbstractSet, Mapping, Optional, Sequence, Union

import dagster._check as check
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.events import CoercibleToAssetKey, Failure
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.execution.context.compute import OpExecutionContext

from dagster_shell.ops import ShellOpConfig
from dagster_shell.utils import execute, execute_script_file


def create_shell_asset(
    *,
    key: CoercibleToAssetKey,
    command: Optional[str] = None,
    script_path: Optional[str] = None,
    description: Optional[str] = None,
    deps: Optional[Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]]] = None,
    required_resource_keys: Optional[AbstractSet[str]] = None,
    op_tags: Optional[Mapping[str, str]] = None,
) -> AssetsDefinition:
    """Create an asset from a shell script.

    Args:
        shell_script_path (str): Path to the shell script.
        name (str): Name of the asset.
        ins (Optional[Dict[str, Asset]]): Mapping of input names to assets.
        **kwargs (Optional[Any]): Additional kwargs to pass to the asset constructor.

    Returns:
        Asset: The asset.
    """
    if command and script_path:
        check.failed("Only one of command or script_path can be provided.")
    elif command:
        exec_fn, first_arg = execute, command
    elif script_path:
        exec_fn, first_arg = execute_script_file, script_path
    else:
        check.failed("One of command or script_path must be provided.")

    @asset(
        key=key,
        deps=deps,
        description=description,
        required_resource_keys=required_resource_keys,
        op_tags=op_tags,
    )
    def shell_asset(context: OpExecutionContext, config: ShellOpConfig) -> str:
        output, return_code = exec_fn(
            first_arg,
            log=context.log,
            context=context,
            **config.to_execute_params(),
        )

        if return_code:
            raise Failure(
                description="Shell command execution failed with output: {output}".format(
                    output=output
                )
            )

        return output

    return shell_asset
