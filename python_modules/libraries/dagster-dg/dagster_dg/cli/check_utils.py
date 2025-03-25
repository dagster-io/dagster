import re
from collections.abc import Sequence
from typing import Optional, Union

import click
import typer
from dagster_shared.serdes.objects import LibraryObjectKey
from dagster_shared.yaml_utils.source_position import SourcePositionTree
from jsonschema import ValidationError


@click.group(name="check")
def check_cli():
    """Commands for checking components."""


def augment_inline_error_message(last_location_part: str, msg: str):
    """Improves a subset of Pyright error messages by including location information."""
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


def error_dict_to_formatted_error(
    object_key: Optional[LibraryObjectKey],
    error_details: ValidationError,
    source_position_tree: SourcePositionTree,
    prefix: Sequence[str] = (),
) -> str:
    """Convert a ValidationError to a formatted error message, including
    a code snippet of the offending YAML file.

    Args:
    <<<<<<< HEAD
        component_key: The name of the component that the error occurred in, e.g. "my_component".
    =======
        object_key: The key of the component that the error occurred in.
    >>>>>>> 9402d2cc11 ([dg] Rename ComponentKey and adjacent to LibraryObjectKey)
        error_details: The JSON Schema ValidationError object.
        source_position_tree: The SourcePositionTree object, which contains the source position of
            each line in the YAML file.
        prefix: A prefix to the JSON path of the location of the error in the YAML file. Used because
            we validate attributes separately from the top-level component YAML fields, so this is often
            set to e.g. ["attributes"] when validating the internal attributes of a component.
    """
    error_path = augment_error_path(error_details)
    yaml_path = [*prefix, *error_path]
    last_location_part = str(yaml_path[-1]) if yaml_path else ""
    source = source_position_tree.source_error(
        yaml_path=yaml_path,
        inline_error_message=augment_inline_error_message(
            last_location_part,
            error_details.message,
        ),
        # May be able to discern certain error types that at the value instead of keys
        value_error=False,
    )

    fmt_filename = (
        f"{source.file_name}" f":{typer.style(source.start_line_no, fg=typer.colors.GREEN)}"
    )
    fmt_location = typer.style(source.location, fg=typer.colors.BRIGHT_WHITE)
    fmt_name = typer.style(
        f"{object_key.to_typename()} " if object_key else "", fg=typer.colors.RED
    )
    return f"{fmt_filename} - {fmt_name}{fmt_location} {error_details.message}\n{source.snippet}\n"
