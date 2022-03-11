import hashlib
import inspect
from typing import TYPE_CHECKING, Any, NamedTuple, Optional

if TYPE_CHECKING:
    from .op_definition import OpDefinition
    from .resource_definition import ResourceDefinition
    from .solid_definition import SolidDefinition


class OpVersionContext(NamedTuple):
    """Provides execution-time information for computing the version for an op.
    Attributes:
        op_def (OpDefinition): The definition of the op to compute a version for.
        op_config (Any): The parsed config to be passed to the op during execution.
    """

    op_def: "OpDefinition"
    op_config: Any

    @property
    def solid_def(self) -> "SolidDefinition":
        return self.op_def

    @property
    def solid_config(self) -> Any:
        return self.op_config


SolidVersionContext = OpVersionContext


class ResourceVersionContext(NamedTuple):
    """Version-specific resource context.

    Attributes:
        resource_def (ResourceDefinition): The definition of the resource whose version will be computed.
        resource_config (Any): The parsed config to be passed to the resource during execution.
    """

    resource_def: "ResourceDefinition"
    resource_config: Any


class VersionStrategy:
    """Abstract class for defining a strategy to version solids and resources.

    When subclassing, `get_solid_version` must be implemented, and `get_resource_version` can be
    optionally implemented.

    `get_solid_version` should ingest a SolidVersionContext, and `get_resource_version` should ingest a
    ResourceVersionContext. From that,  each synthesize a unique string called a `version`, which will
    be tagged to outputs of that solid in the pipeline. Providing a `VersionStrategy` instance to a
    job will enable memoization on that job, such that only steps whose outputs do not have an
    up-to-date version will run.
    """

    def get_solid_version(self, context: SolidVersionContext) -> str:
        pass

    def get_op_version(self, context: OpVersionContext) -> str:
        return self.get_solid_version(context)

    def get_resource_version(
        self, context: ResourceVersionContext  # pylint: disable=unused-argument
    ) -> Optional[str]:
        return None


class SourceHashVersionStrategy(VersionStrategy):
    def _get_source_hash(self, fn):
        code_as_str = inspect.getsource(fn)
        return hashlib.sha1(code_as_str.encode("utf-8")).hexdigest()

    def get_op_version(self, context: OpVersionContext) -> str:
        compute_fn = context.op_def.compute_fn
        if callable(compute_fn):
            return self._get_source_hash(compute_fn)
        else:
            return self._get_source_hash(compute_fn.decorated_fn)

    def get_resource_version(self, context: ResourceVersionContext) -> Optional[str]:
        return self._get_source_hash(context.resource_def.resource_fn)
