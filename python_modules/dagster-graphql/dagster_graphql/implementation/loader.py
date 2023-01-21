from collections import defaultdict
from enum import Enum
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from dagster import (
    DagsterInstance,
    _check as check,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.logical_version import (
    CachingProjectedLogicalVersionResolver,
)
from dagster._core.events.log import EventLogEntry
from dagster._core.host_representation import ExternalRepository
from dagster._core.host_representation.external_data import (
    ExternalAssetDependedBy,
    ExternalAssetDependency,
    ExternalAssetNode,
)
from dagster._core.scheduler.instigation import InstigatorType
from dagster._core.storage.pipeline_run import JobBucket, RunRecord, RunsFilter, TagBucket
from dagster._core.storage.tags import REPOSITORY_LABEL_TAG, SCHEDULE_NAME_TAG, SENSOR_NAME_TAG
from dagster._core.workspace.context import WorkspaceRequestContext


class RepositoryDataType(Enum):
    JOB_RUNS = "job_runs"
    SCHEDULE_RUNS = "schedule_runs"
    SENSOR_RUNS = "sensor_runs"
    SCHEDULE_STATES = "schedule_states"
    SENSOR_STATES = "sensor_states"
    SCHEDULE_TICKS = "schedule_ticks"
    SENSOR_TICKS = "sensor_ticks"


class RepositoryScopedBatchLoader:
    """
    A batch loader that fetches an assortment of data for a given repository.  This loader is
    expected to be instantiated once per repository, and then passed to various child graphene
    objects to batch calls to the DB.

    We can instantiate this loader without knowing which data we will end up requesting deeper in
    the graphql nested schema, which means we can batch DB requests without changing the structure
     of our graphql request.

    Example: When the last 10 runs are requested for a job in the repository, we know that they will
    be fetched for every job in the repository.  We can batch fetch the last 10 runs for every job,
    reducing the number of roundtrips to the DB, and then access them using the in-memory loader
    cache.
    """

    def __init__(self, instance: DagsterInstance, external_repository: ExternalRepository):
        self._instance = instance
        self._repository = external_repository
        self._data: Dict[RepositoryDataType, Dict[str, List[Any]]] = {}
        self._limits: Dict[RepositoryDataType, int] = {}

    def _get(self, data_type: RepositoryDataType, key: str, limit: int) -> Sequence[Any]:
        check.inst_param(data_type, "data_type", RepositoryDataType)
        check.str_param(key, "key")
        check.int_param(limit, "limit")
        if self._data.get(data_type) is None or limit > self._limits.get(data_type, 0):
            self._fetch(data_type, limit)
        return self._data[data_type].get(key, [])[:limit]

    def _fetch(self, data_type: RepositoryDataType, limit: int) -> None:
        check.inst_param(data_type, "data_type", RepositoryDataType)
        check.int_param(limit, "limit")

        fetched: Dict[str, List[Any]] = defaultdict(list)

        if data_type == RepositoryDataType.JOB_RUNS:
            job_names = [x.name for x in self._repository.get_all_external_jobs()]
            if self._instance.supports_bucket_queries and len(job_names) > 1:
                records = self._instance.get_run_records(
                    filters=RunsFilter(
                        tags={
                            REPOSITORY_LABEL_TAG: self._repository.get_external_origin().get_label(),
                        },
                    ),
                    bucket_by=JobBucket(bucket_limit=limit, job_names=job_names),
                )
            else:
                records = []
                for job_name in job_names:
                    records.extend(
                        list(
                            self._instance.get_run_records(
                                filters=RunsFilter(
                                    pipeline_name=job_name,
                                    tags={
                                        REPOSITORY_LABEL_TAG: self._repository.get_external_origin().get_label(),
                                    },
                                ),
                                limit=limit,
                            )
                        )
                    )
            for record in records:
                fetched[record.pipeline_run.pipeline_name].append(record)

        elif data_type == RepositoryDataType.SCHEDULE_RUNS:
            schedule_names = [
                schedule.name for schedule in self._repository.get_external_schedules()
            ]
            if self._instance.supports_bucket_queries and len(schedule_names) > 1:
                records = self._instance.get_run_records(
                    filters=RunsFilter(
                        tags={
                            REPOSITORY_LABEL_TAG: self._repository.get_external_origin().get_label(),
                        }
                    ),
                    bucket_by=TagBucket(
                        tag_key=SCHEDULE_NAME_TAG,
                        bucket_limit=limit,
                        tag_values=schedule_names,
                    ),
                )
            else:
                records = []
                for schedule_name in schedule_names:
                    records.extend(
                        list(
                            self._instance.get_run_records(
                                filters=RunsFilter(
                                    tags={
                                        SCHEDULE_NAME_TAG: schedule_name,
                                        REPOSITORY_LABEL_TAG: self._repository.get_external_origin().get_label(),
                                    }
                                ),
                                limit=limit,
                            )
                        )
                    )
            for record in records:
                tag: str = check.not_none(record.pipeline_run.tags.get(SCHEDULE_NAME_TAG))
                fetched[tag].append(record)

        elif data_type == RepositoryDataType.SENSOR_RUNS:
            sensor_names = [sensor.name for sensor in self._repository.get_external_sensors()]
            if self._instance.supports_bucket_queries and len(sensor_names) > 1:
                records = self._instance.get_run_records(
                    filters=RunsFilter(
                        tags={
                            REPOSITORY_LABEL_TAG: self._repository.get_external_origin().get_label(),
                        }
                    ),
                    bucket_by=TagBucket(
                        tag_key=SENSOR_NAME_TAG,
                        bucket_limit=limit,
                        tag_values=sensor_names,
                    ),
                )
            else:
                records = []
                for sensor_name in sensor_names:
                    records.extend(
                        list(
                            self._instance.get_run_records(
                                filters=RunsFilter(
                                    tags={
                                        SENSOR_NAME_TAG: sensor_name,
                                        REPOSITORY_LABEL_TAG: self._repository.get_external_origin().get_label(),
                                    }
                                ),
                                limit=limit,
                            )
                        )
                    )
            for record in records:
                tag = check.not_none(record.pipeline_run.tags.get(SENSOR_NAME_TAG))
                fetched[tag].append(record)

        elif data_type == RepositoryDataType.SCHEDULE_STATES:
            schedule_states = self._instance.all_instigator_state(
                repository_origin_id=self._repository.get_external_origin_id(),
                repository_selector_id=self._repository.selector_id,
                instigator_type=InstigatorType.SCHEDULE,
            )
            for state in schedule_states:
                fetched[state.name].append(state)

        elif data_type == RepositoryDataType.SENSOR_STATES:
            sensor_states = self._instance.all_instigator_state(
                repository_origin_id=self._repository.get_external_origin_id(),
                repository_selector_id=self._repository.selector_id,
                instigator_type=InstigatorType.SENSOR,
            )
            for state in sensor_states:
                fetched[state.name].append(state)

        elif data_type == RepositoryDataType.SCHEDULE_TICKS:
            if self._instance.supports_batch_tick_queries:
                selector_ids = [
                    schedule.selector_id for schedule in self._repository.get_external_schedules()
                ]
                ticks_by_selector = self._instance.get_batch_ticks(selector_ids, limit=limit)
                for schedule in self._repository.get_external_schedules():
                    fetched[schedule.get_external_origin_id()] = list(
                        ticks_by_selector.get(schedule.selector_id, [])
                    )
            else:
                for schedule in self._repository.get_external_schedules():
                    origin_id = schedule.get_external_origin_id()
                    fetched[origin_id] = list(
                        self._instance.get_ticks(origin_id, schedule.selector_id, limit=limit)
                    )

        elif data_type == RepositoryDataType.SENSOR_TICKS:
            if self._instance.supports_batch_tick_queries:
                selector_ids = [
                    schedule.selector_id for schedule in self._repository.get_external_sensors()
                ]
                ticks_by_selector = self._instance.get_batch_ticks(selector_ids, limit=limit)
                for sensor in self._repository.get_external_sensors():
                    fetched[sensor.get_external_origin_id()] = list(
                        ticks_by_selector.get(sensor.selector_id, [])
                    )
            else:
                for sensor in self._repository.get_external_sensors():
                    origin_id = sensor.get_external_origin_id()
                    fetched[origin_id] = list(
                        self._instance.get_ticks(origin_id, sensor.selector_id, limit=limit)
                    )

        else:
            check.failed(f"Unknown data type for {self.__class__.__name__}: {data_type}")

        self._data[data_type] = fetched
        self._limits[data_type] = limit

    def get_run_records_for_job(self, job_name: str, limit: int) -> Sequence[Any]:
        check.invariant(self._repository.has_external_job(job_name))
        return self._get(RepositoryDataType.JOB_RUNS, job_name, limit)

    def get_run_records_for_schedule(self, schedule_name: str, limit: int) -> Sequence[Any]:
        check.invariant(self._repository.has_external_schedule(schedule_name))
        return self._get(RepositoryDataType.SCHEDULE_RUNS, schedule_name, limit)

    def get_run_records_for_sensor(self, sensor_name: str, limit: int) -> Sequence[Any]:
        check.invariant(self._repository.has_external_sensor(sensor_name))
        return self._get(RepositoryDataType.SENSOR_RUNS, sensor_name, limit)

    def get_schedule_state(self, schedule_name: str) -> Optional[Sequence[Any]]:
        check.invariant(self._repository.has_external_schedule(schedule_name))
        states = self._get(RepositoryDataType.SCHEDULE_STATES, schedule_name, 1)
        return states[0] if states else None

    def get_sensor_state(self, sensor_name: str) -> Optional[Sequence[Any]]:
        check.invariant(self._repository.has_external_sensor(sensor_name))
        states = self._get(RepositoryDataType.SENSOR_STATES, sensor_name, 1)
        return states[0] if states else None

    def get_sensor_ticks(self, origin_id: str, selector_id: str, limit: int) -> Sequence[Any]:
        check.invariant(
            any(
                selector_id == sensor.selector_id
                for sensor in self._repository.get_external_sensors()
            )
        )
        return self._get(RepositoryDataType.SENSOR_TICKS, origin_id, limit)

    def get_schedule_ticks(self, origin_id: str, selector_id: str, limit: int) -> Sequence[Any]:
        check.invariant(
            any(
                selector_id == schedule.selector_id
                for schedule in self._repository.get_external_schedules()
            )
        )
        return self._get(RepositoryDataType.SCHEDULE_TICKS, origin_id, limit)


class BatchRunLoader:
    """
    A batch loader that fetches a set of runs by run_id. This loader is expected to be instantiated
    once with a set of run_ids. For example, for a particular asset, we can fetch a list of asset
    materializations, all of which may have been materialized from a different run.
    """

    def __init__(self, instance: DagsterInstance, run_ids: Iterable[str]):
        self._instance = instance
        self._run_ids: Set[str] = set(run_ids)
        self._records: Dict[str, RunRecord] = {}

    def get_run_record_by_run_id(self, run_id: str) -> Optional[RunRecord]:
        if run_id not in self._run_ids:
            check.failed(
                f"Run id {run_id} not recognized for this loader.  Expected one of: {self._run_ids}"
            )
        if self._records.get(run_id) is None:
            self._fetch()
        return self._records.get(run_id)

    def _fetch(self) -> None:
        records = self._instance.get_run_records(RunsFilter(run_ids=list(self._run_ids)))
        for record in records:
            self._records[record.pipeline_run.run_id] = record


class BatchMaterializationLoader:
    """
    A batch loader that fetches materializations for asset keys.  This loader is expected to be
    instantiated with a set of asset keys.
    """

    def __init__(self, instance: DagsterInstance, asset_keys: Iterable[AssetKey]):
        self._instance = instance
        self._asset_keys: List[AssetKey] = list(asset_keys)
        self._fetched = False
        self._materializations: Mapping[AssetKey, Optional[EventLogEntry]] = {}

    def get_latest_materialization_for_asset_key(
        self, asset_key: AssetKey
    ) -> Optional[EventLogEntry]:
        if asset_key not in self._asset_keys:
            check.failed(
                f"Asset key {asset_key} not recognized for this loader.  Expected one of:"
                f" {self._asset_keys}"
            )

        if not self._fetched:
            self._fetch()
        return self._materializations.get(asset_key)

    def _fetch(self) -> None:
        self._fetched = True
        self._materializations = {
            record.asset_entry.asset_key: record.asset_entry.last_materialization
            for record in self._instance.get_asset_records(self._asset_keys)
        }


class CrossRepoAssetDependedByLoader:
    """
    A batch loader that computes cross-repository asset dependencies. Locates source assets
    within all workspace repositories, and determines if they are derived (defined) assets in
    other repositories.

    For each asset that contains cross-repo dependencies (every asset that is defined as a source
    asset in another repository) a sink asset is any asset immediately downstream of the source
    asset.

    E.g. Asset A is defined in repo X and referenced in repo Y as source asset C (but contains the
    same asset key as A). If within repo C has a downstream asset B, B is a sink asset of A (it
    is external from A's repo but an edge exists from A to B).

    The @lru_cache decorator enables the _build_cross_repo_deps method to cache its return value
    to avoid recalculating the asset dependencies on repeated calls to the method.
    """

    def __init__(self, context: WorkspaceRequestContext):
        self._context = context

    @lru_cache(maxsize=1)
    def _build_cross_repo_deps(
        self,
    ) -> Tuple[
        Dict[AssetKey, ExternalAssetNode],
        Dict[Tuple[str, str], Dict[AssetKey, List[ExternalAssetDependedBy]]],
    ]:
        """
        This method constructs a sink asset as an ExternalAssetNode for every asset immediately
        downstream of a source asset that is defined in another repository as a derived asset.

        In Dagit, sink assets will display as ForeignAssets, which are external from the repository.

        This method also stores a mapping from source asset key to ExternalAssetDependedBy nodes
        that depend on the asset with that key. When get_cross_repo_dependent_assets is called with a derived
        asset's asset key and its location, all dependent ExternalAssetDependedBy nodes are returned.
        """
        depended_by_assets_by_source_asset: Dict[AssetKey, List[ExternalAssetDependedBy]] = {}

        map_defined_asset_to_location: Dict[
            AssetKey, Tuple[str, str]
        ] = {}  # key is asset key, value is tuple (location_name, repo_name)

        external_asset_node_by_asset_key: Dict[
            AssetKey, ExternalAssetNode
        ] = {}  # only contains derived assets
        for location in self._context.repository_locations:
            repositories = location.get_repositories()
            for repo_name, external_repo in repositories.items():
                asset_nodes = external_repo.get_external_asset_nodes()
                for asset_node in asset_nodes:
                    if not asset_node.op_name:  # is source asset
                        if asset_node.asset_key not in depended_by_assets_by_source_asset:
                            depended_by_assets_by_source_asset[asset_node.asset_key] = []
                        depended_by_assets_by_source_asset[asset_node.asset_key].extend(
                            asset_node.depended_by
                        )
                    else:
                        map_defined_asset_to_location[asset_node.asset_key] = (
                            location.name,
                            repo_name,
                        )
                        external_asset_node_by_asset_key[asset_node.asset_key] = asset_node

        sink_assets: Dict[AssetKey, ExternalAssetNode] = {}
        external_asset_deps: Dict[
            Tuple[str, str], Dict[AssetKey, List[ExternalAssetDependedBy]]
        ] = (
            {}
        )  # nested dict that maps dependedby assets by asset key by location tuple (repo_location.name, repo_name)

        for source_asset, depended_by_assets in depended_by_assets_by_source_asset.items():
            asset_def_location = map_defined_asset_to_location.get(source_asset, None)
            if asset_def_location:  # source asset is defined as asset in another repository
                if asset_def_location not in external_asset_deps:
                    external_asset_deps[asset_def_location] = {}
                if source_asset not in external_asset_deps[asset_def_location]:
                    external_asset_deps[asset_def_location][source_asset] = []
                external_asset_deps[asset_def_location][source_asset].extend(depended_by_assets)
                for asset in depended_by_assets:
                    # SourceAssets defined as ExternalAssetNodes contain no definition data (e.g.
                    # no output or partition definition data) and no job_names. Dagit displays
                    # all ExternalAssetNodes with no job_names as foreign assets, so sink assets
                    # are defined as ExternalAssetNodes with no definition data.
                    sink_assets[asset.downstream_asset_key] = ExternalAssetNode(
                        asset_key=asset.downstream_asset_key,
                        dependencies=[
                            ExternalAssetDependency(
                                upstream_asset_key=source_asset,
                                input_name=asset.input_name,
                                output_name=asset.output_name,
                            )
                        ],
                        depended_by=[],
                    )
        return sink_assets, external_asset_deps

    def get_sink_asset(self, asset_key: AssetKey) -> ExternalAssetNode:
        sink_assets, _ = self._build_cross_repo_deps()
        return sink_assets[asset_key]

    def get_cross_repo_dependent_assets(
        self, repository_location_name: str, repository_name: str, asset_key: AssetKey
    ) -> List[ExternalAssetDependedBy]:
        _, external_asset_deps = self._build_cross_repo_deps()
        return external_asset_deps.get((repository_location_name, repository_name), {}).get(
            asset_key, []
        )


class ProjectedLogicalVersionLoader:
    """
    A batch loader that computes the projected logical version for a set of asset keys. This is
    necessary to avoid recomputation, since each asset's logical version is a function of its
    dependency logical versions. We use similar functionality in core, so this loader simply proxies
    to `CachingProjectedLogicalVersionResolver` and extracts the string value of the returned
    `LogicalVersion` objects.
    """

    def __init__(
        self,
        instance: DagsterInstance,
        repositories: Sequence[ExternalRepository],
        key_to_node_map: Optional[Mapping[AssetKey, ExternalAssetNode]],
    ):
        self._caching_resolver = CachingProjectedLogicalVersionResolver(
            instance, repositories, key_to_node_map
        )

    def get(self, asset_key: AssetKey) -> str:
        return self._caching_resolver.get(asset_key).value
