from collections.abc import Mapping, Sequence
from enum import Enum
from typing import TYPE_CHECKING, Any, NamedTuple, Optional, Union

from dagster_shared.serdes import whitelist_for_serdes

import dagster._check as check
from dagster._annotations import PublicAttr, public
from dagster._core.definitions.asset_checks.asset_check_evaluation import AssetCheckEvaluation
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_key import AssetOrCheckKey, EntityKey
from dagster._core.definitions.assets.graph.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AutomationConditionEvaluation,
)
from dagster._core.definitions.dynamic_partitions_request import (
    AddDynamicPartitionsRequest,
    DeleteDynamicPartitionsRequest,
)
from dagster._core.definitions.events import AssetKey, AssetMaterialization, AssetObservation
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.partitions.partition_key_range import PartitionKeyRange
from dagster._core.errors import DagsterInvalidInvocationError, DagsterInvalidSubsetError
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
    PARTITION_NAME_TAG,
)
from dagster._record import IHaveNew, LegacyNamedTupleMixin, record_custom
from dagster._utils.error import SerializableErrorInfo
from dagster._utils.tags import normalize_tags

if TYPE_CHECKING:
    from dagster._core.definitions.assets.graph.base_asset_graph import BaseAssetGraph
    from dagster._core.definitions.job_definition import JobDefinition
    from dagster._core.definitions.partitions.subset.partitions_subset import PartitionsSubset
    from dagster._core.definitions.run_config import RunConfig
    from dagster._core.instance.types import DynamicPartitionsStore


@whitelist_for_serdes(old_storage_names={"JobType"})
class InstigatorType(Enum):
    SCHEDULE = "SCHEDULE"
    SENSOR = "SENSOR"
    AUTO_MATERIALIZE = "AUTO_MATERIALIZE"


@whitelist_for_serdes
class SkipReason(NamedTuple("_SkipReason", [("skip_message", PublicAttr[str | None])])):
    """Represents a skipped evaluation, where no runs are requested. May contain a message to indicate
    why no runs were requested.

    Args:
        skip_message (Optional[str]): A message displayed in the Dagster UI for why this evaluation resulted
            in no requested runs.
    """

    def __new__(cls, skip_message: str | None = None):
        return super().__new__(
            cls,
            skip_message=check.opt_str_param(skip_message, "skip_message"),
        )


@public
@whitelist_for_serdes(kwargs_fields={"asset_graph_subset", "asset_partition_key_range"})
@record_custom
class RunRequest(IHaveNew, LegacyNamedTupleMixin):
    """Represents all the information required to launch a single run.  Must be returned by a
    SensorDefinition or ScheduleDefinition's evaluation function for a run to be launched.

    Args:
        run_key (Optional[str]): A string key to identify this launched run. For sensors, ensures that
            only one run is created per run key across all sensor evaluations.  For schedules,
            ensures that one run is created per tick, across failure recoveries. Passing in a `None`
            value means that a run will always be launched per evaluation.
        run_config (Optional[Union[RunConfig, Mapping[str, Any]]]: Configuration for the run. If the job has
            a :py:class:`PartitionedConfig`, this value will override replace the config
            provided by it.
        tags (Optional[Dict[str, Any]]): A dictionary of tags (string key-value pairs) to attach
            to the launched run.
        job_name (Optional[str]): The name of the job this run request will launch.
            Required for sensors that target multiple jobs.
        asset_selection (Optional[Sequence[AssetKey]]): A subselection of assets that should be
            launched with this run. If the sensor or schedule targets a job, then by default a
            RunRequest returned from it will launch all of the assets in the job. If the sensor
            targets an asset selection, then by default a RunRequest returned from it will launch
            all the assets in the selection. This argument is used to specify that only a subset of
            these assets should be launched, instead of all of them.
        asset_check_keys (Optional[Sequence[AssetCheckKey]]): A subselection of asset checks that
            should be launched with this run. If the sensor/schedule targets a job, then by default a
            RunRequest returned from it will launch all of the asset checks in the job. If the
            sensor/schedule targets an asset selection, then by default a RunRequest returned from it
            will launch all the asset checks in the selection. This argument is used to specify that
            only a subset of these asset checks should be launched, instead of all of them.
        stale_assets_only (bool): Set to true to further narrow the asset
            selection to stale assets. If passed without an asset selection, all stale assets in the
            job will be materialized. If the job does not materialize assets, this flag is ignored.
        partition_key (Optional[str]): The partition key for this run request.
    """

    run_key: str | None
    run_config: Mapping[str, Any]
    tags: Mapping[str, str]
    job_name: str | None
    asset_selection: Sequence[AssetKey] | None
    stale_assets_only: bool
    partition_key: str | None
    asset_check_keys: Sequence[AssetCheckKey] | None
    asset_graph_subset: AssetGraphSubset | None
    asset_partition_key_range: PartitionKeyRange | None

    def __new__(
        cls,
        run_key: str | None = None,
        run_config: Union["RunConfig", Mapping[str, Any]] | None = None,
        tags: Mapping[str, Any] | None = None,
        job_name: str | None = None,
        asset_selection: Sequence[AssetKey] | None = None,
        stale_assets_only: bool = False,
        partition_key: str | None = None,
        asset_check_keys: Sequence[AssetCheckKey] | None = None,
        **kwargs,
    ):
        from dagster._core.definitions.run_config import convert_config_input

        if kwargs.get("asset_graph_subset") is not None:
            # Asset graph subset requests target a backfill, so single-run targeting fields do not
            # apply. Backfill-level run keys, config, and tags are preserved.
            return super().__new__(
                cls,
                run_key=run_key,
                run_config=convert_config_input(run_config) or {},
                tags=normalize_tags(tags),
                job_name=None,
                asset_selection=None,
                stale_assets_only=False,
                partition_key=None,
                asset_check_keys=None,
                asset_graph_subset=check.inst_param(
                    kwargs["asset_graph_subset"], "asset_graph_subset", AssetGraphSubset
                ),
                asset_partition_key_range=None,
            )

        return super().__new__(
            cls,
            run_key=run_key,
            run_config=convert_config_input(run_config) or {},
            tags=normalize_tags(tags),
            job_name=job_name,
            asset_selection=asset_selection,
            stale_assets_only=stale_assets_only,
            partition_key=partition_key,
            asset_check_keys=asset_check_keys,
            asset_graph_subset=None,
            asset_partition_key_range=check.opt_inst_param(
                kwargs.get("asset_partition_key_range"),
                "asset_partition_key_range",
                PartitionKeyRange,
            ),
        )

    @classmethod
    def for_asset_graph_subset(
        cls,
        asset_graph_subset: AssetGraphSubset,
        tags: Mapping[str, str] | None,
    ) -> "RunRequest":
        """Constructs a RunRequest from an AssetGraphSubset. When processed by the sensor
        daemon, this will launch a backfill instead of a run.
        Note: This constructor is intentionally left private since AssetGraphSubset is not part of the
        public API. Other constructor methods will be public.
        """
        return RunRequest(tags=tags, asset_graph_subset=asset_graph_subset)

    @property
    def is_job_entity_request(self) -> bool:
        """Whether this run request launches a whole job by name -- the shape produced
        when a job-level automation condition fires -- rather than targeting a selection
        of assets or checks: job_name is set and there is no asset or check selection.
        """
        return bool(self.job_name) and not self.asset_selection and not self.asset_check_keys

    @public
    @classmethod
    def for_asset_partition_range(
        cls,
        *,
        run_key: str | None = None,
        asset_selection: Sequence[AssetKey],
        partition_key_range: PartitionKeyRange,
        run_config: Union["RunConfig", Mapping[str, Any]] | None = None,
        tags: Mapping[str, Any] | None = None,
    ) -> "RunRequest":
        """Constructs a request for an asset backfill over a contiguous partition range.

        When processed by the sensor daemon, this request launches a backfill instead of a single
        run. The selected assets and partition range are validated after the sensor finishes
        evaluating, including any dynamic partition changes requested in the same sensor result.
        All partitioned assets in ``asset_selection`` must have the same partitions definition,
        both endpoints must be valid partition keys, and the range must contain at least two
        partitions. Unpartitioned assets in the selection are also included.

        Args:
            run_key (Optional[str]): A key that ensures only one backfill is created across sensor
                evaluations for this request.
            asset_selection (Sequence[AssetKey]): Asset keys to include in the backfill.
            partition_key_range (PartitionKeyRange): Inclusive range of partition keys to target.
            run_config (Optional[Union[RunConfig, Mapping[str, Any]]]): Configuration for runs
                launched by the backfill.
            tags (Optional[Mapping[str, Any]]): Tags to attach to the backfill and its runs.
        """
        asset_keys = check.sequence_param(asset_selection, "asset_selection", of_type=AssetKey)
        check.invariant(asset_keys, "asset_selection must contain at least one asset key")
        partition_key_range = check.inst_param(
            partition_key_range, "partition_key_range", PartitionKeyRange
        )
        return RunRequest(
            run_key=run_key,
            run_config=run_config,
            tags=tags,
            asset_selection=asset_keys,
            asset_partition_key_range=partition_key_range,
        )

    def with_resolved_asset_partition_range(
        self,
        asset_graph: "BaseAssetGraph",
        dynamic_partitions_store: "DynamicPartitionsStore",
    ) -> "RunRequest":
        """Validates and resolves an asset partition range request into a backfill subset."""
        partition_key_range = check.not_none(self.asset_partition_key_range)
        asset_keys = set(check.not_none(self.asset_selection))

        missing_asset_keys = {
            asset_key for asset_key in asset_keys if not asset_graph.has(asset_key)
        }
        if missing_asset_keys:
            raise DagsterInvalidSubsetError(
                "Asset partition range request includes asset keys that do not exist: "
                f"{sorted(missing_asset_keys)}"
            )

        non_materializable_asset_keys = {
            asset_key
            for asset_key in asset_keys
            if not asset_graph.get(asset_key).is_materializable
        }
        if non_materializable_asset_keys:
            raise DagsterInvalidSubsetError(
                "Asset partition range request includes non-materializable asset keys: "
                f"{sorted(non_materializable_asset_keys)}"
            )

        required_asset_keys = {
            execution_set_key
            for asset_key in asset_keys
            for execution_set_key in asset_graph.get_execution_set_asset_and_check_keys(asset_key)
            if isinstance(execution_set_key, AssetKey)
        }
        missing_required_asset_keys = required_asset_keys - asset_keys
        if missing_required_asset_keys:
            raise DagsterInvalidSubsetError(
                "Asset partition range request must include asset keys that are required to execute "
                f"together: {sorted(missing_required_asset_keys)}"
            )

        partitioned_assets = [
            (asset_key, partitions_def)
            for asset_key in sorted(asset_keys)
            if (partitions_def := asset_graph.get(asset_key).partitions_def) is not None
        ]
        if not partitioned_assets:
            raise DagsterInvalidInvocationError(
                "asset_selection must contain at least one partitioned asset"
            )

        partitions_def = partitioned_assets[0][1]
        if any(
            candidate_partitions_def != partitions_def
            for _, candidate_partitions_def in partitioned_assets
        ):
            raise DagsterInvalidInvocationError(
                "All partitioned assets in an asset partition range request must have the same "
                "partitions definition"
            )

        with partition_loading_context(dynamic_partitions_store=dynamic_partitions_store):
            for endpoint_name, partition_key in [
                ("start", partition_key_range.start),
                ("end", partition_key_range.end),
            ]:
                if not partitions_def.has_partition_key(partition_key):
                    raise DagsterInvalidInvocationError(
                        f"partition_key_range {endpoint_name} {partition_key!r} is not a valid "
                        "partition key for the selected assets"
                    )

            partitioned_subsets: dict[AssetKey, PartitionsSubset] = {
                asset_key: candidate_partitions_def.empty_subset().with_partition_key_range(
                    candidate_partitions_def, partition_key_range
                )
                for asset_key, candidate_partitions_def in partitioned_assets
            }

        if not all(len(subset) > 1 for subset in partitioned_subsets.values()):
            raise DagsterInvalidInvocationError(
                "partition_key_range must contain at least two partitions for each partitioned asset"
            )

        non_partitioned_asset_keys = asset_keys - set(partitioned_subsets)

        return RunRequest(
            run_key=self.run_key,
            run_config=self.run_config,
            tags=self.tags,
            asset_graph_subset=AssetGraphSubset(
                partitions_subsets_by_asset_key=partitioned_subsets,
                non_partitioned_asset_keys=non_partitioned_asset_keys,
            ),
        )

    def with_replaced_attrs(self, **kwargs: Any) -> "RunRequest":
        fields = dict(self._asdict())
        for k in fields.keys():
            if k in kwargs:
                fields[k] = kwargs[k]
        return RunRequest(**fields)

    def with_resolved_tags_and_config(
        self,
        target_definition: "JobDefinition",
        dynamic_partitions_requests: Sequence[
            AddDynamicPartitionsRequest | DeleteDynamicPartitionsRequest
        ],
        dynamic_partitions_store: Optional["DynamicPartitionsStore"],
    ) -> "RunRequest":
        from dagster._core.instance.types import DynamicPartitionsStoreAfterRequests

        if self.partition_key is None:
            check.failed(
                "Cannot resolve partition for run request without partition key",
            )

        dynamic_partitions_store_after_requests = (
            DynamicPartitionsStoreAfterRequests.from_requests(
                dynamic_partitions_store, dynamic_partitions_requests
            )
            if dynamic_partitions_store
            else None
        )
        with partition_loading_context(
            dynamic_partitions_store=dynamic_partitions_store_after_requests
        ) as ctx:
            context = ctx

        target_definition.validate_partition_key(
            self.partition_key, selected_asset_keys=self.asset_selection, context=context
        )

        tags = {
            **(self.tags or {}),
            **target_definition.get_tags_for_partition_key(
                self.partition_key, selected_asset_keys=self.asset_selection
            ),
        }

        return self.with_replaced_attrs(
            run_config=(
                self.run_config
                if self.run_config
                else target_definition.get_run_config_for_partition_key(self.partition_key)
            ),
            tags=tags,
        )

    def has_resolved_partition(self) -> bool:
        # Backcompat run requests yielded via `run_request_for_partition` already have resolved
        # partitioning
        return self.tags.get(PARTITION_NAME_TAG) is not None if self.partition_key else True

    @property
    def partition_key_range(self) -> PartitionKeyRange | None:
        if (
            ASSET_PARTITION_RANGE_START_TAG in self.tags
            and ASSET_PARTITION_RANGE_END_TAG in self.tags
        ):
            return PartitionKeyRange(
                self.tags[ASSET_PARTITION_RANGE_START_TAG], self.tags[ASSET_PARTITION_RANGE_END_TAG]
            )
        else:
            return None

    @property
    def entity_keys(self) -> Sequence[AssetOrCheckKey]:
        return [*(self.asset_selection or []), *(self.asset_check_keys or [])]

    def requires_backfill_daemon(self) -> bool:
        """For now we always send RunRequests with an asset_graph_subset to the backfill daemon, but
        eventaully we will want to introspect on the asset_graph_subset to determine if we can
        execute it as a single run instead.
        """
        return self.asset_graph_subset is not None or self.asset_partition_key_range is not None


@whitelist_for_serdes(
    storage_name="PipelineRunReaction",
    storage_field_names={
        "dagster_run": "pipeline_run",
    },
)
class DagsterRunReaction(
    NamedTuple(
        "_DagsterRunReaction",
        [
            ("dagster_run", DagsterRun | None),
            ("error", SerializableErrorInfo | None),
            ("run_status", DagsterRunStatus | None),
        ],
    )
):
    """Represents a request that reacts to an existing dagster run. If success, it will report logs
    back to the run.

    Args:
        dagster_run (Optional[DagsterRun]): The dagster run that originates this reaction.
        error (Optional[SerializableErrorInfo]): user code execution error.
        run_status: (Optional[DagsterRunStatus]): The run status that triggered the reaction.
    """

    def __new__(
        cls,
        dagster_run: DagsterRun | None,
        error: SerializableErrorInfo | None = None,
        run_status: DagsterRunStatus | None = None,
    ):
        return super().__new__(
            cls,
            dagster_run=check.opt_inst_param(dagster_run, "dagster_run", DagsterRun),
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
            run_status=check.opt_inst_param(run_status, "run_status", DagsterRunStatus),
        )


@public
class SensorResult(
    NamedTuple(
        "_SensorResult",
        [
            ("run_requests", Sequence[RunRequest] | None),
            ("skip_reason", SkipReason | None),
            ("cursor", str | None),
            (
                "dynamic_partitions_requests",
                Sequence[DeleteDynamicPartitionsRequest | AddDynamicPartitionsRequest] | None,
            ),
            (
                "asset_events",
                list[AssetObservation | AssetMaterialization | AssetCheckEvaluation],
            ),
            (
                "automation_condition_evaluations",
                Sequence[AutomationConditionEvaluation[EntityKey]] | None,
            ),
        ],
    )
):
    """The result of a sensor evaluation.

    Args:
        run_requests (Optional[Sequence[RunRequest]]): A list of run requests to be executed.
        skip_reason (Optional[Union[str, SkipReason]]): A skip message indicating why sensor
            evaluation was skipped.
        cursor (Optional[str]): The cursor value for this sensor, which will be provided on the
            context for the next sensor evaluation.
        dynamic_partitions_requests (Optional[Sequence[Union[DeleteDynamicPartitionsRequest, AddDynamicPartitionsRequest]]]): A list of dynamic partition requests to request dynamic
            partition addition and deletion. Run requests will be evaluated using the state of the
            partitions with these changes applied. We recommend limiting partition additions
            and deletions to a maximum of 25K partitions per sensor evaluation, as this is the maximum
            recommended partition limit per asset.
        asset_events (Optional[Sequence[Union[AssetObservation, AssetMaterialization, AssetCheckEvaluation]]]): A
            list of materializations, observations, and asset check evaluations that the system
            will persist on your behalf at the end of sensor evaluation. These events will be not
            be associated with any particular run, but will be queryable and viewable in the asset catalog.


    """

    def __new__(
        cls,
        run_requests: Sequence[RunRequest] | None = None,
        skip_reason: str | SkipReason | None = None,
        cursor: str | None = None,
        dynamic_partitions_requests: Sequence[
            DeleteDynamicPartitionsRequest | AddDynamicPartitionsRequest
        ]
        | None = None,
        asset_events: Sequence[AssetObservation | AssetMaterialization | AssetCheckEvaluation]
        | None = None,
        **kwargs,
    ):
        if skip_reason and len(run_requests if run_requests else []) > 0:
            check.failed(
                "Expected a single skip reason or one or more run requests: received values for "
                "both run_requests and skip_reason"
            )

        skip_reason = check.opt_inst_param(skip_reason, "skip_reason", (SkipReason, str))
        if isinstance(skip_reason, str):
            skip_reason = SkipReason(skip_reason)

        return super().__new__(
            cls,
            run_requests=check.opt_sequence_param(run_requests, "run_requests", RunRequest),
            skip_reason=skip_reason,
            cursor=check.opt_str_param(cursor, "cursor"),
            dynamic_partitions_requests=check.opt_sequence_param(
                dynamic_partitions_requests,
                "dynamic_partitions_requests",
                (AddDynamicPartitionsRequest, DeleteDynamicPartitionsRequest),
            ),
            asset_events=list(
                check.opt_sequence_param(
                    asset_events,
                    "asset_check_evaluations",
                    (AssetObservation, AssetMaterialization, AssetCheckEvaluation),
                )
            ),
            automation_condition_evaluations=check.opt_sequence_param(
                kwargs.get("automation_condition_evaluations"),
                "automation_condition_evaluations",
                AutomationConditionEvaluation,
            ),
        )
