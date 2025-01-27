from collections.abc import Iterable, Mapping, Sequence
from typing import AbstractSet, Any, Optional  # noqa: UP035

import dagster._check as check
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.repository_definition import SINGLETON_REPOSITORY_NAME
from dagster._record import IHaveNew, record, record_custom
from dagster._serdes import create_snapshot_id, whitelist_for_serdes


@record_custom
class JobSubsetSelector(IHaveNew):
    """The information needed to resolve a job within a host process."""

    location_name: str
    repository_name: str
    job_name: str
    op_selection: Optional[Sequence[str]]
    asset_selection: Optional[AbstractSet[AssetKey]]
    asset_check_selection: Optional[AbstractSet[AssetCheckKey]]

    def __new__(
        cls,
        location_name: str,
        repository_name: str,
        job_name: str,
        op_selection: Optional[Sequence[str]],
        asset_selection: Optional[Iterable[AssetKey]] = None,
        asset_check_selection: Optional[Iterable[AssetCheckKey]] = None,
    ):
        # coerce iterables to sets
        asset_selection = frozenset(asset_selection) if asset_selection else None
        asset_check_selection = (
            frozenset(asset_check_selection) if asset_check_selection is not None else None
        )
        return super().__new__(
            cls,
            location_name=location_name,
            repository_name=repository_name,
            job_name=job_name,
            op_selection=op_selection,
            asset_selection=asset_selection,
            asset_check_selection=asset_check_selection,
        )

    def to_graphql_input(self):
        return {
            "repositoryLocationName": self.location_name,
            "repositoryName": self.repository_name,
            "pipelineName": self.job_name,
            "solidSelection": self.op_selection,
        }

    @property
    def is_subset_selection(self) -> bool:
        return bool(self.op_selection or self.asset_selection or self.asset_check_selection)

    def with_op_selection(self, op_selection: Optional[Sequence[str]]) -> "JobSubsetSelector":
        check.invariant(
            self.op_selection is None,
            f"Can not invoke with_op_selection when op_selection={self.op_selection} is"
            " already set",
        )
        return JobSubsetSelector(
            self.location_name, self.repository_name, self.job_name, op_selection
        )

    @property
    def repository_selector(self) -> "RepositorySelector":
        return RepositorySelector(
            location_name=self.location_name,
            repository_name=self.repository_name,
        )


@whitelist_for_serdes
@record_custom
class JobSelector(IHaveNew):
    location_name: str
    repository_name: str
    job_name: str

    def __new__(
        cls,
        location_name: str,
        repository_name: Optional[str] = None,
        job_name: Optional[str] = None,
    ):
        check.invariant(
            job_name is not None,
            "Must provide job_name argument even though it is marked as optional in the "
            "function signature. repository_name, a truly optional parameter, is before "
            "that argument and actually optional. Use of keyword arguments is "
            "recommended to avoid confusion.",
        )

        return super().__new__(
            cls,
            location_name=location_name,
            repository_name=repository_name or SINGLETON_REPOSITORY_NAME,
            job_name=job_name,
        )

    def to_graphql_input(self):
        return {
            "repositoryLocationName": self.location_name,
            "repositoryName": self.repository_name,
            "jobName": self.job_name,
        }

    @property
    def selector_id(self):
        return create_snapshot_id(self)

    @staticmethod
    def from_graphql_input(graphql_data):
        return JobSelector(
            location_name=graphql_data["repositoryLocationName"],
            repository_name=graphql_data["repositoryName"],
            job_name=graphql_data["jobName"],
        )

    @property
    def repository_selector(self) -> "RepositorySelector":
        return RepositorySelector(
            location_name=self.location_name,
            repository_name=self.repository_name,
        )


@whitelist_for_serdes
@record
class RepositorySelector:
    location_name: str
    repository_name: str

    def to_graphql_input(self):
        return {
            "repositoryLocationName": self.location_name,
            "repositoryName": self.repository_name,
        }

    @property
    def selector_id(self):
        return create_snapshot_id(self)

    @staticmethod
    def from_graphql_input(graphql_data):
        return RepositorySelector(
            location_name=graphql_data["repositoryLocationName"],
            repository_name=graphql_data["repositoryName"],
        )


@record
class AssetGroupSelector:
    group_name: str
    location_name: str
    repository_name: str

    @staticmethod
    def from_graphql_input(graphql_data):
        return AssetGroupSelector(
            group_name=graphql_data["groupName"],
            location_name=graphql_data["repositoryLocationName"],
            repository_name=graphql_data["repositoryName"],
        )


@record(kw_only=False)
class CodeLocationSelector:
    location_name: str

    def to_repository_selector(self) -> RepositorySelector:
        return RepositorySelector(
            location_name=self.location_name,
            repository_name=SINGLETON_REPOSITORY_NAME,
        )


@record
class ScheduleSelector:
    location_name: str
    repository_name: str
    schedule_name: str

    def to_graphql_input(self):
        return {
            "repositoryLocationName": self.location_name,
            "repositoryName": self.repository_name,
            "scheduleName": self.schedule_name,
        }

    @property
    def instigator_name(self) -> str:
        return self.schedule_name

    @staticmethod
    def from_graphql_input(graphql_data):
        return ScheduleSelector(
            location_name=graphql_data["repositoryLocationName"],
            repository_name=graphql_data["repositoryName"],
            schedule_name=graphql_data["scheduleName"],
        )


@record
class ResourceSelector:
    location_name: str
    repository_name: str
    resource_name: str

    def to_graphql_input(self):
        return {
            "repositoryLocationName": self.location_name,
            "repositoryName": self.repository_name,
            "resourceName": self.resource_name,
        }

    @staticmethod
    def from_graphql_input(graphql_data):
        return ResourceSelector(
            location_name=graphql_data["repositoryLocationName"],
            repository_name=graphql_data["repositoryName"],
            resource_name=graphql_data["resourceName"],
        )


@record
class SensorSelector:
    location_name: str
    repository_name: str
    sensor_name: str

    def to_graphql_input(self):
        return {
            "repositoryLocationName": self.location_name,
            "repositoryName": self.repository_name,
            "sensorName": self.sensor_name,
        }

    @staticmethod
    def from_graphql_input(graphql_data):
        return SensorSelector(
            location_name=graphql_data["repositoryLocationName"],
            repository_name=graphql_data["repositoryName"],
            sensor_name=graphql_data["sensorName"],
        )

    @property
    def instigator_name(self) -> str:
        return self.sensor_name


@whitelist_for_serdes
@record
class InstigatorSelector:
    location_name: str
    repository_name: str
    name: str

    def to_graphql_input(self):
        return {
            "repositoryLocationName": self.location_name,
            "repositoryName": self.repository_name,
            "name": self.name,
        }

    @staticmethod
    def from_graphql_input(graphql_data):
        return InstigatorSelector(
            location_name=graphql_data["repositoryLocationName"],
            repository_name=graphql_data["repositoryName"],
            name=graphql_data["name"],
        )

    def get_id(self) -> str:
        return create_snapshot_id(self)


@record
class GraphSelector:
    """The information needed to resolve a graph within a host process."""

    location_name: str
    repository_name: str
    graph_name: str

    def to_graphql_input(self):
        return {
            "repositoryLocationName": self.location_name,
            "repositoryName": self.repository_name,
            "graphName": self.graph_name,
        }


@whitelist_for_serdes
@record
class PartitionSetSelector:
    """The information needed to resolve a partition set within a host process."""

    location_name: str
    repository_name: str
    partition_set_name: str

    def to_graphql_input(self):
        return {
            "repositoryLocationName": self.location_name,
            "repositoryName": self.repository_name,
            "partitionSetName": self.partition_set_name,
        }


@record(kw_only=False)
class PartitionRangeSelector:
    """The information needed to resolve a partition range."""

    start: str
    end: str

    def to_graphql_input(self):
        return {
            "start": self.start,
            "end": self.end,
        }

    @staticmethod
    def from_graphql_input(graphql_data):
        return PartitionRangeSelector(
            start=graphql_data["start"],
            end=graphql_data["end"],
        )


@record(kw_only=False)
class PartitionsSelector:
    """The information needed to define selection partitions."""

    ranges: Sequence[PartitionRangeSelector]

    def to_graphql_input(self):
        return {"ranges": [partition_range.to_graphql_input() for partition_range in self.ranges]}

    @staticmethod
    def from_graphql_input(graphql_data: Mapping[str, Any]) -> "PartitionsSelector":
        if "ranges" in graphql_data:
            check.invariant(
                "range" not in graphql_data,
                "Received partitionsSelector with values for both 'range' and 'ranges'. Only one should be provided.",
            )
            return PartitionsSelector(
                ranges=[
                    PartitionRangeSelector.from_graphql_input(range_data)
                    for range_data in graphql_data["ranges"]
                ]
            )

        if "range" in graphql_data:
            return PartitionsSelector(
                ranges=[PartitionRangeSelector.from_graphql_input(graphql_data["range"])]
            )

        check.failed(
            "Received partitionsSelector without values for either 'range' or 'ranges'. One should be provided.",
        )


@record
class PartitionsByAssetSelector:
    """The information needed to define partitions selection for a given asset key."""

    asset_key: AssetKey
    partitions: Optional[PartitionsSelector] = None

    def to_graphql_input(self):
        return {
            "assetKey": self.asset_key.to_graphql_input(),
            "partitions": self.partitions.to_graphql_input() if self.partitions else None,
        }

    @staticmethod
    def from_graphql_input(graphql_data) -> "PartitionsByAssetSelector":
        asset_key = graphql_data["assetKey"]
        partitions = graphql_data.get("partitions")
        return PartitionsByAssetSelector(
            asset_key=AssetKey.from_graphql_input(asset_key),
            partitions=PartitionsSelector.from_graphql_input(partitions) if partitions else None,
        )
