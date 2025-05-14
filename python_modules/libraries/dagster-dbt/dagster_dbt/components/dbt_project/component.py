import importlib
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Annotated, Any, Callable, Optional, Union, cast

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components import Resolvable
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.core.defs_module import DefsFolderComponent
from dagster.components.resolved.core_models import AssetAttributesModel, OpSpec, ResolutionContext
from dagster.components.resolved.model import Resolver
from dagster.components.scaffold.scaffold import scaffold_with
from dagster.components.utils import TranslatorResolvingInfo
from typing_extensions import TypeAlias

from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.asset_utils import get_asset_key_for_model, get_node
from dagster_dbt.components.dbt_project.scaffolder import DbtProjectComponentScaffolder
from dagster_dbt.core.resource import DbtCliResource
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, DagsterDbtTranslatorSettings
from dagster_dbt.dbt_manifest_asset_selection import DbtManifestAssetSelection
from dagster_dbt.dbt_project import DbtProject

if TYPE_CHECKING:
    from dagster._core.definitions.assets import AssetsDefinition

TranslationFn: TypeAlias = Callable[[AssetSpec, Mapping[str, Any]], AssetSpec]


@dataclass(frozen=True)
class DagsterDbtComponentsTranslatorSettings(DagsterDbtTranslatorSettings):
    """Subclass of DagsterDbtTranslatorSettings that enables code references by default."""

    enable_code_references: bool = True


def resolve_translation(context: ResolutionContext, model):
    info = TranslatorResolvingInfo(
        "node",
        asset_attributes=model,
        resolution_context=context,
        model_key="translation",
    )
    return lambda base_asset_spec, dbt_props: info.get_asset_spec(
        base_asset_spec,
        {
            "node": dbt_props,
            "spec": base_asset_spec,
        },
    )


ResolvedTranslationFn: TypeAlias = Annotated[
    TranslationFn,
    Resolver(
        resolve_translation,
        model_field_type=Union[str, AssetAttributesModel],
    ),
]


@dataclass
class DbtProjectArgs(Resolvable):
    """Aligns with DbtProject.__new__."""

    project_dir: str
    target_path: Optional[str] = None
    profiles_dir: Optional[str] = None
    profile: Optional[str] = None
    target: Optional[str] = None
    packaged_project_dir: Optional[str] = None
    state_path: Optional[str] = None


def resolve_dbt_project(context: ResolutionContext, model) -> DbtProject:
    if isinstance(model, str):
        return DbtProject(
            context.resolve_source_relative_path(
                context.resolve_value(model, as_type=str),
            )
        )

    args = DbtProjectArgs.resolve_from_model(context, model)

    kwargs = {}  # use optionally splatted kwargs to avoid redefining default value
    if args.target_path:
        kwargs["target_path"] = args.target_path

    return DbtProject(
        project_dir=context.resolve_source_relative_path(args.project_dir),
        target=args.target,
        profiles_dir=args.profiles_dir,
        state_path=args.state_path,
        packaged_project_dir=args.packaged_project_dir,
        profile=args.profile,
        **kwargs,
    )


ResolvedDbtProject: TypeAlias = Annotated[
    DbtProject,
    Resolver(
        resolve_dbt_project,
        model_field_type=Union[str, DbtProjectArgs.model()],
    ),
]


@scaffold_with(DbtProjectComponentScaffolder)
@dataclass
class DbtProjectComponent(Component, Resolvable):
    """Expose a DBT project to Dagster as a set of assets.

    This component assumes that you have already set up a dbt project. [Jaffle shop](https://github.com/dbt-labs/jaffle-shop) is their pre-existing
    example. Run `git clone --depth=1 https://github.com/dbt-labs/jaffle-shop.git jaffle_shop && rm -rf jaffle_shop/.git` to copy that project
    into your Dagster project directory.



    Scaffold by running `dagster scaffold component dagster_dbt.DbtProjectComponent --project-path path/to/your/existing/dbt_project`
    in the Dagster project directory.

    ### What is dbt?

    dbt is the industry standard for data transformation. Learn how it can help you transform
    data and deploy analytics code following software engineering best practices like
    version control, modularity, portability, CI/CD, and documentation.
    """

    project: ResolvedDbtProject
    op: Optional[OpSpec] = None
    translation: Optional[ResolvedTranslationFn] = None
    select: str = "fqn:*"
    exclude: Optional[str] = None
    translation_settings: Optional[DagsterDbtComponentsTranslatorSettings] = None

    @cached_property
    def translator(self):
        translation_settings = self.translation_settings or DagsterDbtComponentsTranslatorSettings()
        if self.translation:
            return ProxyDagsterDbtTranslator(self.translation, translation_settings)
        return DagsterDbtTranslator(translation_settings)

    @cached_property
    def cli_resource(self):
        return DbtCliResource(self.project)

    def get_asset_selection(
        self, select: str, exclude: Optional[str] = None
    ) -> DbtManifestAssetSelection:
        return DbtManifestAssetSelection.build(
            manifest=self.project.manifest_path,
            dagster_dbt_translator=self.translator,
            select=select,
            exclude=exclude,
        )

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        self.project.prepare_if_dev()

        @dbt_assets(
            manifest=self.project.manifest_path,
            project=self.project,
            name=self.op.name if self.op else self.project.name,
            op_tags=self.op.tags if self.op else None,
            dagster_dbt_translator=self.translator,
            select=self.select,
            exclude=self.exclude,
            backfill_policy=self.op.backfill_policy if self.op else None,
        )
        def _fn(context: AssetExecutionContext):
            yield from self.execute(context=context, dbt=self.cli_resource)

        defs = Definitions(assets=[_fn])
        return defs

    def execute(self, context: AssetExecutionContext, dbt: DbtCliResource) -> Iterator:
        yield from dbt.cli(["build"], context=context).stream()


def get_asset_key_for_model_from_module(
    context: ComponentLoadContext, dbt_component_module: ModuleType, model_name: str
) -> AssetKey:
    """Component-based version of dagster_dbt.get_asset_key_for_model. Returns the corresponding Dagster
    asset key for a dbt model, seed, or snapshot, loaded from the passed component path.

    Args:
        dbt_component_module (ModuleType): The module that was used to load the dbt project.
        model_name (str): The name of the dbt model, seed, or snapshot.

    Returns:
        AssetKey: The corresponding Dagster asset key.

    Examples:
        .. code-block:: python

            from dagster import asset
            from dagster.components.components.dbt_project import get_asset_key_for_model_from_module
            from dagster.components.core.component import ComponentLoadContext
            from my_project.defs import dbt_component

            ctx = ComponentLoadContext.get()

            @asset(deps={get_asset_key_for_model_from_module(ctx, dbt_component, "customers")})
            def cleaned_customers():
                ...
    """
    defs = context.load_defs(dbt_component_module)
    return get_asset_key_for_model(cast("Sequence[AssetsDefinition]", defs.assets), model_name)


class ProxyDagsterDbtTranslator(DagsterDbtTranslator):
    # get_description conflicts on Component, so cant make it directly a translator

    def __init__(self, fn: TranslationFn, settings: Optional[DagsterDbtTranslatorSettings]):
        self._fn = fn
        super().__init__(settings)

    def get_asset_spec(self, manifest, unique_id, project):
        base_asset_spec = super().get_asset_spec(manifest, unique_id, project)
        dbt_props = get_node(manifest, unique_id)
        return self._fn(base_asset_spec, dbt_props)


def get_projects_from_dbt_component(components: Path) -> list[DbtProject]:
    # defer imports for optional deps
    from dagster_dg.context import DgContext

    projects = []
    dg_context = DgContext.for_project_environment(components, command_line_config={})
    context = ComponentLoadContext.for_module(
        importlib.import_module(dg_context.defs_module_name),
        project_root=dg_context.root_path,
    )
    folder = DefsFolderComponent.get(context)
    for component in folder.iterate_components():
        if isinstance(component, DbtProjectComponent):
            projects.append(component.project)
    return projects
