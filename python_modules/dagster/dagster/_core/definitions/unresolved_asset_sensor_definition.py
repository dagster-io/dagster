import inspect
from collections import defaultdict
from itertools import chain
from typing import TYPE_CHECKING, List, Mapping, Optional, Sequence

from dagster._annotations import experimental
from dagster._core.errors import DagsterInvalidDefinitionError

from .asset_selection import AssetSelection
from .events import AssetKey
from .run_request import PipelineRunReaction, RunRequest, SkipReason
from .sensor_definition import (
    DefaultSensorStatus,
    MultiAssetSensorDefinition,
    MultiAssetSensorEvaluationContext,
    SensorDefinition,
)
from .target import ExecutableDefinition
from .utils import check_valid_name

if TYPE_CHECKING:
    from dagster._core.definitions import AssetsDefinition, SourceAsset


class UnresolvedAssetSensorDefinition:
    def __init__(self):
        pass

    def resolve(
        self,
        assets: Sequence["AssetsDefinition"],
        source_assets: Sequence["SourceAsset"],
    ):
        pass


@experimental
class UnresolvedAssetSensorDefinitionV1(UnresolvedAssetSensorDefinition):
    def __init__(
        self,
        asset_selection: AssetSelection,
        name: str,
        job_name: Optional[str] = None,
        minimum_interval_seconds: Optional[int] = None,
        description: Optional[str] = None,
        job: Optional[ExecutableDefinition] = None,
        jobs: Optional[Sequence[ExecutableDefinition]] = None,
        default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    ):
        self._selection = asset_selection
        self._name = name
        self._job_name = job_name
        self._minimum_interval_seconds = minimum_interval_seconds
        self._description = description
        self._job = job
        self._jobs = jobs
        self._default_status = default_status

        super(UnresolvedAssetSensorDefinitionV1, self).__init__()

    @property
    def name(self):
        return self._name

    def resolve(
        self,
        assets: Sequence["AssetsDefinition"],
        source_assets: Sequence["SourceAsset"],
    ):
        upstream = list(self._selection.upstream().resolve([*assets, *source_assets]))
        monitored_resolved = list(self._selection.resolve([*assets, *source_assets]))

        def materialization_fn(context):
            for a in monitored_resolved:
                print(a)

            print("SUCCESS")
            print(upstream)

        def _fn(context):
            context.cursor_has_been_updated = False
            result = materialization_fn(context)
            if result is None:
                return

            # because the materialization_fn can yield results (see _wrapped_fn in multi_asset_sensor decorator),
            # even if you return None in a sensor, it will still cause in inspect.isgenerator(result) == True.
            # So keep track to see if we actually return any values and should update the cursor
            # runs_yielded = False
            # if inspect.isgenerator(result) or isinstance(result, list):
            #     for item in result:
            #         runs_yielded = True
            #         yield item
            # elif isinstance(result, RunRequest):
            #     runs_yielded = True
            #     yield result
            # elif isinstance(result, SkipReason):
            #     # if result is a SkipReason, we don't update the cursor, so don't set runs_yielded = True
            #     yield result

            # if runs_yielded and not context.cursor_has_been_updated:
            #     raise DagsterInvalidDefinitionError(
            #         "Asset materializations have been handled in this sensor, "
            #         "but the cursor was not updated. This means the same materialization events "
            #         "will be handled in the next sensor tick. Use context.advance_cursor or "
            #         "context.advance_all_cursors to update the cursor."
            #     )

        return SensorDefinition(
            name=check_valid_name(self._name),
            job_name=self._job_name,
            evaluation_fn=_fn,
            minimum_interval_seconds=self._minimum_interval_seconds,
            description=self._description,
            job=self._job,
            jobs=self._jobs,
            default_status=self._default_status,
        )


class UnresolvedAssetSensorDefinitionV2(UnresolvedAssetSensorDefinition):
    def __init__(self, asset_selection, name):
        self._selection = asset_selection
        self._name = name

        super(UnresolvedAssetSensorDefinitionV2, self).__init__()

    @property
    def name(self):
        return self._name

    def get_dependency_mapping(
        self,
        assets: Sequence["AssetsDefinition"],
        source_assets: Sequence["SourceAsset"],
    ):
        """Computes a mapping of assets in self._selection to their parents in the asset graph"""
        upstream = defaultdict(set)
        downstream = defaultdict(set)
        selection_resolved = list(self._selection.resolve([*assets, *source_assets]))
        for a in selection_resolved:
            a_parents = list(AssetSelection.keys(a).upstream().resolve([*assets, *source_assets]))
            # filter out a because upstream() includes the assets in the original AssetSelection
            upstream[a] = {p for p in a_parents if p != a}
            for p in upstream[a]:
                downstream[p].add(a)
        return {"upstream": upstream, "downstream": downstream}

    def make_sensor(self, dependency_mapping: Mapping[AssetKey, Sequence[AssetKey]]):

        upstream = dependency_mapping["upstream"]
        downstream = dependency_mapping["downstream"]

        def sensor_fn(context: MultiAssetSensorEvaluationContext):
            latest_events = context.latest_materialization_records_by_key()

            should_materialize: List[AssetKey] = []

            # we want to materialize an asset if all of its parents have been materialized more recently
            # than the asset was materialized
            for a in upstream.keys():
                a_materialization = latest_events.get(a)
                parents_materialization = {k: v for k, v in latest_events.items() if k in upstream[a]}

                if all(parents_materialization.values()):  # all parents have been materialized
                    parent_timestamps = [
                        parent_event.event_log_entry.timestamp
                        for parent_event in parents_materialization.values()
                    ]

                    if a_materialization is not None:
                        a_timestamp = a_materialization.event_log_entry.timestamp
                        if all(
                            [a_timestamp < p_time for p_time in parent_timestamps]
                        ):  # all parents have been materialized more recently than a
                            should_materialize.append(a)
                    else:
                        should_materialize.append(a)

            # we need to update the cursor for all of the parent assets. We update the cursor for an asset if
            # all of the downstream assets have been materialized more recently than the asset

            # TODO - this won't account for failures in the materialization of assets in should_materialize
            # ie we update the cursor before knowing if the materializations succeeded. Should we handle this?
            cursor_update_dict = {}
            for p in downstream.keys():
                should_update = True
                for c in downstream[p]:
                    if (
                        latest_events[c].event_log_entry.timestamp
                        <= latest_events[p].event_log_entry.timestamp
                        and c not in should_materialize
                    ):
                        # one of the downstream hasn't been materialized yet
                        should_update = False

                if should_update:
                    cursor_update_dict[p] = latest_events[p]
                else:
                    cursor_update_dict[p] = None

            context.advance_cursor(cursor_update_dict)

            # now need to actually launch the run of all should_materialize
            return RunRequest(run_key=f"{context.cursor}", asset_selection=should_materialize)

        return MultiAssetSensorDefinition(
            asset_keys=list(set(chain.from_iterable(upstream.values()))) + list(upstream.keys()),
            asset_materialization_fn=sensor_fn,
            name=self.name,
            job_name="__ASSET_JOB",
        )

    def resolve(
        self,
        assets: Sequence["AssetsDefinition"],
        source_assets: Sequence["SourceAsset"],
    ):
        return self.make_sensor(self.get_dependency_mapping(assets, source_assets))


@experimental
def build_asset_sensor(selection: AssetSelection, name: str) -> UnresolvedAssetSensorDefinition:
    return UnresolvedAssetSensorDefinitionV2(asset_selection=selection, name=name)
