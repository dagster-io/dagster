from abc import abstractmethod
from collections.abc import Mapping
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, TypeAdapter

from dagster_components.core.schema.metadata import get_resolution_metadata
from dagster_components.core.schema.resolver import TemplatedValueResolver

T = TypeVar("T")


class ResolvableModel(BaseModel, Generic[T]):
    """Base class for models that are part of a component schema."""

    model_config = ConfigDict(extra="forbid")

    def _resolved_properties(self, value_resolver: TemplatedValueResolver) -> Mapping[str, Any]:
        """Returns a dictionary of resolved properties for this class."""
        raw_properties = self.model_dump(exclude_unset=True)

        # validate that the resolved properties match the output type
        resolved_properties = {}
        for k, v in raw_properties.items():
            resolved = value_resolver.resolve_obj(v)
            annotation = self.__annotations__[k]
            rendering_metadata = get_resolution_metadata(annotation)

            if rendering_metadata.post_process:
                resolved = rendering_metadata.post_process(resolved)

            # hook into pydantic's type validation to handle complicated stuff like Optional[Mapping[str, int]]
            TypeAdapter(
                rendering_metadata.output_type, config={"arbitrary_types_allowed": True}
            ).validate_python(resolved)

            resolved_properties[k] = resolved

        return resolved_properties

    @abstractmethod
    def resolve(self, value_resolver: TemplatedValueResolver) -> T: ...
