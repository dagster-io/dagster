import warnings
from typing import (
    AbstractSet,
    Any,
    Callable,
    Dict,
    Mapping,
    Optional,
    Sequence,
    Set,
    Union,
    cast,
    overload,
)

from dagster import check
from dagster.builtins import Nothing
from dagster.config import Field
from dagster.core.decorator_utils import get_function_params, get_valid_name_permutations
from dagster.core.definitions.decorators.op import _Op
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.input import In
from dagster.core.definitions.output import Out
from dagster.core.definitions.partition import PartitionsDefinition
from dagster.core.definitions.utils import NoValueSentinel
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.types.dagster_type import DagsterType
from dagster.utils.backcompat import ExperimentalWarning, experimental_decorator

from .asset import AssetsDefinition
from .asset_in import AssetIn
from .partition_mapping import PartitionMapping

ASSET_DEPENDENCY_METADATA_KEY = ".dagster/asset_deps"


@overload
def asset(
    name: Callable[..., Any],
) -> AssetsDefinition:
    ...


@overload
def asset(
    name: Optional[str] = ...,
    namespace: Optional[Sequence[str]] = ...,
    ins: Optional[Mapping[str, AssetIn]] = ...,
    non_argument_deps: Optional[Set[AssetKey]] = ...,
    metadata: Optional[Mapping[str, Any]] = ...,
    description: Optional[str] = ...,
    required_resource_keys: Optional[Set[str]] = ...,
    io_manager_key: Optional[str] = ...,
    compute_kind: Optional[str] = ...,
    dagster_type: Optional[DagsterType] = ...,
    partitions_def: Optional[PartitionsDefinition] = ...,
    partition_mappings: Optional[Mapping[str, PartitionMapping]] = ...,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    ...


@experimental_decorator
def asset(
    name: Optional[Union[Callable[..., Any], Optional[str]]] = None,
    namespace: Optional[Sequence[str]] = None,
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
) -> Union[AssetsDefinition, Callable[[Callable[..., Any]], AssetsDefinition]]:
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
        namespace (Optional[Sequence[str]]): The namespace that the asset resides in.  The namespace + the
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
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
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
            name=cast(Optional[str], name),  # (mypy bug that it can't infer name is Optional[str])
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
        namespace: Optional[Sequence[str]] = None,
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
        # if user inputs a single string, coerce to list
        self.namespace = [namespace] if isinstance(namespace, str) else namespace
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

        asset_ins = build_asset_ins(fn, self.namespace, self.ins or {}, self.non_argument_deps)

        partition_fn: Optional[Callable] = None
        if self.partitions_def:

            def partition_fn(context):  # pylint: disable=function-redefined
                return [context.partition_key]

        out_asset_key = AssetKey(list(filter(None, [*(self.namespace or []), asset_name])))
        out = Out(
            asset_key=out_asset_key,
            metadata=self.metadata or {},
            io_manager_key=self.io_manager_key,
            dagster_type=self.dagster_type if self.dagster_type else NoValueSentinel,
            asset_partitions_def=self.partitions_def,
            asset_partitions=partition_fn,
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=ExperimentalWarning)
            op = _Op(
                name="__".join(out_asset_key.path),
                description=self.description,
                ins=asset_ins,
                out=out,
                required_resource_keys=self.required_resource_keys,
                tags={"kind": self.compute_kind} if self.compute_kind else None,
                config_schema={
                    "assets": {
                        "input_partitions": Field(dict, is_required=False),
                        "output_partitions": Field(dict, is_required=False),
                    }
                },
            )(fn)

        # NOTE: we can `cast` below because we know the Ins returned by `build_asset_ins` always
        # have a plain AssetKey asset key. Dynamic asset keys will be deprecated in 0.15.0, when
        # they are gone we can remove this cast.
        return AssetsDefinition(
            input_names_by_asset_key={
                cast(AssetKey, in_def.asset_key): input_name
                for input_name, in_def in asset_ins.items()
            },
            output_names_by_asset_key={out_asset_key: "result"},
            op=op,
            partitions_def=self.partitions_def,
            partition_mappings={
                cast(AssetKey, asset_ins[input_name].asset_key): partition_mapping
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
    compute_kind: Optional[str] = None,
    internal_asset_deps: Optional[Mapping[str, Set[AssetKey]]] = None,
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
        compute_kind (Optional[str]): A string to represent the kind of computation that produces
            the asset, e.g. "dbt" or "spark". It will be displayed in Dagit as a badge on the asset.
        internal_asset_deps (Optional[Mapping[str, Set[AssetKey]]]): By default, it is assumed
            that all assets produced by a multi_asset depend on all assets that are consumed by that
            multi asset. If this default is not correct, you pass in a map of output names to a
            corrected set of AssetKeys that they depend on. Any AssetKeys in this list must be either
            used as input to the asset or produced within the op.
    """

    check.invariant(
        all(out.asset_key is None or isinstance(out.asset_key, AssetKey) for out in outs.values()),
        "The asset_key argument for Outs supplied to a multi_asset must be a constant or None, not a function. ",
    )
    internal_asset_deps = check.opt_dict_param(
        internal_asset_deps, "internal_asset_deps", key_type=str, value_type=set
    )

    def inner(fn: Callable[..., Any]) -> AssetsDefinition:
        op_name = name or fn.__name__
        asset_ins = build_asset_ins(fn, None, ins or {}, non_argument_deps)
        asset_outs = build_asset_outs(op_name, outs, asset_ins, internal_asset_deps or {})

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=ExperimentalWarning)
            op = _Op(
                name=op_name,
                description=description,
                ins=asset_ins,
                out=asset_outs,
                required_resource_keys=required_resource_keys,
                tags={"kind": compute_kind} if compute_kind else None,
            )(fn)

        # NOTE: we can `cast` below because we know the Ins returned by `build_asset_ins` always
        # have a plain AssetKey asset key. Dynamic asset keys will be deprecated in 0.15.0, when
        # they are gone we can remove this cast.
        return AssetsDefinition(
            input_names_by_asset_key={
                cast(AssetKey, in_def.asset_key): input_name
                for input_name, in_def in asset_ins.items()
            },
            output_names_by_asset_key={
                cast(AssetKey, out_def.asset_key): output_name for output_name, out_def in asset_outs.items()  # type: ignore
            },
            op=op,
        )

    return inner


def build_asset_outs(
    op_name: str,
    outs: Mapping[str, Out],
    ins: Mapping[str, In],
    internal_asset_deps: Mapping[str, Set[AssetKey]],
) -> Dict[str, Out]:

    # if an AssetKey is not supplied, create one based off of the out's name
    asset_keys_by_out_name = {
        out_name: out.asset_key if isinstance(out.asset_key, AssetKey) else AssetKey([out_name])
        for out_name, out in outs.items()
    }

    # update asset_key if necessary, add metadata indicating inter asset deps
    outs = {
        out_name: out._replace(
            asset_key=asset_keys_by_out_name[out_name],
            metadata=dict(
                **(out.metadata or {}),
                **(
                    {ASSET_DEPENDENCY_METADATA_KEY: internal_asset_deps[out_name]}
                    if out_name in internal_asset_deps
                    else {}
                ),
            ),
        )
        for out_name, out in outs.items()
    }

    # validate that the internal_asset_deps make sense
    valid_asset_deps = set(in_def.asset_key for in_def in ins.values())
    valid_asset_deps.update(asset_keys_by_out_name.values())
    for out_name, asset_keys in internal_asset_deps.items():
        check.invariant(
            out_name in outs,
            f"Invalid out key '{out_name}' supplied to `internal_asset_deps` argument for multi-asset "
            f"{op_name}. Must be one of the outs for this multi-asset {list(outs.keys())}.",
        )
        invalid_asset_deps = asset_keys.difference(valid_asset_deps)
        check.invariant(
            not invalid_asset_deps,
            f"Invalid asset dependencies: {invalid_asset_deps} specified in `internal_asset_deps` "
            f"argument for multi-asset '{op_name}' on key '{out_name}'. Each specified asset key "
            "must be associated with an input to the asset or produced by this asset. Valid "
            f"keys: {valid_asset_deps}",
        )

    return outs


def build_asset_ins(
    fn: Callable,
    asset_namespace: Optional[Sequence[str]],
    asset_ins: Mapping[str, AssetIn],
    non_argument_deps: Optional[AbstractSet[AssetKey]],
) -> Dict[str, In]:

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
            list(filter(None, [*(namespace or asset_namespace or []), input_name]))
        )

        ins[input_name] = In(
            metadata=metadata,
            root_manager_key="root_manager",
            asset_key=asset_key,
            dagster_type=dagster_type,
        )

    for asset_key in non_argument_deps:
        stringified_asset_key = "_".join(asset_key.path)
        if stringified_asset_key:
            # cast due to mypy bug-- doesn't understand Nothing is a type
            ins[stringified_asset_key] = In(dagster_type=cast(type, Nothing), asset_key=asset_key)

    return ins
