from typing import NamedTuple, Optional, Sequence

import dagster._check as check
from dagster._core.definitions.events import AssetKey
from dagster._serdes import create_snapshot_id, whitelist_for_serdes


class PipelineSelector(
    NamedTuple(
        "_PipelineSelector",
        [
            ("location_name", str),
            ("repository_name", str),
            ("pipeline_name", str),
            ("solid_selection", Optional[Sequence[str]]),
            ("asset_selection", Optional[Sequence[AssetKey]]),
        ],
    )
):
    """
    The information needed to resolve a pipeline within a host process.
    """

    def __new__(
        cls,
        location_name: str,
        repository_name: str,
        pipeline_name: str,
        solid_selection: Optional[Sequence[str]],
        asset_selection: Optional[Sequence[AssetKey]] = None,
    ):
        return super(PipelineSelector, cls).__new__(
            cls,
            location_name=check.str_param(location_name, "location_name"),
            repository_name=check.str_param(repository_name, "repository_name"),
            pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
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
            "pipelineName": self.pipeline_name,
            "solidSelection": self.solid_selection,
        }

    def with_solid_selection(self, solid_selection):
        check.invariant(
            self.solid_selection is None,
            "Can not invoke with_solid_selection when solid_selection={} is already set".format(
                solid_selection
            ),
        )
        return PipelineSelector(
            self.location_name, self.repository_name, self.pipeline_name, solid_selection
        )


@whitelist_for_serdes
class JobSelector(
    NamedTuple(
        "_JobSelector", [("location_name", str), ("repository_name", str), ("job_name", str)]
    )
):
    def __new__(cls, location_name: str, repository_name: str, job_name: str):
        return super(JobSelector, cls).__new__(
            cls,
            location_name=check.str_param(location_name, "location_name"),
            repository_name=check.str_param(repository_name, "repository_name"),
            job_name=check.str_param(job_name, "job_name"),
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
    """
    The information needed to resolve a graph within a host process.
    """

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
    """
    The information needed to resolve a partition set within a host process.
    """

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
