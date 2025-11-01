from collections.abc import Sequence
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Annotated, Callable, Optional, Union

import dagster as dg
import pydantic
from dagster._annotations import public
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
    DagsterCensusTranslator,
)


class CensusSyncSelectorByName(dg.Model):
    by_name: Annotated[
        Sequence[str],
        pydantic.Field(..., description="A list of sync names to include in the collection."),
    ]


class CensusSyncSelectorById(dg.Model):
    by_id: Annotated[
        Sequence[int],
        pydantic.Field(..., description="A list of sync IDs to include in the collection."),
    ]


def resolve_sync_selector(
    context: dg.ResolutionContext, model
) -> Optional[Callable[[CensusSync], bool]]:
    if isinstance(model, str):
        model = context.resolve_value(model)

    if isinstance(model, CensusSyncSelectorByName):
        return lambda sync: sync.name in model.by_name
    elif isinstance(model, CensusSyncSelectorById):
        return lambda sync: sync.id in model.by_id
    else:
        check.failed(f"Unknown connection target type: {type(model)}")


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
              census_resource:
                api_key: "{{ env.CENSUS_API_KEY }}"
              sync_selector:
                by_name:
                  - my_first_sync
                  - my_second_sync
    """

    census_resource: Annotated[
        CensusResource,
        dg.Resolver(
            lambda context, model: CensusResource(**resolve_fields(model, CensusResource, context))
        ),
    ]

    sync_selector: Annotated[
        Optional[Callable[[CensusSync], bool]],
        dg.Resolver(
            resolve_sync_selector,
            model_field_type=Union[str, CensusSyncSelectorByName, CensusSyncSelectorById],
            description="Function used to select Census syncs to pull into Dagster.",
        ),
    ] = None

    defs_state: ResolvedDefsStateConfig = field(
        default_factory=DefsStateConfigArgs.legacy_code_server_snapshots
    )

    @property
    def defs_state_config(self) -> DefsStateConfig:
        default_key = f"{self.__class__.__name__}"
        return DefsStateConfig.from_args(self.defs_state, default_key=default_key)

    @cached_property
    def translator(self) -> DagsterCensusTranslator:
        return DagsterCensusTranslator()

    def write_state_to_path(self, state_path: Path) -> None:
        state = self.census_resource.fetch_census_workspace_data()
        state_path.write_text(dg.serialize_value(state))

    def _load_asset_specs(self, state: CensusWorkspaceData) -> Sequence[dg.AssetSpec]:
        connection_selector_fn = self.sync_selector or (lambda sync: True)
        return [
            self.translator.get_asset_spec(props)
            for props in state.to_census_sync_table_props_data()
            if connection_selector_fn(state.syncs_by_id[props.sync_id])
        ]

    def _get_census_asset_def(self, sync_name: str, spec: dg.AssetSpec) -> dg.AssetsDefinition:
        @dg.asset(
            name=f"census_{clean_name(sync_name)}",
            deps=spec.deps,
            description=spec.description,
            metadata=spec.metadata,
            group_name=spec.group_name,
            code_version=spec.code_version,
            freshness_policy=spec.freshness_policy,
            automation_condition=spec.automation_condition,
            owners=spec.owners,
            tags=spec.tags,
            partitions_def=spec.partitions_def,
        )
        def _asset(context: dg.AssetExecutionContext):
            census_metadataset = CensusMetadataSet.extract(spec.metadata)
            self.census_resource.trigger_sync_and_poll(sync_id=census_metadataset.sync_id)
            return dg.MaterializeResult()

        return _asset

    def build_defs_from_state(
        self, context: dg.ComponentLoadContext, state_path: Optional[Path]
    ) -> dg.Definitions:
        if state_path is None:
            return dg.Definitions()

        state = deserialize_value(state_path.read_text(), CensusWorkspaceData)

        assets = [
            self._get_census_asset_def(CensusMetadataSet.extract(spec.metadata).sync_name, spec)
            for spec in self._load_asset_specs(state)
        ]

        return dg.Definitions(assets=assets)
