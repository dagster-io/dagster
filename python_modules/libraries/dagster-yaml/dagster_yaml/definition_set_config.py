from abc import ABC, abstractmethod

from dagster import Definitions
from dagster._model import DagsterModel

from dagster_yaml.yaml.object_mapping import HasObjectMappingContext


class DagsterBuildDefinitionsFromConfigError(Exception):
    pass


class DefinitionSetConfig(DagsterModel, ABC, HasObjectMappingContext):
    """A blob of user-provided, structured metadata that specifies a set of Dagster definitions,
    like assets, jobs, schedules, sensors, resources, or asset checks.

    Base class for user-provided definition config types. Users override and provide:
    - A set of fields that define what config is expected
    - A build_defs implementation that generates Dagster definitions from those config fields
    """

    @abstractmethod
    def build_defs(self) -> Definitions:
        raise NotImplementedError()

    def build_defs_add_context_to_errors(self) -> Definitions:
        try:
            return self.build_defs()
        except Exception as e:
            source_pos = None
            if (
                self._object_mapping_context is not None
                and self._object_mapping_context.source_position is not None
            ):
                source_pos = self._object_mapping_context.source_position

            if source_pos is None:
                raise e
            raise DagsterBuildDefinitionsFromConfigError(
                f"Error when building definitions from config at {source_pos}"
            ) from e
