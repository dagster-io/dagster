from typing import Any, Literal, cast

from dagster_shared.dagster_model.pydantic_compat_layer import model_fields
from typing_extensions import TypeVar, get_args, get_origin

from dagster import _check as check
from dagster._core.definitions.metadata.metadata_set import NamespacedKVSet
from dagster._utils.typing_api import is_closed_python_optional_type

T_NamespacedTagSet = TypeVar("T_NamespacedTagSet", bound="NamespacedTagSet")


class NamespacedTagSet(NamespacedKVSet):
    """Extend this class to define a set of tags in the same namespace.

    Supports splatting to a dictionary that can be placed inside a tags argument along with
    other tags.

    .. code-block:: python

        my_tags: NamespacedTagsSet = ...
        @asset(
            tags={**my_tags}
        )
        def my_asset():
            pass
    """

    def __init__(self, *args, **kwargs) -> None:
        for field_name, field in model_fields(self.__class__).items():
            annotation_type = field.annotation

            is_optional = is_closed_python_optional_type(annotation_type)
            is_optional_str = is_optional and str in get_args(annotation_type)
            is_optional_literal = (
                is_optional and get_origin(get_args(annotation_type)[0]) == Literal
            )
            if not (
                is_optional_str
                or annotation_type is str
                or is_optional_literal
                or annotation_type is Literal
            ):
                check.failed(
                    f"Type annotation for field '{field_name}' is not str, Optional[str], Literal, "
                    f"or Optional[Literal]. Is {annotation_type}."
                )
        super().__init__(*args, **kwargs)

    @classmethod
    def _extract_value(cls, field_name: str, value: Any) -> str:
        """Since all tag values are strings, we don't need to do any type coercion."""
        return cast("str", value)
