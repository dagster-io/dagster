import inspect
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from dagster_shared.record import IHaveNew, record_custom
from dagster_shared.yaml_utils.source_position import SourcePosition
from pydantic import BaseModel
from typing_extensions import Self

import dagster._check as check
from dagster._annotations import PublicAttr, preview, public
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.metadata.source_code import CodeReference, LocalFileCodeReference
from dagster._core.definitions.utils import validate_component_owner
from dagster.components.component.component_scaffolder import DefaultComponentScaffolder
from dagster.components.resolved.base import Resolvable
from dagster.components.scaffold.scaffold import scaffold_with

if TYPE_CHECKING:
    from dagster.components.core.context import ComponentLoadContext


@public
@preview(emit_runtime_warning=False)
@record_custom
class ComponentTypeSpec(IHaveNew):
    """Specifies the core attributes of a component.

    Args:
        description (Optional[str]): Human-readable description of this component.
        metadata (Optional[Dict[str, Any]]): A dict of static metadata for this component.
            For example, users can provide information about the database table this
            component corresponds to.
        owners (Optional[Sequence[str]]): A list of strings representing owners of the component. Each
            string can be a user's email address, or a team name prefixed with `team:`,
            e.g. `team:finops`.
        tags (Optional[Sequence[str]]): Tags for filtering and organizing.

    """

    description: PublicAttr[Optional[str]]
    tags: PublicAttr[Sequence[str]]
    owners: PublicAttr[Sequence[str]]
    metadata: PublicAttr[Mapping[str, Any]]

    def __new__(
        cls,
        description: Optional[str] = None,
        tags: Optional[Sequence[str]] = None,
        owners: Optional[Sequence[str]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ):
        owners = check.opt_sequence_param(owners, "owners", of_type=str)
        for owner in owners:
            validate_component_owner(owner)

        return super().__new__(
            cls,
            description=check.opt_str_param(description, "description"),
            tags=check.opt_sequence_param(tags, "tags", of_type=str),
            owners=owners,
            metadata=check.opt_mapping_param(metadata, "metadata", key_type=str),
        )


@public
@preview(emit_runtime_warning=False)
@scaffold_with(DefaultComponentScaffolder)
class Component(ABC):
    """Components are a tool for dynamically creating Dagster definitions.
    A Component subclass must implement the build_defs method. It may also
    inherit from Resolvable or implement get_model_cls to support instantiation
    via yaml.
    """

    @classmethod
    def __dg_package_entry__(cls) -> None: ...

    @classmethod
    def get_schema(cls) -> Optional[type[BaseModel]]:
        return None

    @classmethod
    def get_spec(cls) -> ComponentTypeSpec:
        return ComponentTypeSpec()

    @classmethod
    def get_model_cls(cls) -> Optional[type[BaseModel]]:
        if issubclass(cls, Resolvable):
            return cls.model()

        # handle existing overrides for backwards compatibility
        cls_from_get_schema = cls.get_schema()
        if cls_from_get_schema:
            return cls_from_get_schema

        return None

    @classmethod
    def get_additional_scope(cls) -> Mapping[str, Any]:
        return {}

    @abstractmethod
    def build_defs(self, context: "ComponentLoadContext") -> Definitions: ...

    @classmethod
    def load(cls, attributes: Optional[BaseModel], context: "ComponentLoadContext") -> Self:
        if issubclass(cls, Resolvable):
            return (
                cls.resolve_from_model(
                    context.resolution_context.at_path("attributes"),
                    attributes,
                )
                if attributes
                else cls()
            )
        else:
            # If the Component does not implement anything from Resolved, try to instantiate it without
            # argument.
            return cls()

    @classmethod
    def get_code_references_for_yaml(
        cls, yaml_path: Path, source_position: SourcePosition, context: "ComponentLoadContext"
    ) -> Sequence[CodeReference]:
        """Returns a list of code references for a component which has been defined in a YAML file.

        Args:
            yaml_path (Path): The path to the YAML file where this component is defined.
            source_position (SourcePosition): The source position of the component in the YAML file.
            context (ComponentLoadContext): The context in which the component is being loaded.
        """
        return [
            LocalFileCodeReference(file_path=str(yaml_path), line_number=source_position.start.line)
        ]

    @classmethod
    def get_description(cls) -> Optional[str]:
        return cls.get_spec().description or inspect.getdoc(cls)
