from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional
from collections import namedtuple
from dagster import check

if TYPE_CHECKING:
    from .solid import SolidDefinition
    from .resource import ResourceDefinition

class SolidVersionContext(
    namedtuple(
        "SolidVersionContext",
        "solid_def solid_config",
    )
    ):
    """Version-specific solid context.
    Attributes:
        solid_def (SolidDefinition): The definition of the versioned solid
        solid_config (Any): The parsed config received by the versioned solid
    """

    def __new__(
            cls,
            solid_def,
            solid_config,
    ):
        if TYPE_CHECKING:
            solid_def = check.inst_param(solid_def, "solid_def", SolidDefinition)
        return super(SolidVersionContext, cls).__new__(
            cls,
            solid_def=solid_def,
            solid_config=solid_config
        )

class ResourceVersionContext(
    namedtuple(
        "SolidVersionContext",
        "solid_def solid_config",
    )
    ):
    """Version-specific solid context.
    Attributes:
        resource_def (ResourceDefinition): The definition of the versioned resource
        resource_config (Any): The parsed config received by the versioned resource
    """

    def __new__(
            cls,
            resource_def,
            resource_config,
    ):
        if TYPE_CHECKING:
            resource_def = check.inst_param(resource_def, "resource_def", ResourceDefinition)
        return super(ResourceVersionContext, cls).__new__(
            cls,
            solid_def=resource_def,
            solid_config=resource_config
        )

class VersionStrategy(ABC):
    """Abstract class for defining a strategy to version solids and resources.

    When subclassing, `get_solid_version` must be implemented, and `get_resource_version` can be
    optionally implemented.

    `get_solid_version` should ingest a SolidVersionContext, and `get_resource_version` should ingest a
    ResourceVersionContext. From that,  each synthesize a unique string called a `version`, which will
    be tagged to outputs of that solid in the pipeline. Providing a `VersionStrategy` instance to a
    job will enable memoization on that job, such that only steps whose outputs do not have an
    up-to-date version will run.
    """

    @abstractmethod
    def get_solid_version(self, context: SolidVersionContext) -> str:
        pass

    def get_resource_version(
        self, context: ResourceVersionContext # pylint: disable=unused-argument
    ) -> Optional[str]:
        return None
