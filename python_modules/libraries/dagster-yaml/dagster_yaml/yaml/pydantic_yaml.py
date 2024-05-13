from typing import Any, TypeVar

from pydantic import BaseModel, RootModel, ValidationError

from dagster_yaml.yaml.object_mapping import populate_object_mapping_context
from dagster_yaml.yaml.with_source_positions import parse_yaml_with_source_positions

T = TypeVar("T", bound=BaseModel | RootModel[Any])


def parse_yaml_file(cls: type[T], src: str, filename: str = "<string>") -> T:
    """Parse the YAML source and create a Pydantic model instance.

    This function takes a YAML source string, a Pydantic model class, and an optional
    filename, and returns an instance of the Pydantic model. It performs the following
    steps:

    1. Parses the YAML source with source position information using
       `parse_yaml_with_source_positions()`.
    2. Validates the parsed data against the provided Pydantic model class, using the
       `model_validate()` method.
    3. Populates the `_object_mapping_context` attribute of the Pydantic model instance using the
       source position information.

    Args:
        cls (type[T]): The Pydantic model class to use for validation.
        src (str): The YAML source string to be parsed.
        filename (str): The filename associated with the YAML source, used for error reporting.
            Defaults to "<string>" if not provided.

    Returns:
        T: An instance of the Pydantic model class, with the `_object_mapping_context` attribute
            populated.

    Raises:
        ValidationError: If the YAML data does not conform to the Pydantic model schema.
    """
    parsed = parse_yaml_with_source_positions(src, filename)
    try:
        model = cls.model_validate(parsed.value, strict=True)
        exception_with_context = None
    except ValidationError as e:
        exception_data = [
            {
                **error,
                "loc": [
                    ".".join(str(part) for part in error["loc"])
                    + " at "
                    + str(parsed.tree_node.lookup(list(error["loc"])))
                ],
            }
            for error in e.errors()
        ]

        exception_with_context = ValidationError.from_exception_data(
            e.title,
            exception_data,  # type: ignore
            "json",
            False,
        )

    if exception_with_context:
        # Raise this outside of the "except" block to avoid the confusing "During handling of the
        # above exception, another exception occurred"
        raise exception_with_context

    populate_object_mapping_context(model, parsed.tree_node)
    return model
