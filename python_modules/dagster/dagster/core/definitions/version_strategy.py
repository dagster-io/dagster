from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .solid import SolidDefinition
    from .resource import ResourceDefinition


class VersionStrategy(ABC):
    """Abstract class for defining a strategy to version solids and resources.

    When subclassing, `get_solid_version` must be implemented, and `get_resource_version` can be
    optionally implemented.

    `get_solid_version` should ingest a SolidDefinition, and `get_resource_version` should ingest a
    ResourceDefinition. From that,  each synthesize a unique string called a `version`, which will
    be tagged to outputs of that solid in the pipeline. Providing a `VersionStrategy` instance to a
    job will enable memoization on that job, such that only steps whose outputs do not have an
    up-to-date version will run.
    """

    @abstractmethod
    def get_solid_version(self, solid_def: "SolidDefinition") -> str:
        pass

    def get_resource_version(
        self, resource_def: "ResourceDefinition"  # pylint: disable=unused-argument
    ) -> Optional[str]:
        return None
