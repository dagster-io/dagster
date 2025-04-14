from collections.abc import Mapping, Sequence
from inspect import Parameter, Signature
from typing import Any, Callable, Optional

import click
from click import Choice, Command, Option
from click.types import BOOL, FLOAT, INT, STRING, Path
from dagster_shared import check
from mcp.server.fastmcp import FastMCP
from typing_extensions import get_args, get_origin

from dagster_dg.utils import pushd

PARAMS_TO_IGNORE = {"cache_dir", "disable_cache", "use_component_modules"}
FIXED_PARAMS = {"verbose": True, "output_json": True}


def _is_simple_type(typ: type) -> bool:
    if get_args(typ) is not None and any(not _is_simple_type(arg) for arg in get_args(typ)):
        return False

    origin = get_origin(typ)
    if origin in (list, dict) or isinstance(origin, (Sequence, Mapping)):
        return True

    return typ in (int, float, bool, str, complex, bytes, Any)


def _to_fn_input(typ: click.ParamType) -> type:
    if isinstance(typ, Path):
        return str
    elif typ == BOOL:
        return bool
    elif typ == INT:
        return int
    elif typ == FLOAT:
        return float
    elif typ == STRING:
        return str
    elif isinstance(typ, Choice):
        return str
    raise Exception(f"Unknown param type: {typ}")


def cli_command_to_mcp_tool(
    mcp: FastMCP,
    name: str,
    cmd: Command,
    additional_doc: Optional[str] = None,
    replace_doc: Optional[str] = None,
    ignore_params: Optional[set[str]] = None,
    fixed_params: Optional[Mapping[str, Any]] = None,
) -> Callable:
    """Convert a click command to an MCP tool.

    Args:
        mcp: The MCP server to add the tool to.
        name: The name of the tool.
        cmd: The click command to convert.
        additional_doc: Additional documentation to add to the tool.
        replace_doc: Documentation to replace the existing documentation with.

        ignore_params: Parameters to ignore from the command.
        fixed_params: Parameters to set to a fixed value, for the command.
    """
    check.invariant(
        additional_doc is None or replace_doc is None,
        "Cannot provide both additional_doc and replace_doc",
    )
    ignore_params = ignore_params or set()
    fixed_params = dict(fixed_params) if fixed_params else {}

    cmd_params_to_use = {
        param
        for param in cmd.params
        if param.name not in PARAMS_TO_IGNORE
        and param.name not in ignore_params
        and param.name not in fixed_params
    }

    # Convert Click parameters to inspect.Parameter objects

    param_docs = ["project_path (str): The path to the Dagster project to run the command against."]

    sig_params = [
        Parameter(name="project_path", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=str)
    ]

    for param in cmd_params_to_use:
        if param.name in FIXED_PARAMS:
            fixed_params[param.name] = FIXED_PARAMS[param.name]
            continue

        param_type = _to_fn_input(param.type)
        if param.nargs != 1:
            param_type = list[param_type]

        check.invariant(
            _is_simple_type(param_type),
            f"Parameter type {param_type} is not a simple type",
        )

        sig_params.append(
            Parameter(
                name=check.not_none(param.name), kind=Parameter.KEYWORD_ONLY, annotation=param_type
            )
        )

        if isinstance(param, Option):
            if isinstance(param.type, Choice):
                param_docs.append(
                    f"{param.name} ({param_type.__name__}, valid inputs {param.type.choices}): {param.help}"
                )
            else:
                param_docs.append(f"{param.name} ({param_type.__name__}): {param.help}")

    def cli_command_tool(project_path: str, **kwargs: Any) -> Callable:
        with pushd(project_path):
            return cmd(**fixed_params, **kwargs)

    # Create new signature from parameters
    cli_command_tool.__signature__ = Signature(parameters=sig_params, return_annotation=Callable)

    doc = replace_doc or f"{cmd.__doc__}"
    if additional_doc:
        doc += f"\n{additional_doc}"
    doc += "\n\nArgs:\n"
    for param_doc in param_docs:
        doc += f"  {param_doc}\n"
    cli_command_tool.__doc__ = doc

    return mcp.tool(name=name, description=doc)(cli_command_tool)
