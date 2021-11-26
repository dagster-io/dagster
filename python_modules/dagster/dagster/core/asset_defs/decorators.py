from typing import Any, Callable, Dict, Mapping, Optional, Set

from dagster import check
from dagster.builtins import Nothing
from dagster.core.decorator_utils import get_function_params, get_valid_name_permutations
from dagster.core.definitions.decorators.op import _Op
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.input import In
from dagster.core.definitions.output import Out
from dagster.core.definitions.partition import PartitionsDefinition
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.types.dagster_type import DagsterType
from dagster.utils.backcompat import experimental_decorator

from .asset import AssetsDefinition
from .asset_in import AssetIn
from .partition_mapping import PartitionMapping


@experimental_decorator
def asset(
    name: Optional[str] = None,
    namespace: Optional[str] = None,
    ins: Optional[Mapping[str, AssetIn]] = None,
    non_argument_deps: Optional[Set[AssetKey]] = None,
    metadata: Optional[Mapping[str, Any]] = None,
    description: Optional[str] = None,
    required_resource_keys: Optional[Set[str]] = None,
    io_manager_key: Optional[str] = None,
    compute_kind: Optional[str] = None,
    dagster_type: Optional[DagsterType] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    partition_mappings: Optional[Mapping[str, PartitionMapping]] = None,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    """Create a definition for how to compute an asset.

    A software-defined asset is the combination of:
    1. An asset key, e.g. the name of a table.
    2. A function, which can be run to compute the contents of the asset.
    3. A set of upstream assets that are provided as inputs to the function when computing the asset.

    Unlike an op, whose dependencies are determined by the graph it lives inside, an asset knows
    about the upstream assets it depends on. The upstream assets are inferred from the arguments
    to the decorated function. The name of the argument designates the name of the upstream asset.

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
        compute_kind (Optional[str]): A string to represent the kind of computation that produces
            the asset, e.g. "dbt" or "spark". It will be displayed in Dagit as a badge on the asset.
        dagster_type (Optional[DagsterType]): Allows specifying type validation functions that
            will be executed on the output of the decorated function after it runs.
        partitions_def (Optional[PartitionsDefiniition]): Defines the set of partition keys that
            compose the asset.
        partition_mappings (Optional[Mapping[str, PartitionMapping]]): Defines how to map partition
            keys for this asset to partition keys of upstream assets. Each key in the dictionary
            correponds to one of the input assets, and each value is a PartitionMapping.
            If no entry is provided for a particular asset dependency, the partition mapping defaults
            to the default partition mapping for the partitions definition, which is typically maps
            partition keys to the same partition keys in upstream assets.

    Examples:

        .. code-block:: python

            @asset
            def my_asset(my_upstream_asset: int) -> int:
                return my_upstream_asset + 1
    """
    if callable(name):
        return _Asset()(name)

    def inner(fn: Callable[..., Any]) -> AssetsDefinition:
        return _Asset(
            name=name,
            namespace=namespace,
            ins=ins,
            non_argument_deps=non_argument_deps,
            metadata=metadata,
            description=description,
            required_resource_keys=required_resource_keys,
            io_manager_key=io_manager_key,
            compute_kind=check.opt_str_param(compute_kind, "compute_kind"),
            dagster_type=dagster_type,
            partitions_def=partitions_def,
            partition_mappings=partition_mappings,
        )(fn)

    return inner


class _Asset:
    def __init__(
        self,
        name: Optional[str] = None,
        namespace: Optional[str] = None,
        ins: Optional[Mapping[str, AssetIn]] = None,
        non_argument_deps: Optional[Set[AssetKey]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        description: Optional[str] = None,
        required_resource_keys: Optional[Set[str]] = None,
        io_manager_key: Optional[str] = None,
        compute_kind: Optional[str] = None,
        dagster_type: Optional[DagsterType] = None,
        partitions_def: Optional[PartitionsDefinition] = None,
        partition_mappings: Optional[Mapping[str, PartitionMapping]] = None,
    ):
        self.name = name
        self.namespace = namespace
        self.ins = ins or {}
        self.non_argument_deps = non_argument_deps
        self.metadata = metadata
        self.description = description
        self.required_resource_keys = required_resource_keys
        self.io_manager_key = io_manager_key
        self.compute_kind = compute_kind
        self.dagster_type = dagster_type
        self.partitions_def = partitions_def
        self.partition_mappings = partition_mappings

    def __call__(self, fn: Callable) -> AssetsDefinition:
        asset_name = self.name or fn.__name__

        ins_by_input_names: Mapping[str, In] = build_asset_ins(
            fn, self.namespace, self.ins or {}, self.non_argument_deps
        )

        out = Out(
            asset_key=AssetKey(list(filter(None, [self.namespace, asset_name]))),
            metadata=self.metadata or {},
            io_manager_key=self.io_manager_key,
            dagster_type=self.dagster_type,
        )
        op = _Op(
            name=asset_name,
            description=self.description,
            ins={
                input_name: in_def for input_name, in_def in ins_by_input_names.items()
            },  # convert Mapping object to dict
            out=out,
            required_resource_keys=self.required_resource_keys,
            tags={"kind": self.compute_kind} if self.compute_kind else None,
        )(fn)

        out_asset_key = AssetKey(list(filter(None, [self.namespace, asset_name])))

        return AssetsDefinition(
            input_names_by_asset_key={
                in_def.asset_key: input_name for input_name, in_def in ins_by_input_names.items()
            },
            output_names_by_asset_key={out_asset_key: "result"},
            op=op,
            partitions_def=self.partitions_def,
            partition_mappings={
                ins_by_input_names[input_name].asset_key: partition_mapping
                for input_name, partition_mapping in self.partition_mappings.items()
            }
            if self.partition_mappings
            else None,
        )


@experimental_decorator
def multi_asset(
    outs: Dict[str, Out],
    name: Optional[str] = None,
    ins: Optional[Mapping[str, AssetIn]] = None,
    non_argument_deps: Optional[Set[AssetKey]] = None,
    description: Optional[str] = None,
    required_resource_keys: Optional[Set[str]] = None,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    """Create a combined definition of multiple assets that are computed using the same op and same
    upstream assets.

    Each argument to the decorated function references an upstream asset that this asset depends on.
    The name of the argument designates the name of the upstream asset.

    Args:
        name (Optional[str]): The name of the op.
        outs: (Optional[Dict[str, Out]]): The Outs representing the produced assets.
        ins (Optional[Mapping[str, AssetIn]]): A dictionary that maps input names to their metadata
            and namespaces.
        required_resource_keys (Optional[Set[str]]): Set of resource handles required by the op.
        io_manager_key (Optional[str]): The resource key of the IOManager used for storing the
            output of the op as an asset, and for loading it in downstream ops
            (default: "io_manager").
    """

    def inner(fn: Callable[..., Any]) -> AssetsDefinition:
        asset_name = name or fn.__name__
        ins_by_input_names: Mapping[str, In] = build_asset_ins(
            fn, None, ins or {}, non_argument_deps
        )

        op = _Op(
            name=asset_name,
            description=description,
            ins={
                input_name: in_def for input_name, in_def in ins_by_input_names.items()
            },  # convert Mapping object to dict
            out=outs,
            required_resource_keys=required_resource_keys,
        )(fn)

        return AssetsDefinition(
            input_names_by_asset_key={
                in_def.asset_key: input_name for input_name, in_def in ins_by_input_names.items()
            },
            output_names_by_asset_key={AssetKey([name]): name for name in outs.keys()},
            op=op,
        )

    return inner


def build_asset_ins(
    fn: Callable,
    asset_namespace: Optional[str],
    asset_ins: Mapping[str, AssetIn],
    non_argument_deps: Optional[Set[AssetKey]],
) -> Mapping[str, In]:

    non_argument_deps = check.opt_set_param(non_argument_deps, "non_argument_deps", AssetKey)

    params = get_function_params(fn)
    is_context_provided = len(params) > 0 and params[0].name in get_valid_name_permutations(
        "context"
    )
    input_param_names = [
        input_param.name for input_param in (params[1:] if is_context_provided else params)
    ]

    all_input_names = set(input_param_names) | asset_ins.keys()

    for in_key in asset_ins.keys():
        if in_key not in input_param_names:
            raise DagsterInvalidDefinitionError(
                f"Key '{in_key}' in provided ins dict does not correspond to any of the names "
                "of the arguments to the decorated function"
            )

    ins: Dict[str, In] = {}
    for input_name in all_input_names:
        asset_key = None

        if input_name in asset_ins:
            asset_key = asset_ins[input_name].asset_key
            metadata = asset_ins[input_name].metadata or {}
            namespace = asset_ins[input_name].namespace
            dagster_type = None
        else:
            metadata = {}
            namespace = None
            dagster_type = None

        asset_key = asset_key or AssetKey(
            list(filter(None, [namespace or asset_namespace, input_name]))
        )

        ins[input_name] = In(
            metadata=metadata,
            root_manager_key="root_manager",
            asset_key=asset_key,
            dagster_type=dagster_type,
        )

    for asset_key in non_argument_deps:
        stringified_asset_key = asset_key.to_string(legacy=True)
        if stringified_asset_key:
            ins[str(stringified_asset_key)] = In(dagster_type=Nothing, asset_key=asset_key)

    return ins
