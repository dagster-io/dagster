import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union, cast

import click
import typer
from pydantic import ValidationError
from pydantic_core import ErrorDetails

from dagster_components.core.component import (
    Component,
    ComponentLoadContext,
    ComponentTypeRegistry,
    TemplatedValueResolver,
    get_component_type_name,
)
from dagster_components.core.component_defs_builder import (
    component_type_from_yaml_decl,
    load_components_from_context,
    path_to_decl_node,
    resolve_decl_node_to_yaml_decls,
)
from dagster_components.core.deployment import (
    CodeLocationProjectContext,
    find_enclosing_code_location_root_path,
    is_inside_code_location_project,
)
from dagster_components.utils import CLI_BUILTIN_COMPONENT_LIB_KEY

if TYPE_CHECKING:
    from dagster._utils.source_position import SourcePosition


@click.group(name="check")
def check_cli():
    """Commands for checking components."""


def prepend_lines_with_line_numbers(
    lines_with_numbers: Sequence[tuple[Optional[int], str]],
) -> Sequence[str]:
    """Prepend each line with a line number, right-justified to the maximum line number length.

    Args:
        lines_with_numbers: A sequence of tuples, where the first element is the line number and the
            second element is the line content. Some lines may have a `None` line number, which
            will be rendered as an empty string, used for e.g. inserted error message lines.
    """
    max_line_number_length = max([len(str(n)) for n, _ in lines_with_numbers])
    return [
        f"{(str(n) if n else '').rjust(max_line_number_length)} | {line.rstrip()}"
        for n, line in lines_with_numbers
    ]


def augment_inline_error_message(location: str, msg: str):
    """Improves a subset of Pyright error messages by including location information."""
    last_location_part = location.split(".")[-1]
    if msg == "Field required":
        return f"Field `{last_location_part}` is required but not provided"
    return msg


def format_indented_error_msg(col: int, msg: str) -> str:
    """Format an error message with a caret pointing to the column where the error occurred."""
    return typer.style(" " * (col - 1) + f"^ {msg}", fg=typer.colors.YELLOW)


OFFSET_LINES_BEFORE = 2
OFFSET_LINES_AFTER = 3


def error_dict_to_formatted_error(
    component_type: Optional[type[Component]], error_details: ErrorDetails
) -> str:
    ctx = error_details.get("ctx", {})
    source_position: SourcePosition = ctx["source_position"]
    source_position_path: Sequence[SourcePosition] = ctx["source_position_path"]

    # Retrieves dotted path representation of the location of the error in the YAML file, e.g.
    # params.nested.foo.an_int
    location = cast(str, error_details["loc"])[0].split(" at ")[0]

    # Find the first source position that has a different start line than the current source position
    # This is e.g. the parent json key of the current source position
    preceding_source_position = next(
        iter(
            [
                value
                for value in reversed(list(source_position_path))
                if value.start.line < source_position.start.line
            ]
        ),
        source_position,
    )
    with open(source_position.filename) as f:
        lines = f.readlines()
        lines_with_line_numbers = list(zip(range(1, len(lines) + 1), lines))

        filtered_lines_with_line_numbers = (
            lines_with_line_numbers[
                max(
                    0, preceding_source_position.start.line - OFFSET_LINES_BEFORE
                ) : source_position.start.line
            ]
            + [
                (
                    None,
                    format_indented_error_msg(
                        source_position.start.col,
                        augment_inline_error_message(location, error_details["msg"]),
                    ),
                )
            ]
            + lines_with_line_numbers[
                source_position.start.line : source_position.end.line + OFFSET_LINES_AFTER
            ]
        )
        # Combine the filtered lines with the line numbers, and add empty lines before and after
        lines_with_line_numbers = prepend_lines_with_line_numbers(
            [(None, ""), *filtered_lines_with_line_numbers, (None, "")]
        )
        code_snippet = "\n".join(lines_with_line_numbers)

    fmt_filename = (
        f"{source_position.filename}"
        f":{typer.style(source_position.start.line, fg=typer.colors.GREEN)}"
    )
    fmt_location = typer.style(location, fg=typer.colors.BRIGHT_WHITE)
    fmt_name = typer.style(
        f"{get_component_type_name(component_type)} " if component_type else "", fg=typer.colors.RED
    )
    return f"{fmt_filename} - {fmt_name}{fmt_location} {error_details['msg']}\n{code_snippet}\n"


@check_cli.command(name="component")
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.pass_context
def check_component_command(ctx: click.Context, paths: Sequence[str]) -> None:
    """Check component files against their schemas, showing validation errors."""
    # Resolve paths to check against, defaulting to the current working directory
    # Any files (e.g. component yaml files) are resolved to their parent component
    # directory, so that we check the corresponding component
    path_objs = [Path(p).resolve() for p in paths] or [Path.cwd().resolve()]
    path_objs = [p.parent if p.is_file() else p for p in path_objs]

    builtin_component_lib = ctx.obj.get(CLI_BUILTIN_COMPONENT_LIB_KEY, False)
    if not is_inside_code_location_project(Path.cwd()):
        click.echo(
            click.style(
                "This command must be run inside a Dagster code location project.", fg="red"
            )
        )
        sys.exit(1)

    validation_errors: list[tuple[Union[type[Component], None], ValidationError]] = []

    context = CodeLocationProjectContext.from_code_location_path(
        find_enclosing_code_location_root_path(Path.cwd()),
        ComponentTypeRegistry.from_entry_point_discovery(
            builtin_component_lib=builtin_component_lib
        ),
    )

    for instance_path in Path(context.components_path).iterdir():
        try:
            decl_node = path_to_decl_node(path=instance_path)
        except ValidationError as e:
            validation_errors.append((None, e))
            continue

        if not decl_node:
            raise Exception(f"No component found at path {instance_path}")

        yaml_decls = resolve_decl_node_to_yaml_decls(decl_node)
        for yaml_decl in yaml_decls:
            decl_path = yaml_decl.path.resolve()
            if not any((path == decl_path or path in decl_path.parents) for path in path_objs):
                continue

            clc = ComponentLoadContext(
                resources={},
                registry=context.component_registry,
                decl_node=yaml_decl,
                templated_value_resolver=TemplatedValueResolver.default(),
            )
            try:
                load_components_from_context(clc)
            except ValidationError as e:
                component_type = component_type_from_yaml_decl(
                    context.component_registry, yaml_decl
                )
                validation_errors.append((component_type, e))

    if validation_errors:
        errs = 0
        for component_type, e in validation_errors:
            for error_dict in e.errors():
                errs += 1
                click.echo(error_dict_to_formatted_error(component_type, error_dict))

        click.echo(f"Found {errs} validation errors in {len(validation_errors)} components.")
        sys.exit(1)
    else:
        click.echo("All components validated successfully.")
