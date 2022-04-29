from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .graph_definition import GraphDefinition
    from .job_definition import JobDefinition


class OriginDefinition:
    def upstream_def(self) -> Optional["JobDefinition", "GraphDefinition"]:
        pass


class FromGraphDefinition(OriginDefinition):
    """Represents a call to `to_job`."""

    def __init__(self, graph_def, provided_resource_keys):
        self._graph_def = graph_def
        self._provided_resource_keys = provided_resource_keys

    @property
    def upstream_def(self):
        return self._graph_def

    @property
    def provided_resource_keys(self):
        return self._provided_resource_keys


class FromJobDecorator(OriginDefinition):
    """Represents a job created using the @job decorator."""

    def __init__(self, origin_def, provided_resource_keys):
        self._origin_def = origin_def
        self._provided_resource_keys


class FromGraphRepositoryCoercion(OriginDefinition):
    def __init__(self, graph_def, provided_resource_keys):
        self._origin_def = graph_def
        self._provided_resource_keys = provided_resource_keys

    @property
    def upstream_def(self):
        return self._graph_def

    @property
    def provided_resource_keys(self):
        return self._provided_resource_keys
