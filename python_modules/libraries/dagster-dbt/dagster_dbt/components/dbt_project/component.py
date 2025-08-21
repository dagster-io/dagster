from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Annotated, Any, Optional, Union

from dagster import Resolvable
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._utils.cached_method import cached_method
from dagster.components.component.component import Component
from dagster.components.core.component_tree import ComponentTree
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.core_models import OpSpec, ResolutionContext
from dagster.components.resolved.model import Resolver
from dagster.components.scaffold.scaffold import scaffold_with
from dagster.components.utils.translation import TranslationFn, TranslationFnResolver

from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.asset_utils import DBT_DEFAULT_EXCLUDE, DBT_DEFAULT_SELECT, get_node
from dagster_dbt.components.dbt_project.scaffolder import DbtProjectComponentScaffolder
from dagster_dbt.core.resource import DbtCliResource
from dagster_dbt.dagster_dbt_translator import (
    DagsterDbtTranslator,
    DagsterDbtTranslatorSettings,
    validate_translator,
)
from dagster_dbt.dbt_manifest import validate_manifest
from dagster_dbt.dbt_manifest_asset_selection import DbtManifestAssetSelection
from dagster_dbt.dbt_project import DbtProject
from dagster_dbt.utils import ASSET_RESOURCE_TYPES


@dataclass(frozen=True)
class DagsterDbtComponentsTranslatorSettings(DagsterDbtTranslatorSettings):
    """Subclass of DagsterDbtTranslatorSettings that enables code references by default."""

    enable_code_references: bool = True


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

    project: Annotated[
        DbtProject,
        Resolver(
            resolve_dbt_project,
            model_field_type=Union[str, DbtProjectArgs.model()],
            description="The path to the dbt project or a mapping defining a DbtProject",
            examples=[
                "{{ project_root }}/path/to/dbt_project",
                {
                    "project_dir": "path/to/dbt_project",
                    "profile": "your_profile",
                    "target": "your_target",
                },
            ],
        ),
    ]
    op: Annotated[
        Optional[OpSpec],
        Resolver.default(
            description="Op related arguments to set on the generated @dbt_assets",
            examples=[
                {
                    "name": "some_op",
                    "tags": {"tag1": "value"},
                    "backfill_policy": {"type": "single_run"},
                },
            ],
        ),
    ] = None
    translation: Annotated[
        Optional[TranslationFn[Mapping[str, Any]]],
        TranslationFnResolver(template_vars_for_translation_fn=lambda data: {"node": data}),
    ] = None
    select: Annotated[
        str,
        Resolver.default(
            description="The dbt selection string for models in the project you want to include.",
            examples=["tag:dagster"],
        ),
    ] = DBT_DEFAULT_SELECT
    exclude: Annotated[
        str,
        Resolver.default(
            description="The dbt selection string for models in the project you want to exclude.",
            examples=["tag:skip_dagster"],
        ),
    ] = DBT_DEFAULT_EXCLUDE
    translation_settings: Annotated[
        Optional[DagsterDbtComponentsTranslatorSettings],
        Resolver.default(
            description="Allows enabling or disabling various features for translating dbt models in to Dagster assets.",
            examples=[
                {
                    "enable_source_tests_as_checks": True,
                },
            ],
        ),
    ] = None
    prepare_if_dev: Annotated[
        bool,
        Resolver.default(
            description="Whether to prepare the dbt project every time in `dagster dev` or `dg` cli calls."
        ),
    ] = True

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
        self, select: str, exclude: str = DBT_DEFAULT_EXCLUDE
    ) -> DbtManifestAssetSelection:
        return DbtManifestAssetSelection.build(
            manifest=self.project.manifest_path,
            dagster_dbt_translator=self.translator,
            select=select,
            exclude=exclude,
        )

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        if self.prepare_if_dev:
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

    @cached_property
    def _validated_manifest(self):
        return validate_manifest(self.project.manifest_path)

    @cached_property
    def _validated_translator(self):
        return validate_translator(self.translator)

    @cached_method
    def asset_key_for_model(self, model_name: str) -> AssetKey:
        dagster_dbt_translator = self._validated_translator
        manifest = self._validated_manifest

        matching_model_ids = [
            unique_id
            for unique_id, value in manifest["nodes"].items()
            if value["name"] == model_name and value["resource_type"] in ASSET_RESOURCE_TYPES
        ]

        if len(matching_model_ids) == 0:
            raise KeyError(f"Could not find a dbt model, seed, or snapshot with name: {model_name}")

        return dagster_dbt_translator.get_asset_spec(
            manifest,
            next(iter(matching_model_ids)),
            self.project,
        ).key


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
    project_components = ComponentTree.for_project(components).get_all_components(
        of_type=DbtProjectComponent
    )

    return [component.project for component in project_components]
