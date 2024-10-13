from abc import ABC, abstractmethod

from dagster import _check as check
from dagster._core.definitions.definitions_class import Definitions
from dagster._model import DagsterModel
from dagster._utils.source_position import HasSourcePositionAndKeyPath


class DagsterBuildDefinitionsFromConfigError(Exception):
    pass


class Blueprint(DagsterModel, ABC, HasSourcePositionAndKeyPath):
    """A blob of user-provided, structured metadata that specifies a set of Dagster definitions,
    like assets, jobs, schedules, sensors, resources, or asset checks.

    Base class for user-provided types. Users override and provide:
    - The set of fields
    - A build_defs implementation that generates Dagster Definitions from field values
    """

    @abstractmethod
    def build_defs(self) -> Definitions:
        raise NotImplementedError()

    def build_defs_add_context_to_errors(self) -> Definitions:
        try:
            return check.inst(self.build_defs(), Definitions)
        except Exception as e:
            source_pos = None
            if (
                self._source_position_and_key_path is not None
                and self._source_position_and_key_path.source_position is not None
            ):
                source_pos = self._source_position_and_key_path.source_position

            cls_name = self.__class__.__name__
            if source_pos is None:
                raise DagsterBuildDefinitionsFromConfigError(
                    f"Error when building definitions from config with type {cls_name}"
                )
            raise DagsterBuildDefinitionsFromConfigError(
                f"Error when building definitions from config with type {cls_name} at {source_pos}"
            ) from e
