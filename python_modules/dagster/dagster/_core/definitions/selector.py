from typing import NamedTuple, Optional, Sequence

import dagster._check as check
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.repository_definition import SINGLETON_REPOSITORY_NAME
from dagster._serdes import create_snapshot_id, whitelist_for_serdes


class JobSubsetSelector(
    NamedTuple(
        "_JobSubsetSelector",
        [
            ("location_name", str),
            ("repository_name", str),
            ("job_name", str),
            ("solid_selection", Optional[Sequence[str]]),
            ("asset_selection", Optional[Sequence[AssetKey]]),
        ],
    )
):
    """The information needed to resolve a job within a host process."""

    def __new__(
        cls,
        location_name: str,
        repository_name: str,
        job_name: str,
        solid_selection: Optional[Sequence[str]],
        asset_selection: Optional[Sequence[AssetKey]] = None,
    ):
        return super(JobSubsetSelector, cls).__new__(
            cls,
            location_name=check.str_param(location_name, "location_name"),
            repository_name=check.str_param(repository_name, "repository_name"),
            job_name=check.str_param(job_name, "job_name"),
            solid_selection=check.opt_nullable_sequence_param(
                solid_selection, "solid_selection", str
            ),
            asset_selection=check.opt_nullable_sequence_param(
                asset_selection, "asset_selection", AssetKey
            ),
        )

    def to_graphql_input(self):
        return {
            "repositoryLocationName": self.location_name,
            "repositoryName": self.repository_name,
            "pipelineName": self.job_name,
            "solidSelection": self.solid_selection,
        }

    def with_solid_selection(self, solid_selection):
        check.invariant(
            self.solid_selection is None,
            "Can not invoke with_solid_selection when solid_selection={} is already set".format(
                solid_selection
            ),
        )
        return JobSubsetSelector(
            self.location_name, self.repository_name, self.job_name, solid_selection
        )


@whitelist_for_serdes
class JobSelector(
    NamedTuple(
        "_JobSelector", [("location_name", str), ("repository_name", str), ("job_name", str)]
    )
):
    def __new__(
        cls,
        location_name: str,
        repository_name: Optional[str] = None,
        job_name: Optional[str] = None,
    ):
        return super(JobSelector, cls).__new__(
            cls,
            location_name=check.str_param(location_name, "location_name"),
            repository_name=check.opt_str_param(
                repository_name,
                "repository_name",
                default=SINGLETON_REPOSITORY_NAME,
            ),
            job_name=check.str_param(
                job_name,
                "job_name",
                (
                    "Must provide job_name argument even though it is marked as optional in the "
                    "function signature. repository_name, a truly optional parameter, is before "
                    "that argument and actually optional. Use of keyword arguments is "
                    "recommended to avoid confusion."
                ),
            ),
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


@whitelist_for_serdes
class RepositorySelector(
    NamedTuple("_RepositorySelector", [("location_name", str), ("repository_name", str)])
):
    def __new__(cls, location_name: str, repository_name: str):
        return super(RepositorySelector, cls).__new__(
            cls,
            location_name=check.str_param(location_name, "location_name"),
            repository_name=check.str_param(repository_name, "repository_name"),
        )

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


class CodeLocationSelector(NamedTuple("_CodeLocationSelector", [("location_name", str)])):
    def __new__(cls, location_name: str):
        return super(CodeLocationSelector, cls).__new__(
            cls,
            location_name=check.str_param(location_name, "location_name"),
        )

    def to_repository_selector(self) -> RepositorySelector:
        return RepositorySelector(
            location_name=self.location_name, repository_name=SINGLETON_REPOSITORY_NAME
        )


class ScheduleSelector(
    NamedTuple(
        "_ScheduleSelector",
        [("location_name", str), ("repository_name", str), ("schedule_name", str)],
    )
):
    def __new__(cls, location_name: str, repository_name: str, schedule_name: str):
        return super(ScheduleSelector, cls).__new__(
            cls,
            location_name=check.str_param(location_name, "location_name"),
            repository_name=check.str_param(repository_name, "repository_name"),
            schedule_name=check.str_param(schedule_name, "schedule_name"),
        )

    def to_graphql_input(self):
        return {
            "repositoryLocationName": self.location_name,
            "repositoryName": self.repository_name,
            "scheduleName": self.schedule_name,
        }

    @staticmethod
    def from_graphql_input(graphql_data):
        return ScheduleSelector(
            location_name=graphql_data["repositoryLocationName"],
            repository_name=graphql_data["repositoryName"],
            schedule_name=graphql_data["scheduleName"],
        )


class ResourceSelector(NamedTuple):
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


class SensorSelector(
    NamedTuple(
        "_SensorSelector", [("location_name", str), ("repository_name", str), ("sensor_name", str)]
    )
):
    def __new__(cls, location_name: str, repository_name: str, sensor_name: str):
        return super(SensorSelector, cls).__new__(
            cls,
            location_name=check.str_param(location_name, "location_name"),
            repository_name=check.str_param(repository_name, "repository_name"),
            sensor_name=check.str_param(sensor_name, "sensor_name"),
        )

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


@whitelist_for_serdes
class InstigatorSelector(
    NamedTuple(
        "_InstigatorSelector", [("location_name", str), ("repository_name", str), ("name", str)]
    )
):
    def __new__(cls, location_name: str, repository_name: str, name: str):
        return super(InstigatorSelector, cls).__new__(
            cls,
            location_name=check.str_param(location_name, "location_name"),
            repository_name=check.str_param(repository_name, "repository_name"),
            name=check.str_param(name, "name"),
        )

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


class GraphSelector(
    NamedTuple(
        "_GraphSelector", [("location_name", str), ("repository_name", str), ("graph_name", str)]
    )
):
    """The information needed to resolve a graph within a host process."""

    def __new__(cls, location_name: str, repository_name: str, graph_name: str):
        return super(GraphSelector, cls).__new__(
            cls,
            location_name=check.str_param(location_name, "location_name"),
            repository_name=check.str_param(repository_name, "repository_name"),
            graph_name=check.str_param(graph_name, "graph_name"),
        )

    def to_graphql_input(self):
        return {
            "repositoryLocationName": self.location_name,
            "repositoryName": self.repository_name,
            "graphName": self.graph_name,
        }


@whitelist_for_serdes
class PartitionSetSelector(
    NamedTuple(
        "_PartitionSetSelector",
        [("location_name", str), ("repository_name", str), ("partition_set_name", str)],
    )
):
    """The information needed to resolve a partition set within a host process."""

    def __new__(cls, location_name: str, repository_name: str, partition_set_name: str):
        return super(PartitionSetSelector, cls).__new__(
            cls,
            location_name=check.str_param(location_name, "location_name"),
            repository_name=check.str_param(repository_name, "repository_name"),
            partition_set_name=check.str_param(partition_set_name, "partition_set_name"),
        )

    def to_graphql_input(self):
        return {
            "repositoryLocationName": self.location_name,
            "repositoryName": self.repository_name,
            "partitionSetName": self.partition_set_name,
        }
