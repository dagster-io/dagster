import re
from collections.abc import Sequence
from typing import Optional, Union

import click
import typer
from jsonschema import ValidationError

from dagster_dg.component_key import ComponentKey
from dagster_dg.yaml_utils.source_position import SourcePositionTree


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


ADDITIONAL_PROPERTIES_ERROR_MESSAGE = (
    r"Additional properties are not allowed \('(.*?)' was unexpected\)"
)


def augment_error_path(error_details: ValidationError) -> Sequence[Union[str, int]]:
    """Augment the error location (e.g. key) for certain error messages.

    In particular, for extra properties, returns the location of the extra property instead
    of the parent key.
    """
    additional_property = re.match(ADDITIONAL_PROPERTIES_ERROR_MESSAGE, error_details.message)
    if additional_property:
        return [*error_details.absolute_path, additional_property.group(1)]
    return error_details.absolute_path


def format_indented_error_msg(col: int, msg: str) -> str:
    """Format an error message with a caret pointing to the column where the error occurred."""
    return typer.style(" " * (col - 1) + f"^ {msg}", fg=typer.colors.YELLOW)


OFFSET_LINES_BEFORE = 2
OFFSET_LINES_AFTER = 3


def error_dict_to_formatted_error(
    component_key: Optional[ComponentKey],
    error_details: ValidationError,
    source_position_tree: SourcePositionTree,
    prefix: Sequence[str] = (),
) -> str:
    """Convert a ValidationError to a formatted error message, including
    a code snippet of the offending YAML file.

    Args:
        component_name: The name of the component that the error occurred in, e.g. "my_component".
        error_details: The JSON Schema ValidationError object.
        source_position_tree: The SourcePositionTree object, which contains the source position of
            each line in the YAML file.
        prefix: A prefix to the JSON path of the location of the error in the YAML file. Used because
            we validate attributes separately from the top-level component YAML fields, so this is often
            set to e.g. ["attributes"] when validating the internal attributes of a component.
    """
    error_path = augment_error_path(error_details)

    source_position, source_position_path = source_position_tree.lookup_closest_and_path(
        [*prefix, *error_path], trace=None
    )

    # Retrieves dotted path representation of the location of the error in the YAML file, e.g.
    # attributes.nested.foo.an_int
    location = ".".join([*prefix, *[str(part) for part in error_path]]).split(" at ")[0]

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
                        augment_inline_error_message(location, error_details.message),
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
        f"{component_key.to_typename()} " if component_key else "", fg=typer.colors.RED
    )
    return f"{fmt_filename} - {fmt_name}{fmt_location} {error_details.message}\n{code_snippet}\n"
