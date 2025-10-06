import itertools
import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Annotated, Any, Literal, Optional, Union

import dagster as dg
from dagster._annotations import public
from dagster._utils.cached_method import cached_method
from dagster.components.core.component_tree import ComponentTree
from dagster.components.resolved.core_models import OpSpec, ResolutionContext
from dagster.components.resolved.model import Resolver
from dagster.components.scaffold.scaffold import scaffold_with
from dagster.components.utils.translation import (
    ComponentTranslator,
    TranslationFn,
    TranslationFnResolver,
    create_component_translator_cls,
)
from dagster_shared import check
from typing_extensions import TypeAlias

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
class DagsterDbtComponentTranslatorSettings(DagsterDbtTranslatorSettings):
    """Subclass of DagsterDbtTranslatorSettings that enables code references by default."""

    enable_code_references: bool = True


@dataclass
class DbtProjectArgs(dg.Resolvable):
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


DbtMetadataAddons: TypeAlias = Literal["column_metadata", "row_count"]


@public
@scaffold_with(DbtProjectComponentScaffolder)
@dataclass
class DbtProjectComponent(dg.Component, dg.Resolvable):
    """Expose a DBT project to Dagster as a set of assets.

    This component assumes that you have already set up a dbt project, for example, the dbt `Jaffle shop <https://github.com/dbt-labs/jaffle-shop>`_. Run `git clone --depth=1 https://github.com/dbt-labs/jaffle-shop.git jaffle_shop && rm -rf jaffle_shop/.git` to copy that project
    into your Dagster project directory.

    Scaffold a DbtProjectComponent definition by running `dg scaffold defs dagster_dbt.DbtProjectComponent --project-path path/to/your/existing/dbt_project`
    in the Dagster project directory.
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
    cli_args: Annotated[
        list[Union[str, dict[str, Any]]],
        Resolver.passthrough(
            description="Arguments to pass to the dbt CLI when executing. Defaults to `['build']`.",
            examples=[
                ["run"],
                [
                    "build",
                    "--full_refresh",
                    {
                        "--vars": {
                            "start_date": "{{ context.partition_range_start }}",
                            "end_date": "{{ context.partition_range_end }}",
                        },
                    },
                ],
            ],
        ),
    ] = field(default_factory=lambda: ["build"])
    include_metadata: Annotated[
        list[DbtMetadataAddons],
        Resolver.default(
            description="Optionally include additional metadata in materializations generated while executing your dbt models",
            examples=[
                ["row_count"],
                ["row_count", "column_metadata"],
            ],
        ),
    ] = field(default_factory=list)
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
    translation: Annotated[
        Optional[TranslationFn[Mapping[str, Any]]],
        TranslationFnResolver(template_vars_for_translation_fn=lambda data: {"node": data}),
    ] = None
    translation_settings: Annotated[
        Optional[DagsterDbtComponentTranslatorSettings],
        Resolver.default(
            description="Allows enabling or disabling various features for translating dbt models in to Dagster assets.",
            examples=[
                {
                    "enable_source_tests_as_checks": True,
                },
            ],
        ),
    ] = field(default_factory=lambda: DagsterDbtComponentTranslatorSettings())
    prepare_if_dev: Annotated[
        bool,
        Resolver.default(
            description="Whether to prepare the dbt project every time in `dagster dev` or `dg` cli calls."
        ),
    ] = True

    @cached_property
    def translator(self) -> "DagsterDbtTranslator":
        return DbtProjectComponentTranslator(self, self.translation_settings)

    @cached_property
    def _base_translator(self) -> "DagsterDbtTranslator":
        return DagsterDbtTranslator(self.translation_settings)

    def get_asset_spec(
        self, manifest: Mapping[str, Any], unique_id: str, project: Optional[DbtProject]
    ) -> dg.AssetSpec:
        return self._base_translator.get_asset_spec(manifest, unique_id, project)

    def get_asset_check_spec(
        self,
        asset_spec: dg.AssetSpec,
        manifest: Mapping[str, Any],
        unique_id: str,
        project: Optional["DbtProject"],
    ) -> Optional[dg.AssetCheckSpec]:
        return self._base_translator.get_asset_check_spec(asset_spec, manifest, unique_id, project)

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

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
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
        def _fn(context: dg.AssetExecutionContext):
            yield from self.execute(context=context, dbt=self.cli_resource)

        return dg.Definitions(assets=[_fn])

    def get_cli_args(self, context: dg.AssetExecutionContext) -> list[str]:
        # create a resolution scope that includes the partition key and range, if available
        partition_key = context.partition_key if context.has_partition_key else None
        partition_key_range = (
            context.partition_key_range if context.has_partition_key_range else None
        )
        try:
            partition_time_window = context.partition_time_window
        except Exception:
            partition_time_window = None

        scope = dict(
            partition_key=partition_key,
            partition_key_range=partition_key_range,
            partition_time_window=partition_time_window,
        )

        # resolve the cli args with this additional scope
        resolved_args = ResolutionContext(scope=scope).resolve_value(
            self.cli_args, as_type=list[str]
        )

        def _normalize_arg(arg: Union[str, dict[str, Any]]) -> list[str]:
            if isinstance(arg, str):
                return [arg]

            check.invariant(
                len(arg.keys()) == 1, "Invalid cli args dict, must have exactly one key"
            )
            key = next(iter(arg.keys()))
            value = arg[key]
            if isinstance(value, dict):
                normalized_value = json.dumps(value)
            else:
                normalized_value = str(value)

            return [key, normalized_value]

        normalized_args = list(
            itertools.chain(*[list(_normalize_arg(arg)) for arg in resolved_args])
        )
        return normalized_args

    def _get_dbt_event_iterator(
        self, context: dg.AssetExecutionContext, dbt: DbtCliResource
    ) -> Iterator:
        iterator = dbt.cli(self.get_cli_args(context), context=context).stream()
        if "column_metadata" in self.include_metadata:
            iterator = iterator.fetch_column_metadata()
        if "row_count" in self.include_metadata:
            iterator = iterator.fetch_row_counts()
        return iterator

    def execute(self, context: dg.AssetExecutionContext, dbt: DbtCliResource) -> Iterator:
        yield from self._get_dbt_event_iterator(context, dbt)

    @cached_property
    def _validated_manifest(self):
        return validate_manifest(self.project.manifest_path)

    @cached_property
    def _validated_translator(self):
        return validate_translator(self.translator)

    @cached_method
    def asset_key_for_model(self, model_name: str) -> dg.AssetKey:
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


class DbtProjectComponentTranslator(
    create_component_translator_cls(DbtProjectComponent, DagsterDbtTranslator),
    ComponentTranslator[DbtProjectComponent],
):
    def __init__(
        self,
        component: DbtProjectComponent,
        settings: Optional[DagsterDbtComponentTranslatorSettings],
    ):
        self._component = component
        super().__init__(settings)

    def get_asset_spec(
        self, manifest: Mapping[str, Any], unique_id: str, project: Optional[DbtProject]
    ) -> dg.AssetSpec:
        base_spec = super().get_asset_spec(manifest, unique_id, project)
        if self.component.translation is None:
            return base_spec
        else:
            dbt_props = get_node(manifest, unique_id)
            return self.component.translation(base_spec, dbt_props)


def get_projects_from_dbt_component(components: Path) -> list[DbtProject]:
    project_components = ComponentTree.for_project(components).get_all_components(
        of_type=DbtProjectComponent
    )

    return [component.project for component in project_components]
