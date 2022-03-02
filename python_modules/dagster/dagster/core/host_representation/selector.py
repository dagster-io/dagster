from typing import List, NamedTuple, Optional

from dagster import check


class JobSelector(
    NamedTuple(
        "_PipelineSelector",
        [
            ("location_name", str),
            ("repository_name", str),
            ("job_name", str),
            ("op_selection", Optional[List[str]]),
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
        job_name: str,
        op_selection: Optional[List[str]],
    ):
        return super(JobSelector, cls).__new__(
            cls,
            location_name=check.str_param(location_name, "location_name"),
            repository_name=check.str_param(repository_name, "repository_name"),
            job_name=check.str_param(job_name, "job_name"),
            op_selection=check.opt_nullable_list_param(op_selection, "op_selection", str),
        )

    def to_graphql_input(self):
        return {
            "repositoryLocationName": self.location_name,
            "repositoryName": self.repository_name,
            "jobName": self.job_name,
            "opSelection": self.op_selection,
        }

    def with_op_selection(self, op_selection):
        check.invariant(
            self.op_selection is None,
            f"Can not invoke with_op_selection when op_selection={op_selection} is already set"
        )
        return JobSelector(
            self.location_name, self.repository_name, self.job_name, op_selection
        )


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


class InstigationSelector(
    NamedTuple(
        "_InstigationSelector", [("location_name", str), ("repository_name", str), ("name", str)]
    )
):
    def __new__(cls, location_name: str, repository_name: str, name: str):
        return super(InstigationSelector, cls).__new__(
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
        return InstigationSelector(
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
