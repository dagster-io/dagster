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
from dagster.components.component.template_vars import get_context_free_static_template_vars
from dagster.components.resolved.base import Resolvable
from dagster.components.resolved.model import Model
from dagster.components.scaffold.scaffold import scaffold_with

if TYPE_CHECKING:
    from dagster.components.core.context import ComponentLoadContext
    from dagster.components.core.decl import ComponentDecl


class EmptyAttributesModel(Model):
    """Represents a model that should explicitly have no fields set."""

    pass


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
    """Abstract base class for creating Dagster components.

    Components are the primary building blocks for programmatically creating Dagster
    definitions. They enable building multiple interrelated definitions for specific use cases,
    provide schema-based configuration, and built-in scaffolding support to simplify
    component instantiation in projects. Components are automatically discovered by
    Dagster tooling and can be instantiated from YAML configuration files or Python code that
    conform to the declared schema.

    Key Capabilities:
    - **Definition Factory**: Creates Dagster assets, jobs, schedules, and other definitions
    - **Schema-Based Configuration**: Optional parameterization via YAML or Python objects
    - **Scaffolding Support**: Custom project structure generation via ``dg scaffold`` commands
    - **Tool Integration**: Automatic discovery by Dagster CLI and UI tools
    - **Testing Utilities**: Built-in methods for testing component behavior

    Implementing a component:
    - Every component must implement the ``build_defs()`` method, which serves as a factory for creating Dagster definitions.
    - Components can optionally inherit from ``Resolvable`` to add schema-based configuration capabilities, enabling parameterization through YAML files or structured Python objects.
    - Components can attach a custom scaffolder with the ``@scaffold_with`` decorator.

    Examples:
        Simple component with hardcoded definitions:

        .. code-block:: python

            import dagster as dg

            class SimpleDataComponent(dg.Component):
                \"\"\"Component that creates a toy, hardcoded data processing asset.\"\"\"

                def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
                    @dg.asset
                    def raw_data():
                        return [1, 2, 3, 4, 5]

                    @dg.asset
                    def processed_data(raw_data):
                        return [x * 2 for x in raw_data]

                    return dg.Definitions(assets=[raw_data, processed_data])

        Configurable component with schema:

        .. code-block:: python

            import dagster as dg
            from typing import List

            class DatabaseTableComponent(dg.Component, dg.Resolvable, dg.Model):
                \"\"\"Component for creating assets from database tables.\"\"\"

                table_name: str
                columns: List[str]
                database_url: str = "postgresql://localhost/mydb"

                def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
                    @dg.asset(key=f"{self.table_name}_data")
                    def table_asset():
                        # Use self.table_name, self.columns, etc.
                        return execute_query(f"SELECT {', '.join(self.columns)} FROM {self.table_name}")

                    return dg.Definitions(assets=[table_asset])

        Using the component in a YAML file (``defs.yaml``):

        .. code-block:: yaml

            type: my_project.components.DatabaseTableComponent
            attributes:
              table_name: "users"
              columns: ["id", "name", "email"]
              database_url: "postgresql://prod-db/analytics"

    Component Discovery:

    Components are automatically discovered by Dagster tooling when defined in modules
    specified in your project's ``pyproject.toml`` registry configuration:

    .. code-block:: toml

        [tool.dagster]
        module_name = "my_project"
        registry_modules = ["my_project.components"]

    This enables CLI commands like:

    .. code-block:: bash

        dg list components # List all available components in the Python environment
        dg scaffold defs MyComponent path/to/component  # Generate component instance with scaffolding

    Schema and Configuration:

    To make a component configurable, inherit from both ``Component`` and ``Resolvable``,
    along with a model base class. Pydantic models and dataclasses are supported largely
    so that pre-existing code can be used as schema without having to modify it. We recommend
    using ``dg.Model`` for new components, which wraps Pydantic with Dagster defaults for better
    developer experience.

    - ``dg.Model``: Recommended for new components (wraps Pydantic with Dagster defaults)
    - ``pydantic.BaseModel``: Direct Pydantic usage
    - ``@dataclass``: Python dataclasses with validation

    Custom Scaffolding:

    Components can provide custom scaffolding behavior using the ``@scaffold_with`` decorator:

    .. code-block:: python

        import textwrap

        import dagster as dg
        from dagster.components import Scaffolder, ScaffoldRequest


        class DatabaseComponentScaffolder(Scaffolder):
            def scaffold(self, request: ScaffoldRequest) -> None:
                # Create component directory
                component_dir = request.target_path
                component_dir.mkdir(parents=True, exist_ok=True)

                # Generate defs.yaml with template
                defs_file = component_dir / "defs.yaml"
                defs_file.write_text(
                    textwrap.dedent(
                        f'''
                    type: {request.type_name}
                    attributes:
                        table_name: "example_table"
                        columns: ["id", "name"]
                        database_url: "${{DATABASE_URL}}"
                '''.strip()
                    )
                )

                # Generate SQL query template
                sql_file = component_dir / "query.sql"
                sql_file.write_text("SELECT * FROM example_table;")


        @dg.scaffold_with(DatabaseComponentScaffolder)
        class DatabaseTableComponent(dg.Component, dg.Resolvable, dg.Model):
            table_name: str
            columns: list[str]

            def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
                # Component implementation
                pass

    See Also:
        - :py:class:`dagster.Definitions`: The object returned by ``build_defs()``
        - :py:class:`dagster.ComponentLoadContext`: Context provided to ``build_defs()``
        - :py:class:`dagster.components.resolved.base.Resolvable`: Base for configurable components
        - :py:class:`dagster.Model`: Recommended base class for component schemas
        - :py:func:`dagster.scaffold_with`: Decorator for custom scaffolding

    """

    @classmethod
    def get_decl_type(cls) -> type["ComponentDecl"]:
        from dagster.components.core.decl import YamlDecl

        return YamlDecl

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

        # explicitly mark that the component has no attributes
        return EmptyAttributesModel

    @classmethod
    def get_additional_scope(cls) -> Mapping[str, Any]:
        return get_context_free_static_template_vars(cls)

    @abstractmethod
    def build_defs(self, context: "ComponentLoadContext") -> Definitions: ...

    @classmethod
    def load(cls, attributes: Optional[BaseModel], context: "ComponentLoadContext") -> Self:
        if issubclass(cls, Resolvable):
            context_with_injected_scope = context.with_rendering_scope(
                {
                    "load_component_at_path": context.load_component_at_path,
                    "build_defs_at_path": context.build_defs_at_path,
                }
            )
            return (
                cls.resolve_from_model(
                    context_with_injected_scope.resolution_context.at_path("attributes"),
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
        from dagster.components.core.component_tree import ComponentTree

        model_cls = cls.get_model_cls()
        assert model_cls
        model = TypeAdapter(model_cls).validate_python(attributes)
        return cls.load(model, context if context else ComponentTree.for_test().load_context)

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
        from dagster.components.core.component_tree import ComponentTree
        from dagster.components.core.defs_module import load_yaml_component_from_path

        return load_yaml_component_from_path(
            context=context or ComponentTree.for_test().load_context,
            component_def_path=yaml_path,
        )
