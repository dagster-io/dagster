import os
from collections.abc import Mapping, Sequence
from typing import Any, Generic, Optional, TypeVar, get_args

from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._record import record
from jinja2.nativetypes import NativeTemplate
from pydantic import BaseModel, ConfigDict, TypeAdapter

from dagster_components.core.schema.metadata import ResolutionMetadata, get_resolution_metadata

T = TypeVar("T")
U = TypeVar("U")


def env_scope(key: str) -> Optional[str]:
    return os.environ.get(key)


def automation_condition_scope() -> Mapping[str, Any]:
    return {
        "eager": AutomationCondition.eager,
        "on_cron": AutomationCondition.on_cron,
    }


@record
class TemplatedValueResolver:
    scope: Mapping[str, Any]

    @staticmethod
    def default() -> "TemplatedValueResolver":
        return TemplatedValueResolver(
            scope={"env": env_scope, "automation_condition": automation_condition_scope()}
        )

    def with_scope(self, **additional_scope) -> "TemplatedValueResolver":
        return TemplatedValueResolver(scope={**self.scope, **additional_scope})

    def _resolve_value(self, val: Any) -> Any:
        """Resolves a single value, if it is a templated string."""
        return NativeTemplate(val).render(**self.scope) if isinstance(val, str) else val

    def _resolve_obj_pre_process(self, val: Any, resolution_metadata: ResolutionMetadata) -> Any:
        if resolution_metadata.pre_process:
            return resolution_metadata.pre_process(val, self)

        output_type = resolution_metadata.output_type or type(val)
        if issubclass(output_type, ResolvableModel):
            if resolution_metadata.output_type is None:
                # use the default resolution data
                return val.resolve(self)
            else:
                return val.resolve_as(output_type, self)
        elif issubclass(output_type, Sequence):
            inner_annotation = get_args(output_type)[0]
            return [self.resolve_obj(v, get_resolution_metadata(inner_annotation)) for v in val]
        elif issubclass(output_type, Mapping):
            key_annotation, value_annotation = get_args(output_type)
            key_metadata, value_metadata = (
                get_resolution_metadata(key_annotation),
                get_resolution_metadata(value_annotation),
            )
            return {
                self.resolve_obj(k, key_metadata): self.resolve_obj(v, value_metadata)
                for k, v in val.items()
            }
        else:
            return self._resolve_value(val)

    def resolve_obj(self, val: Any, resolution_metadata: ResolutionMetadata) -> Any:
        """Recursively resolves templated values in a nested object."""
        preprocessed = self._resolve_obj_pre_process(val, resolution_metadata)
        if resolution_metadata.post_process:
            resolved = resolution_metadata.post_process(preprocessed, self)
        else:
            resolved = preprocessed

        return TypeAdapter(
            resolution_metadata.output_type, config={"arbitrary_types_allowed": True}
        ).validate_python(resolved)


class ResolvableModel(BaseModel, Generic[T]):
    """Base class for models that are part of a component schema."""

    model_config = ConfigDict(extra="forbid")

    def get_resolved_properties(self, resolver: TemplatedValueResolver) -> Mapping[str, Any]:
        """Returns a dictionary of resolved properties for this class."""
        raw_properties = self.model_dump(exclude_unset=True)
        return {
            k: resolver.resolve_obj(v, get_resolution_metadata(self.__pydantic_fields__[k]))
            for k, v in raw_properties.items()
        }

    def resolve_as(self, cls: type[U], resolver: TemplatedValueResolver) -> U:
        """Resolves this model to a new instance of the given class."""
        return cls(**self.get_resolved_properties(resolver))
