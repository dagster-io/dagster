from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from functools import cached_property
from types import ModuleType
from typing import Annotated, Any, Optional, Union, cast

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
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

from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.asset_utils import get_asset_key_for_model, get_node
from dagster_dbt.components.dbt_project.scaffolder import DbtProjectComponentScaffolder
from dagster_dbt.core.resource import DbtCliResource
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator
from dagster_dbt.dbt_manifest_asset_selection import DbtManifestAssetSelection
from dagster_dbt.dbt_project import DbtProject


class ComponentDagsterDbtTranslator(DagsterDbtTranslator):
    def __init__(self, *, resolving_info: TranslatorResolvingInfo):
        super().__init__()
        self.resolving_info = resolving_info
        self._specs_map: dict[tuple, AssetSpec] = {}

    def get_asset_spec(
        self,
        manifest: Mapping[str, Any],
        unique_id: str,
        project: Optional[DbtProject],
    ) -> AssetSpec:
        memo_id = (id(manifest), unique_id)
        if memo_id not in self._specs_map:
            base_spec = super().get_asset_spec(
                manifest=manifest,
                unique_id=unique_id,
                project=project,
            )
            self._specs_map[memo_id] = self.resolving_info.get_asset_spec(
                base_spec,
                {
                    self.resolving_info.obj_name: get_node(manifest, unique_id),
                    "spec": base_spec,
                },
            )
        return self._specs_map[memo_id]


def resolve_translator(context: ResolutionContext, model) -> DagsterDbtTranslator:
    if (
        model.asset_attributes
        and isinstance(model.asset_attributes, AssetAttributesModel)
        and "deps" in model.asset_attributes.model_dump(exclude_unset=True)
    ):
        # TODO: Consider supporting alerting deps in the future
        raise ValueError("deps are not supported for dbt_project component")

    return ComponentDagsterDbtTranslator(
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
