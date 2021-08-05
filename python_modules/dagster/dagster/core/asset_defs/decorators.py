from typing import Any, Callable, Dict, Mapping, Optional, Set

from dagster.core.decorator_utils import get_function_params, get_valid_name_permutations
from dagster.core.definitions.decorators.op import _Op
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.input import In
from dagster.core.definitions.output import Out
from dagster.core.definitions.solid import SolidDefinition
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.utils.merger import merge_dicts

from .asset_in import AssetIn

NAMESPACE = "namespace"


def asset(
    name: Optional[str] = None,
    namespace: Optional[str] = None,
    ins: Optional[Mapping[str, AssetIn]] = None,
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
        ins (Optional[Mapping[str, AssetIn]]): A dictionary that maps input names to their metadata
            and namespaces.
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

    def inner(fn: Callable[..., Any]) -> SolidDefinition:
        return _Asset(
            name=name,
            namespace=namespace,
            ins=ins,
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
        ins: Optional[Mapping[str, AssetIn]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        description: Optional[str] = None,
        required_resource_keys: Optional[Set[str]] = None,
        io_manager_key: Optional[str] = None,
    ):
        self.name = name
        self.namespace = namespace
        self.ins = ins or {}
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
        input_param_names = [
            input_param.name for input_param in (params[1:] if is_context_provided else params)
        ]

        for in_key in self.ins.keys():
            if in_key not in input_param_names:
                raise DagsterInvalidDefinitionError(
                    f"Key '{in_key}' in provided ins dict does not correspond to any of the names "
                    "of the arguments to the decorated function"
                )

        ins: Dict[str, In] = {}
        for input_param_name in input_param_names:
            if input_param_name in self.ins:
                metadata = self.ins[input_param_name].metadata or {}
                namespace = self.ins[input_param_name].namespace
            else:
                metadata = {}
                namespace = None

            asset_key = AssetKey(
                list(filter(None, [namespace or self.namespace, input_param_name]))
            )

            ins[input_param_name] = In(
                metadata=metadata, root_manager_key="root_manager", asset_key=asset_key
            )

        out = Out(
            asset_key=AssetKey(list(filter(None, [self.namespace, asset_name]))),
            metadata=self.metadata or {},
            io_manager_key=self.io_manager_key,
        )
        return _Op(
            name=asset_name,
            description=self.description,
            ins=ins,
            out=out,
            required_resource_keys=self.required_resource_keys,
        )(fn)
