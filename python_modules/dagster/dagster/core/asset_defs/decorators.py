import textwrap
from typing import Any, Callable, Dict, Mapping, Optional, Set

from dagster.core.decorator_utils import get_function_params, get_valid_name_permutations
from dagster.core.definitions.decorators.op import _Op
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.input import In
from dagster.core.definitions.output import Out
from dagster.core.definitions.solid import SolidDefinition
from dagster.core.errors import DagsterInvalidDefinitionError

from .asset_in import AssetIn
from .column import Column


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

        out = Out(
            asset_key=AssetKey(list(filter(None, [self.namespace, asset_name]))),
            metadata=self.metadata or {},
            io_manager_key=self.io_manager_key,
        )
        return _Op(
            name=asset_name,
            description=self.description,
            ins=build_asset_ins(fn, self.namespace, self.ins),
            out=out,
            required_resource_keys=self.required_resource_keys,
        )(fn)


def multi_asset(
    name: Optional[str] = None,
    outs: Optional[Dict[str, Out]] = None,
    ins: Optional[Mapping[str, AssetIn]] = None,
    description: Optional[str] = None,
    required_resource_keys: Optional[Set[str]] = None,
) -> Callable[[Callable[..., Any]], SolidDefinition]:
    if callable(name):
        return _Asset()(name)

    def inner(fn: Callable[..., Any]) -> SolidDefinition:
        return _MultiAsset(
            name=name,
            outs=outs,
            ins=ins,
            description=description,
            required_resource_keys=required_resource_keys,
        )(fn)

    return inner


class _MultiAsset:
    def __init__(
        self,
        name: Optional[str] = None,
        outs: Optional[Dict[str, Out]] = None,
        ins: Optional[Mapping[str, AssetIn]] = None,
        description: Optional[str] = None,
        required_resource_keys: Optional[Set[str]] = None,
        io_manager_key: Optional[str] = None,
    ):
        self.name = name
        self.ins = ins or {}
        self.outs = outs
        self.description = description
        self.required_resource_keys = required_resource_keys
        self.io_manager_key = io_manager_key

    def __call__(self, fn: Callable):
        asset_name = self.name or fn.__name__

        return _Op(
            name=asset_name,
            description=self.description,
            ins=build_asset_ins(fn, None, self.ins),
            out=self.outs,
            required_resource_keys=self.required_resource_keys,
        )(fn)


def build_asset_ins(
    fn: Callable, asset_namespace: Optional[str], asset_ins: Mapping[str, AssetIn]
) -> Dict[str, In]:
    params = get_function_params(fn)
    is_context_provided = len(params) > 0 and params[0].name in get_valid_name_permutations(
        "context"
    )
    input_param_names = [
        input_param.name for input_param in (params[1:] if is_context_provided else params)
    ]

    for in_key in asset_ins.keys():
        if in_key not in input_param_names:
            raise DagsterInvalidDefinitionError(
                f"Key '{in_key}' in provided ins dict does not correspond to any of the names "
                "of the arguments to the decorated function"
            )

    ins: Dict[str, In] = {}
    for input_param_name in input_param_names:
        if input_param_name in asset_ins:
            metadata = asset_ins[input_param_name].metadata or {}
            namespace = asset_ins[input_param_name].namespace
        else:
            metadata = {}
            namespace = None

        asset_key = AssetKey(list(filter(None, [namespace or asset_namespace, input_param_name])))

        ins[input_param_name] = In(
            metadata=metadata, root_manager_key="root_manager", asset_key=asset_key
        )

    return ins


def table(
    name: Optional[str] = None,
    namespace: Optional[str] = None,
    ins: Optional[Mapping[str, AssetIn]] = None,
    metadata: Optional[Mapping[str, Any]] = None,
    description: Optional[str] = None,
    required_resource_keys: Optional[Set[str]] = None,
    io_manager_key: Optional[str] = None,
    columns: Optional[Mapping[str, Column]] = None,
) -> Callable[[Callable[..., Any]], SolidDefinition]:
    """Create an op that computes a table asset.

    Each argument to the decorated function references an upstream asset that this table depends on.
    The name of the argument designates the name of the upstream asset.

    Args:
        name (Optional[str]): The name of the table.  If not provided, defaults to the name of the
            decorated function.
        namespace (Optional[str]): The namespace that the table resides in.  The namespace + the
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

    def inner(fn: Callable[..., Any]) -> SolidDefinition:
        final_description = textwrap.dedent(description or fn.__doc__ or "") + columns_to_markdown(
            columns
        )
        return _Asset(
            name=name,
            namespace=namespace,
            ins=ins,
            metadata=metadata,
            description=final_description,
            required_resource_keys=required_resource_keys,
            io_manager_key=io_manager_key,
        )(fn)

    return inner


def columns_to_markdown(columns: Optional[Mapping[str, Column]]) -> str:
    if not columns:
        return ""

    return (
        textwrap.dedent(
            """
        | Name | Type | Description |
        | - | - | - |
    """
        )
        + "\n".join(
            [
                f"| {name} | {column.type_name} | {column.description} |"
                for name, column in columns.items()
            ]
        )
    )
