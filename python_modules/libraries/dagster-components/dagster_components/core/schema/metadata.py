from collections.abc import Set
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Any, Callable, Optional, get_args, get_origin

from pydantic.fields import FieldInfo

if TYPE_CHECKING:
    from dagster_components.core.schema.resolution import TemplatedValueResolver

REF_BASE = "#/$defs/"
REF_TEMPLATE = f"{REF_BASE}{{model}}"
JSON_SCHEMA_EXTRA_REQUIRED_SCOPE_KEY = "dagster_required_scope"


@dataclass
class ResolutionMetadata:
    """Internal class that stores arbitrary metadata about a resolved field."""

    output_type: Optional[type] = None
    resolved_name: Optional[str] = None
    pre_process: Optional[Callable[[Any, "TemplatedValueResolver"], Any]] = None
    post_process: Optional[Callable[[Any, "TemplatedValueResolver"], Any]] = None


class ResolvableFieldInfo(FieldInfo):
    """Wrapper class that stores additional resolution metadata within a pydantic FieldInfo object.

    Examples:
    ```python
    class MyModel(ResolvableModel):
        resolvable_obj: Annotated[str, ResolvableFieldInfo(output_type=SomeObj)]
    ```
    """

    def __init__(
        self,
        *,
        output_type: Optional[type] = None,
        resolved_name: Optional[str] = None,
        pre_process_fn: Optional[Callable[[Any, "TemplatedValueResolver"], Any]] = None,
        post_process_fn: Optional[Callable[[Any, "TemplatedValueResolver"], Any]] = None,
        required_scope: Optional[Set[str]] = None,
    ):
        self.resolution_metadata = (
            ResolutionMetadata(
                output_type=output_type,
                resolved_name=resolved_name,
                pre_process=pre_process_fn,
                post_process=post_process_fn,
            )
            if output_type
            else None
        )
        super().__init__(
            json_schema_extra={JSON_SCHEMA_EXTRA_REQUIRED_SCOPE_KEY: list(required_scope or [])},
        )


def get_resolution_metadata(field_info: FieldInfo) -> ResolutionMetadata:
    annotation = field_info.annotation
    origin = get_origin(annotation)
    if origin is Annotated:
        _, f_metadata, *_ = get_args(annotation)
        if isinstance(f_metadata, ResolvableFieldInfo) and f_metadata.resolution_metadata:
            return f_metadata.resolution_metadata
    return ResolutionMetadata()
