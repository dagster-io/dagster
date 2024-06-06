from typing import Sequence, Type, TypeVar

from pydantic import BaseModel, ValidationError, parse_obj_as

from dagster._core.errors import DagsterInvariantViolationError
from dagster._model.pydantic_compat_layer import USING_PYDANTIC_1

from .source_position import (
    KeyPath,
    ValueAndSourcePositionTree,
    populate_source_position_and_key_paths,
)
from .yaml_utils import parse_yaml_with_source_positions

T = TypeVar("T", bound=BaseModel)


def _parse_and_populate_model_with_annotated_errors(
    cls: Type[T],
    obj_parse_root: ValueAndSourcePositionTree,
    obj_key_path_prefix: KeyPath,
) -> T:
    """Helper function to parse the Pydantic model from the parsed YAML object and populate source
    position information on the model and its sub-objects.

    Raises more helpful errors than Pydantic's default error messages, including the source position
    in the YAML file where the error occurred.

    Args:
        cls (Type[T]): The Pydantic model class to use for validation.
        obj_parse_root (ValueAndSourcePositionTree): The parsed YAML object to use for validation.
        file_root (Optional[ValueAndSourcePositionTree]): The root of the parsed YAML file, used for
            error reporting.
        obj_key_path_prefix (KeyPath): The path of keys that lead to the current object, used for
            both error reporting and populating source position information.
    """
    try:
        model = parse_obj_as(cls, obj_parse_root.value)
    except ValidationError as e:
        if USING_PYDANTIC_1:
            raise e
        else:
            line_errors = []
            for error in e.errors():
                key_path_in_obj = list(error["loc"])
                source_position = obj_parse_root.source_position_tree.lookup(key_path_in_obj)

                file_key_path: KeyPath = list(obj_key_path_prefix) + key_path_in_obj
                file_key_path_str = ".".join(str(part) for part in file_key_path)
                line_errors.append(
                    {**error, "loc": [file_key_path_str + " at " + str(source_position)]}
                )

            raise ValidationError.from_exception_data(  # type: ignore
                title=e.title,  # type: ignore
                line_errors=line_errors,
                input_type="json",
                hide_input=False,
            ) from None

    populate_source_position_and_key_paths(
        model, obj_parse_root.source_position_tree, obj_key_path_prefix
    )
    return model


def parse_yaml_file_to_pydantic(cls: Type[T], src: str, filename: str = "<string>") -> T:
    """Parse the YAML source and create a Pydantic model instance from it.

    Attaches source position information to the `_source_position_and_key_path` attribute of the
    Pydantic model instance and sub-objects.

    Args:
        cls (type[T]): The Pydantic model class to use for validation.
        src (str): The YAML source string to be parsed.
        filename (str): The filename associated with the YAML source, used for error reporting.
            Defaults to "<string>" if not provided.

    Returns:
        T: An instance of the Pydantic model class, with the `_source_position_and_key_path`
            attribute populated on it and all the objects inside it.

    Raises:
        ValidationError: If the YAML data does not conform to the Pydantic model schema. If using
            Pydantic2+, errors will include context information about the position in the document
            that the model corresponds to.
    """
    parsed = parse_yaml_with_source_positions(src, filename)
    return _parse_and_populate_model_with_annotated_errors(
        cls=cls, obj_parse_root=parsed, obj_key_path_prefix=[]
    )


def parse_yaml_file_to_pydantic_sequence(
    cls: Type[T], src: str, filename: str = "<string>"
) -> Sequence[T]:
    """Parse the YAML source and create a list of Pydantic model instances from it.

    Attaches source position information to the `_source_position_and_key_path` attribute of the
    Pydantic model instance and sub-objects.

    Args:
        cls (type[T]): The Pydantic model class to use for validation.
        src (str): The YAML source string to be parsed.
        filename (str): The filename associated with the YAML source, used for error reporting.
            Defaults to "<string>" if not provided.

    Returns:
        T: A list of instances of the Pydantic model class, with the `_source_position_and_key_path`
            attribute populated on each list element and all the objects inside them.

    Raises:
        ValidationError: If the YAML data does not conform to the Pydantic model schema. If using
            Pydantic2+, errors will include context information about the position in the document
            that the model corresponds to.
    """
    parsed = parse_yaml_with_source_positions(src, filename)

    if not isinstance(parsed.value, list):
        raise DagsterInvariantViolationError(
            f"Error parsing YAML file {filename}: Expected a list of objects at document root, but got {type(parsed.value)}"
        )

    results = []
    for i, entry in enumerate(parsed.value):
        results.append(
            _parse_and_populate_model_with_annotated_errors(
                cls=cls,
                obj_parse_root=ValueAndSourcePositionTree(
                    value=entry, source_position_tree=parsed.source_position_tree.children[i]
                ),
                obj_key_path_prefix=[i],
            )
        )
    return results
