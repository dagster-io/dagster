import inspect
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from dagster_shared.record import IHaveNew, record_custom
from dagster_shared.yaml_utils.source_position import SourcePosition
from pydantic import BaseModel, TypeAdapter
from typing_extensions import Self

import dagster._check as check
from dagster._annotations import PublicAttr, public
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.metadata.source_code import CodeReference, LocalFileCodeReference
from dagster._core.definitions.utils import validate_component_owner
from dagster.components.component.component_scaffolder import DefaultComponentScaffolder
from dagster.components.component.template_vars import get_static_template_vars
from dagster.components.resolved.base import Resolvable
from dagster.components.scaffold.scaffold import scaffold_with

if TYPE_CHECKING:
    from dagster.components.core.context import ComponentLoadContext


@public
@record_custom
class ComponentTypeSpec(IHaveNew):
    """Specifies the core attributes of a component. Used when defining custom components.

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
@scaffold_with(DefaultComponentScaffolder)
class Component(ABC):
    """A component is a class that creates Dagster definitions. Inherit from it when creating a custom component.

    Components have a few responsibilities:

    - A definitions factory: Implement the build_defs function, which creates the definitions
    - Optionally specify schema via Resolvable. This is used to instantiate the component and provide schema
      to yaml files that can configure the component. The schema also has integrated documenation,
      surfaced in the Dagster UI.
    - Optionally specify a scaffolder. This is used to scaffold the component when invoking tools such as
      `dg scaffold defs` and

    **Definitions Factory**:

    The workhouse function of a component is the build_defs methods, implemented by the user when
    defining a custom component . This is called by framework when it is crawling the defs folder
    of a project to create the definitions for that project.

    This is also called in testing utilities with context objects with parameters that simulate
    the loading process. You may also directly invoke build_defs in tests if so desired.

    **Schema**:

    Optionally a Component can specify a schema used when instantiating the component. To do this
    you make a component inherit from Resolvable.

    The Resolvable abstract class can be used with @dataclass, pydantic.BaseModel, or dagster.Model (which
    lightly wraps pydantic.BaseModel). It is up to the user to decide. Prefer dagster.Model for
    new components or schema classes, as it sets defaults that result in the best error messages and
    user experience.

    Resolvable allows a component parameterized with a yaml file or Python business objects. Its role
    in the system is to manage the resolution and mapping between the schema and those business objects.

    **Scaffolding**:

    Components can also define custom scaffolding with the @scaffold_with decorator. This decorator
    takes a Scaffolder subtype, which specifies custom scaffolding for the component. This scaffolding
    can provide default structure for its corresponding defs.yaml file, stubs for integration-specific
    configuration files. Scaffold parameters can be passed to the scaffolder via dg scaffold defs.

    Components are discoverable by Dagster tooling in a project that specifies registry modules in its
    pyproject.toml or setup.py. These modules are inspected by tools such as dg for components, which
    are then in turn discoverable by users by commands `dg list components` or `dg scaffold defs`. These
    componets always appear in automatically generated documentation in the Dagster UI.

    Examples:
    A component that creates a single, hardcoded asset.

    .. code-block:: python

        class MyComponent(dg.Component):
            def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
                @dg.asset
                def dummy_asset() -> None: ...

                return dg.Definitions(assets=[dummy_asset])

    A component that creates a single asset and is parameterized with a yaml file.

    .. code-block:: python

        class ReturnValueComponent(dg.Component, dg.Resolvable, dg.Model):
            value: str

            def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
                @dg.asset
                def return_value_asset() -> None:
                    return self.value

                return dg.Definitions(assets=[return_value_asset])
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
        return get_static_template_vars(cls)

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

    @classmethod
    def from_attributes_dict(
        cls, *, attributes: dict, context: Optional["ComponentLoadContext"] = None
    ) -> Self:
        """Load a Component from a dictionary. The dictionary is what would exist in the component.yaml file
        under the "attributes" key.

        Examples:

        .. code-block:: python

            class ModelComponentWithDeclaration(Component, Model, Resolvable):
                value: str

                def build_defs(self, context: ComponentLoadContext) -> Definitions: ...

            assert (
                component_defs(
                    component=ModelComponentWithDeclaration.from_attributes_dict(attributes={"value": "foobar"}),
                ).get_assets_def("an_asset")()
                == "foobar"
            )

        Args:
            attributes (dict): The attributes to load the Component from.
            context (Optional[ComponentLoadContext]): The context to load the Component from.

        Returns:
            A Component instance.
        """
        from dagster.components.core.context import ComponentLoadContext

        model_cls = cls.get_model_cls()
        assert model_cls
        model = TypeAdapter(model_cls).validate_python(attributes)
        return cls.load(model, context if context else ComponentLoadContext.for_test())

    @classmethod
    def from_yaml_path(
        cls, yaml_path: Path, context: Optional["ComponentLoadContext"] = None
    ) -> "Component":
        """Load a Component from a yaml file.

        Args:
            yaml_path (Path): The path to the yaml file.
            context (Optional[ComponentLoadContext]): The context to load the Component from. Defaults to a test context.

        Returns:
            A Component instance.
        """
        from dagster.components.core.context import ComponentLoadContext
        from dagster.components.core.defs_module import load_yaml_component_from_path

        return load_yaml_component_from_path(
            context=context or ComponentLoadContext.for_test(), component_def_path=yaml_path
        )
