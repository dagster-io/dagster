from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Optional, Union

import dagster as dg
import pydantic
from dagster._annotations import public
from dagster._core.definitions.metadata import TableMetadataSet
from dagster._utils.names import clean_name
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.resolved.base import resolve_fields
from dagster.components.utils.defs_state import (
    DefsStateConfig,
    DefsStateConfigArgs,
    ResolvedDefsStateConfig,
)
from dagster_shared import check
from dagster_shared.serdes.serdes import deserialize_value

from dagster_census.components.census_scaffolder import CensusComponentScaffolder
from dagster_census.resources import CensusResource
from dagster_census.translator import (
    CensusMetadataSet,
    CensusSync,
    CensusWorkspaceData,
    generate_table_schema,
)


class CensusSyncSelectorByName(dg.Resolvable, dg.Model):
    by_name: Annotated[
        Sequence[str],
        pydantic.Field(..., description="A list of sync names to include in the collection."),
    ]


class CensusSyncSelectorById(dg.Resolvable, dg.Model):
    by_id: Annotated[
        Sequence[Union[int, str]],  # Allow strings for use-cases like '{{ env.ENV_VAR }}'
        pydantic.Field(..., description="A list of sync IDs to include in the collection."),
    ]


def resolve_sync_selector(
    context: dg.ResolutionContext, model
) -> Optional[Callable[[CensusSync], bool]]:
    if isinstance(model, str):
        resolved = context.resolve_value(model)
        resolved = check.callable_param(resolved, "unknown")  # pyright: ignore[reportArgumentType]
        return resolved
    if isinstance(model, CensusSyncSelectorByName.model()):
        resolved = resolve_fields(model, CensusSyncSelectorByName.model(), context)
        return lambda sync: sync.name in resolved["by_name"]
    elif isinstance(model, CensusSyncSelectorById.model()):
        resolved = resolve_fields(model, CensusSyncSelectorById.model(), context)
        return lambda sync: sync.id in resolved["by_id"]
    else:
        check.failed(f"Unknown sync target type: {type(model)}")


@dataclass
class CensusResourceArgs(dg.Resolvable, dg.Model):
    """The fields are analogous to the fields at `CensusResource`."""

    api_key: Annotated[str, pydantic.Field(...)]
    request_max_retries: Annotated[int, pydantic.Field(None)]
    request_retry_delay: Annotated[float, pydantic.Field(None)]
    request_timeout: Annotated[int, pydantic.Field(None)]


def resolve_census_workspace(
    context: dg.ResolutionContext, model: CensusResourceArgs
) -> CensusResource:
    return CensusResource(**resolve_fields(model, CensusResourceArgs, context))


@public
@dataclass
@dg.scaffold_with(CensusComponentScaffolder)
class CensusComponent(StateBackedComponent, dg.Resolvable):
    """Loads Census syncs from a Census workspace as Dagster assets.
    Materializing these assets will trigger the Census sync, enabling
    you to schedule Census syncs using Dagster.

    Example:

        .. code-block:: yaml

            # defs.yaml

            type: dagster_census.CensusComponent
            attributes:
              workspace:
                api_key: "{{ env.CENSUS_API_KEY }}"
              sync_selector:
                by_name:
                  - my_first_sync
                  - my_second_sync
    """

    workspace: Annotated[
        CensusResource,
        dg.Resolver(resolve_census_workspace, model_field_type=CensusResourceArgs),
    ]

    sync_selector: Annotated[
        Optional[Callable[[CensusSync], bool]],
        dg.Resolver(
            resolve_sync_selector,
            model_field_type=Union[
                str, CensusSyncSelectorByName.model(), CensusSyncSelectorById.model()
            ],
            description="Function used to select Census syncs to pull into Dagster.",
        ),
    ] = None

    defs_state: ResolvedDefsStateConfig = field(
        default_factory=DefsStateConfigArgs.local_filesystem
    )

    @property
    def defs_state_config(self) -> DefsStateConfig:
        default_key = f"{self.__class__.__name__}"
        return DefsStateConfig.from_args(self.defs_state, default_key=default_key)

    def write_state_to_path(self, state_path: Path) -> None:
        state = self.workspace.fetch_census_workspace_data()
        state_path.write_text(dg.serialize_value(state))

    @public
    def get_asset_spec(self, sync: CensusSync) -> dg.AssetSpec:
        metadata = {
            **TableMetadataSet(
                column_schema=generate_table_schema(sync.mappings),
                table_name=sync.name,
            ),
            **CensusMetadataSet(
                sync_id=sync.id,
                sync_name=sync.name,
                source_id=sync.source_id,
                destination_id=sync.destination_id,
            ),
        }

        return dg.AssetSpec(
            key=dg.AssetKey(clean_name(sync.name)),
            metadata=metadata,
            description=f"Asset generated from Census sync {sync.id}",
            kinds={"census"},
        )

    @public
    def execute(
        self, context: dg.AssetExecutionContext, census: CensusResource
    ) -> Iterable[Union[dg.AssetMaterialization, dg.MaterializeResult]]:
        """Executes a Census sync for the selected sync.

        This method can be overridden in a subclass to customize the sync execution behavior,
        such as adding custom logging or handling sync results differently.

        Args:
            context: The asset execution context provided by Dagster
            census: The CensusResource used to trigger and monitor syncs

        Returns:
            MaterializeResult event from the Census sync

        Example:
            Override this method to add custom logging during sync execution:

            .. code-block:: python

                from dagster_census import CensusComponent
                import dagster as dg

                class CustomCensusComponent(CensusComponent):
                    def execute(self, context, census):
                        context.log.info(f"Starting Census sync for {context.asset_key}")
                        result = super().execute(context, census)
                        context.log.info("Census sync completed successfully")
                        return result
        """
        # Select the first asset-spec (since there is only one)
        spec = next(iter(context.assets_def.specs))

        census_metadataset = CensusMetadataSet.extract(spec.metadata)
        census.trigger_sync_and_poll(sync_id=census_metadataset.sync_id)
        yield dg.AssetMaterialization(asset_key=clean_name(census_metadataset.sync_name))

    def _load_asset_specs(self, state: CensusWorkspaceData) -> Sequence[dg.AssetSpec]:
        connection_selector_fn = self.sync_selector or (lambda sync: True)
        return [self.get_asset_spec(sync) for sync in state.syncs if connection_selector_fn(sync)]

    def _get_census_assets_def(self, sync_name: str, spec: dg.AssetSpec) -> dg.AssetsDefinition:
        @dg.multi_asset(
            name=f"census_{clean_name(sync_name)}",
            can_subset=True,
            specs=[spec],
        )
        def _asset(context: dg.AssetExecutionContext):
            yield from self.execute(context, self.workspace)

        return _asset

    def build_defs_from_state(
        self, context: dg.ComponentLoadContext, state_path: Optional[Path]
    ) -> dg.Definitions:
        if state_path is None:
            return dg.Definitions()

        state = deserialize_value(state_path.read_text(), CensusWorkspaceData)

        assets = [
            self._get_census_assets_def(CensusMetadataSet.extract(spec.metadata).sync_name, spec)
            for spec in self._load_asset_specs(state)
        ]

        return dg.Definitions(assets=assets)
