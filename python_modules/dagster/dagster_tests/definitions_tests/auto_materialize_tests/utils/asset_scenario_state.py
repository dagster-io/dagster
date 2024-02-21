import dataclasses
import datetime
import json
import logging
from collections import namedtuple
from dataclasses import dataclass, field
from typing import (
    Iterable,
    NamedTuple,
    Optional,
    Sequence,
    Union,
)

import dagster._check as check
import mock
import pendulum
from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetsDefinition,
    AssetSpec,
    AutoMaterializePolicy,
    DagsterInstance,
    DagsterRunStatus,
    Definitions,
    PartitionsDefinition,
    RunRequest,
    RunsFilter,
    asset,
    materialize,
)
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.events import CoercibleToAssetKey
from dagster._core.storage.tags import PARTITION_NAME_TAG
from dagster._seven.compat.pendulum import pendulum_freeze_time
from typing_extensions import Self

from ..base_scenario import FAIL_TAG, run_request


class AssetSpecWithPartitionsDef(
    namedtuple(
        "AssetSpecWithPartitionsDef",
        AssetSpec._fields + ("partitions_def",),
        defaults=(None,) * (1 + len(AssetSpec._fields)),
    )
):
    ...


class MultiAssetSpec(NamedTuple):
    specs: Sequence[AssetSpec]
    partitions_def: Optional[PartitionsDefinition] = None
    can_subset: bool = False


@dataclass(frozen=True)
class AssetScenarioState:
    """Generic base class for an object which can be used to specify relevent state when simulating
    an interaction that mutates state involving assets (e.g. their definitions or the state of
    the event log).
    """

    asset_specs: Sequence[Union[AssetSpec, AssetSpecWithPartitionsDef, MultiAssetSpec]]
    current_time: datetime.datetime = field(default=pendulum.now("UTC"))
    logger: logging.Logger = field(default=logging.getLogger("dagster.amp"))
    scenario_instance: Optional[DagsterInstance] = None

    @property
    def instance(self) -> DagsterInstance:
        return check.not_none(self.scenario_instance)

    @property
    def assets(self) -> Sequence[AssetsDefinition]:
        def compute_fn(context: AssetExecutionContext) -> None:
            fail_keys = {
                AssetKey.from_coercible(s)
                for s in json.loads(context.run.tags.get(FAIL_TAG) or "[]")
            }
            for asset_key in context.selected_asset_keys:
                if asset_key in fail_keys:
                    raise Exception("Asset failed")

        assets = []
        for spec in self.asset_specs:
            if isinstance(spec, MultiAssetSpec):

                @multi_asset(**spec._asdict())
                def _multi_asset(context: AssetExecutionContext):
                    return compute_fn(context)

                assets.append(_multi_asset)
            else:
                params = {
                    "key",
                    "deps",
                    "group_name",
                    "code_version",
                    "auto_materialize_policy",
                    "freshness_policy",
                    "partitions_def",
                }
                assets.append(
                    asset(
                        compute_fn=compute_fn,
                        **{k: v for k, v in spec._asdict().items() if k in params},
                    )
                )
        return assets

    @property
    def defs(self) -> Definitions:
        return Definitions(assets=self.assets)

    @property
    def asset_graph(self) -> AssetGraph:
        return AssetGraph.from_assets(self.assets)

    def with_asset_properties(
        self, keys: Optional[Iterable[CoercibleToAssetKey]] = None, **kwargs
    ) -> Self:
        """Convenience method to update the properties of one or more assets in the scenario state."""
        new_asset_specs = []
        for spec in self.asset_specs:
            if isinstance(spec, MultiAssetSpec):
                partitions_def = kwargs.get("partitions_def", spec.partitions_def)
                new_multi_specs = [
                    s._replace(**{k: v for k, v in kwargs.items() if k != "partitions_def"})
                    if keys is None or s.key in keys
                    else s
                    for s in spec.specs
                ]
                new_asset_specs.append(
                    spec._replace(partitions_def=partitions_def, specs=new_multi_specs)
                )
            else:
                if keys is None or spec.key in {AssetKey.from_coercible(key) for key in keys}:
                    if "partitions_def" in kwargs:
                        # partitions_def is not a field on AssetSpec, so we need to do this hack
                        new_asset_specs.append(
                            AssetSpecWithPartitionsDef(**{**spec._asdict(), **kwargs})
                        )
                    else:
                        new_asset_specs.append(spec._replace(**kwargs))
                else:
                    new_asset_specs.append(spec)
        return dataclasses.replace(self, asset_specs=new_asset_specs)

    def with_all_eager(self, max_materializations_per_minute: int = 1) -> Self:
        return self.with_asset_properties(
            auto_materialize_policy=AutoMaterializePolicy.eager(
                max_materializations_per_minute=max_materializations_per_minute
            )
        )

    def with_current_time(self, time: str) -> Self:
        return dataclasses.replace(self, current_time=pendulum.parse(time))

    def with_current_time_advanced(self, **kwargs) -> Self:
        # hacky support for adding years
        if "years" in kwargs:
            kwargs["days"] = kwargs.get("days", 0) + 365 * kwargs.pop("years")
        return dataclasses.replace(
            self, current_time=self.current_time + datetime.timedelta(**kwargs)
        )

    def with_runs(self, *run_requests: RunRequest) -> Self:
        start = datetime.datetime.now()

        def test_time_fn() -> float:
            # this function will increment the current timestamp in real time, relative to the
            # fake current_time on the scenario state
            return (self.current_time + (datetime.datetime.now() - start)).timestamp()

        with pendulum_freeze_time(self.current_time), mock.patch("time.time", new=test_time_fn):
            for rr in run_requests:
                materialize(
                    assets=self.assets,
                    instance=self.instance,
                    partition_key=rr.partition_key,
                    tags=rr.tags,
                    raise_on_error=False,
                    selection=rr.asset_selection,
                )
        # increment current_time by however much time elapsed during the materialize call
        return dataclasses.replace(
            self, current_time=self.current_time + (datetime.datetime.now() - start)
        )

    def with_not_started_runs(self) -> Self:
        """Execute all runs in the NOT_STARTED state and delete them from the instance. The scenario
        adds in the run requests from previous ticks as runs in the NOT_STARTED state, so this method
        executes requested runs from previous ticks.
        """
        not_started_runs = self.instance.get_runs(
            filters=RunsFilter(statuses=[DagsterRunStatus.NOT_STARTED])
        )
        for run in not_started_runs:
            self.instance.delete_run(run_id=run.run_id)
        return self.with_runs(
            *[
                run_request(
                    asset_keys=list(run.asset_selection or set()),
                    partition_key=run.tags.get(PARTITION_NAME_TAG),
                )
                for run in not_started_runs
            ]
        )

    def with_dynamic_partitions(
        self, partitions_def_name: str, partition_keys: Sequence[str]
    ) -> Self:
        self.instance.add_dynamic_partitions(
            partitions_def_name=partitions_def_name, partition_keys=partition_keys
        )
        return self
