import hashlib
import inspect
from abc import ABC, abstractmethod
from collections import namedtuple
from typing import TYPE_CHECKING, Optional

from dagster import check

if TYPE_CHECKING:
    from .solid_definition import SolidDefinition
    from .resource_definition import ResourceDefinition


class SolidVersionContext(
    namedtuple(
        "_SolidVersionContext",
        "solid_def solid_config",
    )
):
    """Version-specific solid context.
    Attributes:
        solid_def (SolidDefinition): The definition of the solid to compute a version for.
        solid_config (Any): The parsed config to be passed to the solid during execution.
    """

    def __new__(
        cls,
        solid_def,
        solid_config,
    ):
        if TYPE_CHECKING:
            solid_def = check.inst_param(
                solid_def, "solid_def", SolidDefinition  # pylint: disable=E0601
            )
        return super(SolidVersionContext, cls).__new__(
            cls, solid_def=solid_def, solid_config=solid_config
        )


class ResourceVersionContext(
    namedtuple(
        "_ResourceVersionContext",
        "resource_def resource_config",
    )
):
    """Version-specific resource context.

    Attributes:
        resource_def (ResourceDefinition): The definition of the resource whose version will be computed.
        resource_config (Any): The parsed config to be passed to the resource during execution.
    """

    def __new__(
        cls,
        resource_def,
        resource_config,
    ):
        if TYPE_CHECKING:
            resource_def = check.inst_param(
                resource_def, "resource_def", ResourceDefinition  # pylint: disable=E0601
            )
        return super(ResourceVersionContext, cls).__new__(
            cls, resource_def=resource_def, resource_config=resource_config
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
        self, context: ResourceVersionContext  # pylint: disable=unused-argument
    ) -> Optional[str]:
        return None


class SourceHashVersionStrategy(VersionStrategy):
    def _get_source_hash(self, fn):
        code_as_str = inspect.getsource(fn)
        return hashlib.sha1(code_as_str.encode("utf-8")).hexdigest()

    def get_solid_version(self, context: SolidVersionContext) -> str:
        return self._get_source_hash(context.solid_def.compute_fn.decorated_fn)

    def get_resource_version(self, context: ResourceVersionContext) -> Optional[str]:
        return self._get_source_hash(context.resource_def.resource_fn)
