from typing import Any, Callable, Mapping, Optional, Sequence, Set

from dagster.core.decorator_utils import get_function_params, get_valid_name_permutations
from dagster.core.definitions.decorators.op import _Op
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.input import In
from dagster.core.definitions.output import Out
from dagster.core.definitions.solid import SolidDefinition
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.utils.merger import merge_dicts

LOGICAL_ASSET_KEY = "logical_asset_key"
NAMESPACE = "namespace"


def asset(
    name: Optional[str] = None,
    namespace: Optional[str] = None,
    input_namespaces: Optional[Mapping[str, str]] = None,
    metadata: Optional[Mapping[str, Any]] = None,
    description: Optional[str] = None,
    required_resource_keys: Optional[Set[str]] = None,
    io_manager_key: Optional[str] = None,
) -> Callable[[Callable[..., Any]], SolidDefinition]:
    """Create an op that computes an asset.

    Each argument to the decorated function references an upstream asset that this asset depends on.
    The name of the argument designates the name of the upstream asset.

    Args:
        name (Optional[str]): The name of the asset.  If not provided, defaults to the name of the
            decorated function.
        namespace (Optional[str]): The namespace that the asset resides in.  The namespace + the
            name forms the asset key.
        input_namespaces (Optional[Mapping[str, str]]): A dictionary that maps input names to the
            asset namespaces where they reside.
        metadata (Optional[Dict[str, Any]]): A dict of metadata entries for the asset.
        required_resource_keys (Optional[Set[str]]): Set of resource handles required by the op.
        io_manager_key (Optional[str]): The resource key of the IOManager used for storing the
            output of the op as an asset, and for loading it in downstream ops
            (default: "io_manager").
    """
    if callable(name):
        return _Asset()(name)

    if metadata:
        if NAMESPACE in metadata:
            raise DagsterInvalidDefinitionError(
                f"'{NAMESPACE}' is a reserved metadata key, but was included in the asset metadata"
            )

        if LOGICAL_ASSET_KEY in metadata:
            raise DagsterInvalidDefinitionError(
                f"'{LOGICAL_ASSET_KEY}' is a reserved metadata key, but was included in the asset metadata"
            )

    def inner(fn: Callable[..., Any]) -> SolidDefinition:
        return _Asset(
            name=name,
            namespace=namespace,
            input_namespaces=input_namespaces,
            metadata=metadata,
            description=description,
            required_resource_keys=required_resource_keys,
            io_manager_key=io_manager_key,
        )(fn)

    return inner


class _Asset:
    def __init__(
        self,
        name: Optional[str] = None,
        namespace: Optional[str] = None,
        input_namespaces: Mapping[str, Sequence] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        description: Optional[str] = None,
        required_resource_keys: Optional[Set[str]] = None,
        io_manager_key: Optional[str] = None,
    ):
        self.name = name
        self.namespace = namespace
        self.input_namespaces = input_namespaces or {}
        self.metadata = metadata
        self.description = description
        self.required_resource_keys = required_resource_keys
        self.io_manager_key = io_manager_key

    def __call__(self, fn: Callable):
        asset_name = self.name or fn.__name__
        params = get_function_params(fn)
        is_context_provided = len(params) > 0 and params[0].name in get_valid_name_permutations(
            "context"
        )
        input_params = params[1:] if is_context_provided else params

        ins = {
            input_param.name: In(
                metadata={
                    LOGICAL_ASSET_KEY: AssetKey(
                        tuple(
                            filter(
                                None,
                                [
                                    self.input_namespaces.get(input_param.name, self.namespace),
                                    input_param.name,
                                ],
                            )
                        )
                    ),
                },
                root_manager_key="root_manager",
            )
            for input_param in input_params
        }
        out = Out(
            metadata=merge_dicts(
                {LOGICAL_ASSET_KEY: AssetKey(tuple(filter(None, [self.namespace, asset_name])))},
                self.metadata or {},
            ),
            io_manager_key=self.io_manager_key,
        )
        return _Op(
            name=asset_name,
            description=self.description,
            ins=ins,
            out=out,
            required_resource_keys=self.required_resource_keys,
        )(fn)
