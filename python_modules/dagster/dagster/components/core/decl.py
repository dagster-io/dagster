import abc
import inspect
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import nullcontext
from functools import cached_property
from pathlib import Path
from typing import Generic, TypeVar, cast

from dagster_shared.record import record
from dagster_shared.serdes.objects import EnvRegistryKey
from dagster_shared.seven import load_module_object
from dagster_shared.yaml_utils import (
    parse_yaml_with_source_position,
    parse_yamls_with_source_position,
)
from dagster_shared.yaml_utils.source_position import SourcePosition, ValueAndSourcePositionTree
from pydantic import BaseModel, TypeAdapter

import dagster._check as check
from dagster._core.definitions.definitions_load_context import DefinitionsLoadContext
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._utils.pydantic_yaml import (
    _parse_and_populate_model_with_annotated_errors,
    enrich_validation_errors_with_source_position,
)
from dagster.components.component.app_managed_state import (
    AppManagedComponentEntry,
    import_component_class,
)
from dagster.components.component.component import Component, EmptyAttributesModel
from dagster.components.component.component_loader import is_component_loader
from dagster.components.core.context import ComponentDeclLoadContext, ComponentLoadContext
from dagster.components.core.defs_module import (
    EXPLICITLY_IGNORED_GLOB_PATTERNS,
    AppManagedDefinitionsComponent,
    ComponentFileModel,
    ComponentLoc,
    ComponentPath,
    ComponentRootComponent,
    CompositeYamlComponent,
    DefsFolderComponent,
    PythonFileComponent,
    asset_post_processor_list_from_post_processing_dict,
    context_with_injected_scope,
    find_defs_or_component_yaml,
)
from dagster.components.resolved.core_models import AssetPostProcessor

T = TypeVar("T", bound=Component)


@record
class ComponentDecl(abc.ABC, Generic[T]):
    """Class representing a not-yet-loaded component in the defs hierarchy. In effect, a closure
    with all information needed to load the component. A tree of component decls is initially
    built before any components are loaded.
    """

    context: ComponentDeclLoadContext
    loc: ComponentLoc

    @abc.abstractmethod
    def _load_component(self) -> T:
        """Loads the component represented by this decl."""
        ...

    @property
    @abc.abstractmethod
    def component_type(self) -> type[T]: ...

    def iterate_all_component_decls(self) -> Iterator["ComponentDecl"]:
        for _, component in self.iterate_loc_component_decl_pairs():
            yield component

    def iterate_child_component_decls(self) -> Iterator["ComponentDecl"]:
        return iter([])

    def iterate_loc_component_decl_pairs(
        self,
    ) -> Iterator[tuple[ComponentLoc, "ComponentDecl"]]:
        yield self.loc, self
        for child in self.iterate_child_component_decls():
            yield from child.iterate_loc_component_decl_pairs()


@record
class ComponentLoaderDecl(ComponentDecl[Component]):
    """Declaration of a component that is loaded by a user-defined Python function."""

    component_node_fn: Callable[[ComponentDeclLoadContext], Component]

    def _load_component(self) -> Component:
        return self.component_node_fn(self.context)

    @property
    def component_type(self) -> type[Component]:
        # parse from function return type if possible
        sig = inspect.signature(self.component_node_fn)
        return sig.return_annotation or Component


@record
class PythonFileDecl(ComponentDecl[PythonFileComponent]):
    """Declaration of a PythonFileComponent, corresponding to a Python file with zero or more
    ComponentLoaderDecls and zero or more plain Dagster defs.
    """

    decls: Mapping[str, ComponentLoaderDecl]

    def _load_component(self) -> "PythonFileComponent":
        component_path = check.inst(self.loc, ComponentPath)
        return PythonFileComponent(
            components={
                attr: self.context.load_structural_component_at_loc(decl.loc)
                for attr, decl in self.decls.items()
            },
            path=component_path.file_path,
        )

    @property
    def component_type(self) -> type[PythonFileComponent]:
        return PythonFileComponent

    def iterate_child_component_decls(self) -> Iterator["ComponentDecl"]:
        yield from self.decls.values()


def _get_component_class(
    context: ComponentDeclLoadContext, component_file_model: ComponentFileModel
) -> type[Component]:
    # TODO: lookup in cache so we don't have to import the class directly
    type_str = context.normalize_component_type_str(component_file_model.type)
    key = EnvRegistryKey.from_typename(type_str)
    obj = load_module_object(key.namespace, key.name)
    if not isinstance(obj, type) or not issubclass(obj, Component):
        raise DagsterInvalidDefinitionError(
            f"Component type {type_str} is of type {type(obj)}, but must be a subclass of dagster.Component"
        )

    return obj


def _process_attributes_with_enriched_validation_err(
    source_tree: ValueAndSourcePositionTree | None,
    component_file_model: ComponentFileModel | None,
    model_cls: type[BaseModel] | None,
) -> BaseModel | None:
    if (
        model_cls is None
        or not source_tree
        or not component_file_model
        or not component_file_model.attributes
    ):
        return None

    attributes_position_tree = source_tree.source_position_tree.children.get("attributes", None)
    with (
        enrich_validation_errors_with_source_position(attributes_position_tree, ["attributes"])
        if attributes_position_tree
        else nullcontext()
    ):
        if issubclass(model_cls, EmptyAttributesModel):
            raise DagsterInvalidDefinitionError(
                "Component is not resolvable from YAML, but attributes were provided. This error can be avoided by "
                "making the component a subclass of `Resolvable` or by overriding `get_model_cls` on your component."
            )

        return TypeAdapter(model_cls).validate_python(component_file_model.attributes)


@record
class YamlBackedComponentDecl(ComponentDecl[T]):
    source_tree: ValueAndSourcePositionTree | None
    component_file_model: ComponentFileModel | None

    @cached_property
    def context_with_component_injected_scope(self) -> ComponentDeclLoadContext:
        if not self.component_file_model:
            return self.context
        return context_with_injected_scope(
            self.context,
            self.component_type,
            self.component_file_model.template_vars_module,
        )

    @property
    def component_type(self) -> type[T]:
        """The class of the component that is being loaded."""
        return cast(
            "type[T]",
            _get_component_class(self.context, check.not_none(self.component_file_model)),
        )

    def get_asset_post_processor_lists(self) -> list[AssetPostProcessor]:
        if not self.source_tree or not self.component_file_model:
            return []

        post_processing_position_tree = self.source_tree.source_position_tree.children.get(
            "post_processing", None
        )
        with (
            enrich_validation_errors_with_source_position(
                post_processing_position_tree, ["post_processing"]
            )
            if post_processing_position_tree
            else nullcontext()
        ):
            return asset_post_processor_list_from_post_processing_dict(
                self.context_with_component_injected_scope.resolution_context,
                self.component_file_model.post_processing,
            )


@record
class YamlDecl(YamlBackedComponentDecl):
    """Declaration of a single component loaded from a YAML file."""

    @staticmethod
    def from_source_tree(
        context: ComponentDeclLoadContext,
        source_tree: ValueAndSourcePositionTree,
        path: ComponentPath,
    ) -> "YamlDecl":
        component_file_model = _parse_and_populate_model_with_annotated_errors(
            cls=ComponentFileModel, obj_parse_root=source_tree, obj_key_path_prefix=[]
        )
        return YamlDecl(
            context=context,
            source_tree=source_tree,
            component_file_model=component_file_model,
            loc=path,
        )

    def _load_component(self) -> "Component":
        context = self.context_with_component_injected_scope.with_source_position_tree(
            check.not_none(self.source_tree).source_position_tree,
        )

        model_cls = self.component_type.get_model_cls()

        attributes = _process_attributes_with_enriched_validation_err(
            self.source_tree, self.component_file_model, model_cls
        )

        return self.component_type.load(
            attributes, ComponentLoadContext.from_decl_load_context(context, self)
        )


@record
class YamlFileDecl(ComponentDecl[CompositeYamlComponent]):
    """Declaration of a CompositeYamlComponent, corresponding to a YAML file with one or more
    YamlDecls.
    """

    decls: Sequence[YamlBackedComponentDecl]
    source_positions: Sequence[SourcePosition]

    def _load_component(self) -> "CompositeYamlComponent":
        return CompositeYamlComponent(
            components=[
                self.context.load_structural_component_at_loc(decl.loc) for decl in self.decls
            ],
            source_positions=self.source_positions,
            asset_post_processor_lists=[
                decl.get_asset_post_processor_lists() for decl in self.decls
            ],
        )

    @property
    def component_type(self) -> type[CompositeYamlComponent]:
        return CompositeYamlComponent

    def iterate_child_component_decls(self) -> Iterator["ComponentDecl"]:
        yield from self.decls


@record
class DefsFolderDecl(YamlBackedComponentDecl[DefsFolderComponent]):
    children: Mapping[Path, ComponentDecl]

    @classmethod
    def get(cls, context: ComponentDeclLoadContext) -> "DefsFolderDecl":
        component = build_filesystem_component_decl_from_context(context)
        return check.inst(
            component,
            DefsFolderDecl,
            f"Expected DefsFolderDecl at {context.path}, got {component}.",
        )

    @property
    def component_type(self) -> type[DefsFolderComponent]:
        return DefsFolderComponent

    def _load_component(self) -> "DefsFolderComponent":
        _process_attributes_with_enriched_validation_err(
            self.source_tree, self.component_file_model, DefsFolderComponent.get_model_cls()
        )
        component_path = check.inst(self.loc, ComponentPath)
        return DefsFolderComponent(
            path=component_path.file_path,
            children={
                subpath: self.context.load_structural_component_at_loc(decl.loc)
                for subpath, decl in self.children.items()
            },
        )

    def iterate_child_component_decls(self) -> Iterator["ComponentDecl"]:
        yield from self.children.values()


@record
class AppManagedComponentDecl(ComponentDecl[Component]):
    """Declaration for a single app-managed component.

    Each app-managed component has its own state key in storage. The
    ``instance_key`` on the decl's loc (a ``AppManagedDefinitionsLoc``) is the
    component id that addresses its storage entry, mirroring how
    ``YamlDecl`` uses an instance key to distinguish multiple components
    in a single yaml file.

    The entry payload (component type + attributes) is fetched lazily on
    first access. Building the decl tree is a metadata-only operation —
    it costs one cursor read for the whole listing, regardless of how
    many UI components exist. The per-component download only happens
    when the decl is actually loaded (i.e. when ``build_defs`` reaches
    this loc), so tree walks that don't need the entries (string
    rendering, loc enumeration, type filtering on filesystem-only
    queries) pay no per-component download cost.
    """

    location_name: str
    component_id: str

    @cached_property
    def entry(self) -> AppManagedComponentEntry:
        from dagster._core.storage.defs_state.base import DefsStateStorage
        from dagster.components.component.app_managed_state import (
            get_app_managed_component_state_key,
            read_app_managed_component_entry_at_version,
        )

        storage = check.not_none(
            DefsStateStorage.get(),
            "DefsStateStorage must be available to load a app-managed component.",
        )
        # Resolve the version through the pinned DefinitionsLoadContext so that
        # entry bytes are consistent with the listing in
        # ComponentTree._build_app_managed_definitions_decl, even when storage has moved
        # past the snapshot we're loading against (RECONSTRUCTION, or an
        # explicit ReloadCodeWithState pin).
        key = get_app_managed_component_state_key(self.location_name, self.component_id)
        key_info = check.not_none(
            DefinitionsLoadContext.get().get_defs_key_state_info(key),
            f"No state version pinned for UI component {self.component_id} in location"
            f" {self.location_name} — it may have been deleted concurrently.",
        )
        return read_app_managed_component_entry_at_version(
            storage, self.location_name, self.component_id, key_info.version
        )

    @property
    def component_type(self) -> type[Component]:
        return import_component_class(self.entry.component_type)

    def _load_component(self) -> Component:
        cls = self.component_type
        model_cls = cls.get_model_cls()
        model = None
        if model_cls and self.entry.attributes.strip():
            parsed = parse_yaml_with_source_position(self.entry.attributes).value
            if parsed is not None:
                model = TypeAdapter(model_cls).validate_python(parsed)
        load_context = ComponentLoadContext.from_decl_load_context(self.context, self)
        return cls.load(model, load_context)


@record
class AppManagedDefinitionsDecl(ComponentDecl[AppManagedDefinitionsComponent]):
    """Declaration for the UI-definitions subtree at a code location.

    Aggregates ``AppManagedComponentDecl`` children, one per app-managed entry
    discovered in storage. Mirrors the structural role of
    ``YamlFileDecl`` for yaml-defined components: a single named node
    that bundles the components beneath it. The list of children is
    rebuilt fresh on every ``find_root_decl`` call (since the listing
    step is cheap), but each child's decl is cached individually.
    """

    location_name: str
    children: Sequence[AppManagedComponentDecl]

    def _load_component(self) -> AppManagedDefinitionsComponent:
        return AppManagedDefinitionsComponent()

    @property
    def component_type(self) -> type[AppManagedDefinitionsComponent]:
        return AppManagedDefinitionsComponent

    def iterate_child_component_decls(self) -> Iterator["ComponentDecl"]:
        yield from self.children


@record
class ComponentRootDecl(ComponentDecl[ComponentRootComponent]):
    """Declaration for the unified root of the component tree.

    Holds a flat list of child decls. Not cached itself — always freshly
    constructed by ``ComponentTree.find_root_decl`` from independently
    cached parts.
    """

    decls: Sequence[ComponentDecl]

    def _load_component(self) -> ComponentRootComponent:
        return ComponentRootComponent(
            components=[
                self.context.load_structural_component_at_loc(decl.loc) for decl in self.decls
            ],
        )

    @property
    def component_type(self) -> type[ComponentRootComponent]:
        return ComponentRootComponent

    def iterate_child_component_decls(self) -> Iterator["ComponentDecl"]:
        yield from self.decls


def build_filesystem_component_decl_from_context(
    context: ComponentDeclLoadContext,
) -> ComponentDecl | None:
    """Attempts to determine the type of component that should be loaded for the given context.  Iterates through potential component
    type matches, prioritizing more specific types: YAML, Python, plain Dagster defs, and component
    folder.
    """
    # in priority order
    # yaml component
    if find_defs_or_component_yaml(context.path):
        return build_component_decl_from_yaml_file_backcompat(context)
    # defs
    elif (
        context.terminate_autoloading_on_keyword_files
        and (context.path / "definitions.py").exists()
        and not (context.path / "component.py").exists()
    ):
        return PythonFileDecl(
            context=context,
            loc=ComponentPath.from_path(context.path / "definitions.py"),
            decls={},
        )
    elif context.path.suffix == ".py":
        return build_component_decl_from_python_file(context)
    # folder
    elif context.path.is_dir():
        children = build_component_decls_from_directory_items(context, None)
        if children:
            return DefsFolderDecl(
                context=context,
                loc=ComponentPath.from_path(context.path),
                children=children,
                source_tree=None,
                component_file_model=None,
            )

    return None


def build_component_decls_from_directory_items(
    context: ComponentDeclLoadContext, component_file_model: ComponentFileModel | None
) -> Mapping[Path, ComponentDecl]:
    found = {}
    for subpath in sorted(context.path.iterdir()):
        relative_subpath = subpath.relative_to(context.path)
        if any(relative_subpath.match(pattern) for pattern in EXPLICITLY_IGNORED_GLOB_PATTERNS):
            continue
        path_context = context_with_injected_scope(
            context,
            DefsFolderComponent,
            component_file_model.template_vars_module if component_file_model else None,
        ).for_component_loc(ComponentPath.from_path(subpath))

        component_node = build_filesystem_component_decl_from_context(path_context)
        if component_node:
            found[subpath] = component_node
    return found


def build_component_decl_from_python_file(
    context: ComponentDeclLoadContext,
) -> ComponentLoaderDecl | PythonFileDecl:
    # backcompat for component.yaml
    component_def_path = context.path
    module = context.load_defs_relative_python_module(component_def_path)
    component_loaders = list(inspect.getmembers(module, is_component_loader))

    return PythonFileDecl(
        loc=ComponentPath.from_path(context.path),
        context=context,
        decls={
            attr: ComponentLoaderDecl(
                context=context.for_component_loc(ComponentPath.from_path(context.path, attr)),
                component_node_fn=component_loader,
                loc=ComponentPath.from_path(context.path, attr),
            )
            for attr, component_loader in component_loaders
        },
    )


def build_component_decl_from_yaml_file_backcompat(
    context: ComponentDeclLoadContext,
) -> ComponentDecl:
    component_def_path = check.not_none(find_defs_or_component_yaml(context.path))
    return build_component_decl_from_yaml_file(
        context=context, component_def_path=component_def_path
    )


def build_component_decl_from_yaml_file(
    context: ComponentDeclLoadContext, component_def_path: Path
) -> ComponentDecl:
    source_trees = parse_yamls_with_source_position(
        component_def_path.read_text(), str(component_def_path)
    )
    component_nodes = []
    for i, source_tree in enumerate(source_trees):
        component_nodes.append(
            build_component_decl_from_yaml_document(
                context=context.for_component_loc(ComponentPath.from_path(context.path, i)),
                source_tree=source_tree,
                path=ComponentPath.from_path(context.path, i),
            )
        )

    check.invariant(len(component_nodes) > 0, "No components found in YAML file")
    return YamlFileDecl(
        loc=ComponentPath.from_path(context.path),
        context=context,
        decls=component_nodes,  # ty: ignore[invalid-argument-type]
        source_positions=[
            source_tree.source_position_tree.position for source_tree in source_trees
        ],
    )


def build_component_decl_from_yaml_document(
    context: ComponentDeclLoadContext,
    source_tree: ValueAndSourcePositionTree,
    path: ComponentPath,
) -> ComponentDecl:
    component_file_model = _parse_and_populate_model_with_annotated_errors(
        cls=ComponentFileModel, obj_parse_root=source_tree, obj_key_path_prefix=[]
    )
    component_cls = _get_component_class(context, component_file_model)
    component_decl_type = component_cls.get_decl_type()
    check.invariant(component_decl_type in (YamlDecl, DefsFolderDecl))

    if component_decl_type == DefsFolderDecl:
        children = build_component_decls_from_directory_items(context, component_file_model)
        return DefsFolderDecl(
            context=context,
            loc=path,
            children=children,
            source_tree=source_tree,
            component_file_model=component_file_model,
        )
    else:
        return YamlDecl(
            context=context,
            source_tree=source_tree,
            component_file_model=component_file_model,
            loc=path,
        )
