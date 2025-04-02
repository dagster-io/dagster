from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from functools import cached_property
from types import ModuleType
from typing import Annotated, Any, Optional, Union, cast

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components import Resolvable, Resolver
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.core_models import (
    AssetAttributesModel,
    AssetPostProcessor,
    OpSpec,
    ResolutionContext,
)
from dagster.components.scaffold.scaffold import scaffold_with
from dagster.components.utils import TranslatorResolvingInfo
from typing_extensions import override

from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.asset_utils import (
    get_asset_key_for_model as get_asset_key_for_model,
    get_asset_spec,
)
from dagster_dbt.components.dbt_project.scaffolder import DbtProjectComponentScaffolder
from dagster_dbt.core.resource import DbtCliResource
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator
from dagster_dbt.dbt_manifest import validate_manifest
from dagster_dbt.dbt_manifest_asset_selection import DbtManifestAssetSelection
from dagster_dbt.dbt_project import DbtProject
from dagster_dbt.utils import get_dbt_resource_props_by_dbt_unique_id_from_manifest


def resolve_translator(context: ResolutionContext, model) -> DagsterDbtTranslator:
    class DagsterDbtTranslatorWithSpecs(DagsterDbtTranslator):
        def __init__(self, *, resolving_info: TranslatorResolvingInfo):
            super().__init__()
            self.resolving_info = resolving_info
            self.base_translator = DagsterDbtTranslator()
            self._specs_map: dict[int, AssetSpec] = {}

        @cached_property
        def project(self) -> DbtProject:
            return DbtProject(model.dbt.project_dir)

        @cached_property
        def manifest(self) -> Mapping[str, Any]:
            return validate_manifest(self.project.manifest_path)

        @cached_property
        def dbt_nodes(self) -> Mapping[str, Any]:
            return get_dbt_resource_props_by_dbt_unique_id_from_manifest(self.manifest)

        @cached_property
        def group_props(self) -> Mapping[str, Any]:
            return {group["name"]: group for group in self.manifest.get("groups", {}).values()}

        def get_asset_spec(self, stream_definition: Mapping[str, Any]) -> AssetSpec:
            if id(stream_definition) not in self._specs_map:
                base_spec = get_asset_spec(
                    translator=DagsterDbtTranslator(),
                    manifest=self.manifest,
                    dbt_nodes=self.dbt_nodes,
                    group_props=self.group_props,
                    project=self.project,
                    resource_props=stream_definition,
                )
                self._specs_map[id(stream_definition)] = self.resolving_info.get_asset_spec(
                    base_spec,
                    {self.resolving_info.obj_name: stream_definition, "spec": base_spec},
                )
            return self._specs_map[id(stream_definition)]

        @override
        def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
            return self.get_asset_spec(dbt_resource_props).key

        @override
        def get_description(self, dbt_resource_props: Mapping[str, Any]) -> Optional[str]:  # pyright: ignore[reportIncompatibleMethodOverride]
            return self.get_asset_spec(dbt_resource_props).description

        @override
        def get_metadata(self, dbt_resource_props: Mapping[str, Any]) -> Mapping[str, Any]:
            return self.get_asset_spec(dbt_resource_props).metadata

        @override
        def get_tags(self, dbt_resource_props: Mapping[str, Any]) -> Mapping[str, str]:
            return self.get_asset_spec(dbt_resource_props).tags

        @override
        def get_group_name(self, dbt_resource_props: Mapping[str, Any]) -> Optional[str]:
            return self.get_asset_spec(dbt_resource_props).group_name

        @override
        def get_code_version(self, dbt_resource_props: Mapping[str, Any]) -> Optional[str]:
            return self.get_asset_spec(dbt_resource_props).code_version

        @override
        def get_owners(self, dbt_resource_props: Mapping[str, Any]) -> Sequence[str]:
            return self.get_asset_spec(dbt_resource_props).owners

        @override
        def get_automation_condition(
            self, dbt_resource_props: Mapping[str, Any]
        ) -> Optional[AutomationCondition]:
            return self.get_asset_spec(dbt_resource_props).automation_condition

    if (
        model.asset_attributes
        and isinstance(model.asset_attributes, AssetAttributesModel)
        and "deps" in model.asset_attributes.model_dump(exclude_unset=True)
    ):
        # TODO: Consider supporting alerting deps in the future
        raise ValueError("deps are not supported for dbt_project component")

    return DagsterDbtTranslatorWithSpecs(
        resolving_info=TranslatorResolvingInfo(
            "node",
            model.asset_attributes or AssetAttributesModel(),
            context,
        )
    )


def resolve_dbt(context: ResolutionContext, dbt: DbtCliResource) -> DbtCliResource:
    return DbtCliResource(**context.resolve_value(dbt.model_dump()))


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

    dbt: Annotated[DbtCliResource, Resolver(resolve_dbt)]
    op: Optional[OpSpec] = None
    translator: Annotated[
        DagsterDbtTranslator,
        Resolver.from_model(
            resolve_translator,
            model_field_name="asset_attributes",
            model_field_type=Optional[Union[str, AssetAttributesModel]],
        ),
    ] = field(default_factory=DagsterDbtTranslator)
    asset_post_processors: Optional[Sequence[AssetPostProcessor]] = None
    select: str = "fqn:*"
    exclude: Optional[str] = None

    @cached_property
    def project(self) -> DbtProject:
        return DbtProject(self.dbt.project_dir)

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
            yield from self.execute(context=context, dbt=self.dbt)

        defs = Definitions(assets=[_fn])
        for post_processor in self.asset_post_processors or []:
            defs = post_processor(defs)
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
    return get_asset_key_for_model(cast(Sequence[AssetsDefinition], defs.assets), model_name)
