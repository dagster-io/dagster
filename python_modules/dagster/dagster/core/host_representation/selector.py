from collections import namedtuple

from dagster import check


class PipelineSelector(
    namedtuple("_PipelineSelector", "location_name repository_name pipeline_name solid_selection")
):
    """
    The information needed to resolve a pipeline within a host process.
    """

    def __new__(
        cls,
        location_name,
        repository_name,
        pipeline_name,
        solid_selection,
    ):
        return super(PipelineSelector, cls).__new__(
            cls,
            location_name=check.str_param(location_name, "location_name"),
            repository_name=check.str_param(repository_name, "repository_name"),
            pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
            solid_selection=check.opt_nullable_list_param(solid_selection, "solid_selection", str),
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


class RepositorySelector(namedtuple("_RepositorySelector", "location_name repository_name")):
    def __new__(cls, location_name, repository_name):
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
    namedtuple("_ScheduleSelector", "location_name repository_name schedule_name")
):
    def __new__(cls, location_name, repository_name, schedule_name):
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


class SensorSelector(namedtuple("_SensorSelector", "location_name repository_name sensor_name")):
    def __new__(cls, location_name, repository_name, sensor_name):
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


class InstigationSelector(namedtuple("_InstigationSelector", "location_name repository_name name")):
    def __new__(cls, location_name, repository_name, name):
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


class GraphSelector(namedtuple("_GraphSelector", "location_name repository_name graph_name")):
    """
    The information needed to resolve a graph within a host process.
    """

    def __new__(
        cls,
        location_name,
        repository_name,
        graph_name,
    ):
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
