import itertools
import json
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field, replace
from functools import cached_property
from pathlib import Path
from typing import Annotated, Any, Literal, Optional, TypeAlias, Union

import dagster as dg
from dagster._annotations import public
from dagster._utils.cached_method import cached_method
from dagster.components import ComponentLoadContext
from dagster.components.core.component_tree import ComponentTree
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import OpSpec
from dagster.components.resolved.model import Resolver
from dagster.components.scaffold.scaffold import scaffold_with
from dagster.components.utils.defs_state import DefsStateConfig
from dagster.components.utils.translation import (
    ComponentTranslator,
    TranslationFn,
    TranslationFnResolver,
    create_component_translator_cls,
)
from dagster_shared import check
from dagster_shared.serdes.objects.models.defs_state_info import DefsStateManagementType
from pydantic import Field

from dagster_dbt.asset_utils import DBT_DEFAULT_EXCLUDE, build_dbt_specs, get_node
from dagster_dbt.components.base import BaseDbtComponent, DagsterDbtComponentTranslatorSettings
from dagster_dbt.components.dbt_project.scaffolder import DbtProjectComponentScaffolder
from dagster_dbt.core.resource import DbtCliResource
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, validate_translator
from dagster_dbt.dbt_manifest import validate_manifest
from dagster_dbt.dbt_manifest_asset_selection import DbtManifestAssetSelection
from dagster_dbt.dbt_project import DbtProject
from dagster_dbt.dbt_project_manager import (
    DbtProjectArgsManager,
    DbtProjectManager,
    NoopDbtProjectManager,
    RemoteGitDbtProjectManager,
)
from dagster_dbt.utils import ASSET_RESOURCE_TYPES


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


def resolve_dbt_project(context: ResolutionContext, model) -> DbtProjectManager:
    if isinstance(model, RemoteGitDbtProjectManager.model()):
        return RemoteGitDbtProjectManager.resolve_from_model(context, model)

    args = (
        DbtProjectArgs(project_dir=context.resolve_value(model, as_type=str))
        if isinstance(model, str)
        else DbtProjectArgs.resolve_from_model(context, model)
    )
    args = replace(args, project_dir=context.resolve_source_relative_path(args.project_dir))
    return DbtProjectArgsManager(args)


DbtMetadataAddons: TypeAlias = Literal["column_metadata", "row_count"]

_resolution_context: ContextVar[ResolutionContext] = ContextVar("resolution_context")


@contextmanager
def _set_resolution_context(context: ResolutionContext):
    token = _resolution_context.set(context)
    try:
        yield
    finally:
        _resolution_context.reset(token)


@public
@scaffold_with(DbtProjectComponentScaffolder)
class DbtProjectComponent(BaseDbtComponent):
    """Expose a DBT project to Dagster as a set of assets.

    This component assumes that you have already set up a dbt project, for example, the dbt `Jaffle shop <https://github.com/dbt-labs/jaffle-shop>`_. Run `git clone --depth=1 https://github.com/dbt-labs/jaffle-shop.git jaffle_shop && rm -rf jaffle_shop/.git` to copy that project
    into your Dagster project directory.

    Scaffold a DbtProjectComponent definition by running `dg scaffold defs dagster_dbt.DbtProjectComponent --project-path path/to/your/existing/dbt_project`
    in the Dagster project directory.

    Example:

        .. code-block:: yaml

            # defs.yaml

            type: dagster_dbt.DbtProjectComponent
            attributes:
              project: "{{ project_root }}/path/to/dbt_project"
              cli_args:
                - build
    """

    project: Annotated[
        Union[DbtProject, DbtProjectManager],
        Resolver(
            resolve_dbt_project,
            model_field_type=Union[str, DbtProjectArgs.model(), RemoteGitDbtProjectManager.model()],
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
    ] = field(default_factory=DagsterDbtComponentTranslatorSettings)
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
                            "start_date": "{{ partition_range_start }}",
                            "end_date": "{{ partition_range_end }}",
                        },
                    },
                ],
            ],
        ),
    ] = Field(default_factory=lambda: ["build"])
    include_metadata: Annotated[
        list[DbtMetadataAddons],
        Resolver.default(
            description="Optionally include additional metadata in materializations generated while executing your dbt models",
            examples=[
                ["row_count"],
                ["row_count", "column_metadata"],
            ],
        ),
    ] = Field(default_factory=list)
    translation: Annotated[
        Optional[TranslationFn[Mapping[str, Any]]],
        TranslationFnResolver(template_vars_for_translation_fn=lambda data: {"node": data}),
    ] = None
    prepare_if_dev: Annotated[
        bool,
        Resolver.default(
            description="Whether to prepare the dbt project every time in `dagster dev` or `dg` cli calls."
        ),
    ] = True

    @property
    def defs_state_config(self) -> DefsStateConfig:
        return DefsStateConfig(
            key=f"DbtProjectComponent[{self._project_manager.defs_state_discriminator}]",
            management_type=DefsStateManagementType.LOCAL_FILESYSTEM,
            refresh_if_dev=self.prepare_if_dev,
        )

    @property
    def op_config_schema(self) -> Optional[type[dg.Config]]:
        return None

    @property
    def config_cls(self) -> Optional[type[dg.Config]]:
        """Internal property that returns the config schema for the op.

        Delegates to op_config_schema for backwards compatibility and consistency
        with other component types.
        """
        return self.op_config_schema

    def _get_op_spec(self, op_name: Optional[str] = None) -> OpSpec:
        if op_name is None:
            op_name = self.dbt_project.name

        return super()._get_op_spec(op_name)

    @property
    @cached_method
    def translator(self) -> "DagsterDbtTranslator":
        return DbtProjectComponentTranslator(self, self.translation_settings)

    @cached_property
    def _base_translator(self) -> "DagsterDbtTranslator":
        return DagsterDbtTranslator(self.translation_settings)

    @cached_property
    def _project_manager(self) -> DbtProjectManager:
        if isinstance(self.project, DbtProject):
            return NoopDbtProjectManager(self.project)
        else:
            return self.project

    @cached_property
    def dbt_project(self) -> DbtProject:
        return self._project_manager.get_project(None)

    def get_asset_selection(
        self, select: str, exclude: str = DBT_DEFAULT_EXCLUDE, manifest_path: Optional[str] = None
    ) -> DbtManifestAssetSelection:
        actual_manifest_path = manifest_path or str(self.dbt_project.manifest_path)
        return DbtManifestAssetSelection.build(
            manifest=actual_manifest_path,
            dagster_dbt_translator=self.translator,
            select=select,
            exclude=exclude,
        )

    def write_state_to_path(self, state_path: Path) -> None:
        self._project_manager.prepare(state_path)

    def build_defs_from_state(
        self, context: ComponentLoadContext, state_path: Optional[Path]
    ) -> dg.Definitions:
        project = self._project_manager.get_project(state_path)

        res_ctx = context.resolution_context

        asset_specs, check_specs = build_dbt_specs(
            translator=validate_translator(self.translator),
            manifest=validate_manifest(project.manifest_path),
            select=self.select,
            exclude=self.exclude,
            selector=self.selector,
            project=project,
            io_manager_key=None,
        )
        op_spec = self._get_op_spec(project.name)

        @dg.multi_asset(
            specs=asset_specs,
            check_specs=check_specs,
            can_subset=True,
            name=op_spec.name,
            op_tags=op_spec.tags,
            backfill_policy=op_spec.backfill_policy,
            pool=op_spec.pool,
            config_schema=self.config_cls.to_fields_dict() if self.config_cls else None,
            allow_arbitrary_check_specs=self.translator.settings.enable_source_tests_as_checks,
        )
        def _fn(context: dg.AssetExecutionContext):
            with _set_resolution_context(res_ctx):
                yield from self.execute(context=context, dbt=DbtCliResource(project))

        return dg.Definitions(assets=[_fn])

    def get_cli_args(self, context: dg.AssetExecutionContext) -> list[str]:
        partition_key = context.partition_key if context.has_partition_key else None
        partition_key_range = (
            context.partition_key_range if context.has_partition_key_range else None
        )
        try:
            partition_time_window = context.partition_time_window
        except Exception:
            partition_time_window = None

        resolved_args = (
            _resolution_context.get()
            .with_scope(
                partition_key=partition_key,
                partition_key_range=partition_key_range,
                partition_time_window=partition_time_window,
            )
            .resolve_value(self.cli_args, as_type=list[str])
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

    @public
    def execute(self, context: dg.AssetExecutionContext, dbt: DbtCliResource) -> Iterator:
        """Executes the dbt command for the selected assets.

        This method can be overridden in a subclass to customize the execution behavior,
        such as adding custom logging, modifying CLI arguments, or handling events differently.

        Args:
            context: The asset execution context provided by Dagster
            dbt: The DbtCliResource used to execute dbt commands

        Yields:
            Events from the dbt CLI execution (e.g., AssetMaterialization, AssetObservation)

        Example:
            Override this method to add custom logging before and after execution:

            .. code-block:: python

                from dagster_dbt import DbtProjectComponent
                import dagster as dg

                class CustomDbtProjectComponent(DbtProjectComponent):
                    def execute(self, context, dbt):
                        context.log.info("Starting custom dbt execution")
                        yield from super().execute(context, dbt)
                        context.log.info("Completed custom dbt execution")
        """
        yield from self._get_dbt_event_iterator(context, dbt)

    @cached_property
    def _validated_manifest(self):
        return validate_manifest(self.dbt_project.manifest_path)

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
            self.dbt_project,
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

    return [component.dbt_project for component in project_components]
