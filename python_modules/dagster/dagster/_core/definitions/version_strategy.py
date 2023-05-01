import hashlib
import inspect
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, NamedTuple, Optional

from dagster._annotations import public

if TYPE_CHECKING:
    from .op_definition import OpDefinition
    from .resource_definition import ResourceDefinition


class OpVersionContext(NamedTuple):
    """Provides execution-time information for computing the version for an op.

    Attributes:
        op_def (OpDefinition): The definition of the op to compute a version for.
        op_config (Any): The parsed config to be passed to the op during execution.
    """

    op_def: "OpDefinition"
    op_config: Any


class ResourceVersionContext(NamedTuple):
    """Provides execution-time information for computing the version for a resource.

    Attributes:
        resource_def (ResourceDefinition): The definition of the resource whose version will be computed.
        resource_config (Any): The parsed config to be passed to the resource during execution.
    """

    resource_def: "ResourceDefinition"
    resource_config: Any


class VersionStrategy(ABC):
    """Abstract class for defining a strategy to version ops and resources.

    When subclassing, `get_op_version` must be implemented, and
    `get_resource_version` can be optionally implemented.

    `get_op_version` should ingest an OpVersionContext, and `get_resource_version` should ingest a
    ResourceVersionContext. From that,  each synthesize a unique string called
    a `version`, which will
    be tagged to outputs of that op in the job. Providing a
    `VersionStrategy` instance to a
    job will enable memoization on that job, such that only steps whose
    outputs do not have an up-to-date version will run.
    """

    @public
    @abstractmethod
    def get_op_version(self, context: OpVersionContext) -> str:
        raise NotImplementedError()

    @public
    def get_resource_version(self, context: ResourceVersionContext) -> Optional[str]:
        return None


class SourceHashVersionStrategy(VersionStrategy):
    """VersionStrategy that checks for changes to the source code of ops and resources.

    Only checks for changes within the immediate body of the op/resource's
    decorated function (or compute function, if the op/resource was
    constructed directly from a definition).
    """

    def _get_source_hash(self, fn):
        code_as_str = inspect.getsource(fn)
        return hashlib.sha1(code_as_str.encode("utf-8")).hexdigest()

    @public
    def get_op_version(self, context: OpVersionContext) -> str:
        compute_fn = context.op_def.compute_fn
        if callable(compute_fn):
            return self._get_source_hash(compute_fn)
        else:
            return self._get_source_hash(compute_fn.decorated_fn)

    @public
    def get_resource_version(self, context: ResourceVersionContext) -> Optional[str]:
        return self._get_source_hash(context.resource_def.resource_fn)
