from typing import AbstractSet, Any, Callable, Iterable, Mapping, Optional, Set, Tuple, Union

from typing_extensions import TypeAlias

from dagster import _check as check
from dagster._annotations import experimental
from dagster._config import UserConfigSchema
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.asset_dep import CoercibleToAssetDep
from dagster._core.definitions.asset_in import AssetIn
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.output import Out
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.definitions.resource_annotation import get_resource_args
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.execution.build_resources import wrap_resources_for_execution

from ..input import In
from .asset_decorator import (
    build_asset_ins,
    get_function_params_without_context_or_config_or_resources,
    make_asset_deps,
)
from .op_decorator import _Op

AssetCheckFunctionReturn: TypeAlias = AssetCheckResult
AssetCheckFunction: TypeAlias = Callable[..., AssetCheckFunctionReturn]


def _build_asset_check_input(
    name: str,
    asset_key: AssetKey,
    fn: Callable[..., Any],
    additional_ins: Mapping[str, AssetIn],
    additional_deps: Optional[AbstractSet[AssetKey]],
) -> Mapping[AssetKey, Tuple[str, In]]:
    fn_params = get_function_params_without_context_or_config_or_resources(fn)

    if asset_key in (additional_deps or []):
        raise DagsterInvalidDefinitionError(
            f"When defining check '{name}', asset '{asset_key.to_user_string()}' was passed to `asset` and `additional_deps`."
            " It can only be passed to one of these parameters."
        )
    if asset_key in [asset_in.key for asset_in in additional_ins.values()]:
        raise DagsterInvalidDefinitionError(
            f"When defining check '{name}', asset '{asset_key.to_user_string()}' was passed to `asset` and `additional_ins`."
            " It can only be passed to one of these parameters."
        )

    fn_param_names = {param.name for param in fn_params}
    for in_name in additional_ins.keys():
        if in_name not in fn_param_names:
            raise DagsterInvalidDefinitionError(
                f"'{in_name}' is specified in 'additional_ins' but isn't a parameter."
            )

    # if all the fn_params are in additional_ins, then we add the prmary asset as a dep
    if len(fn_params) == len(additional_ins):
        all_deps = {*(additional_deps if additional_deps else set()), asset_key}
        all_ins = additional_ins
    # otherwise there should be one extra fn_param, which is the primary asset. Add that as an input
    elif len(fn_params) == len(additional_ins) + 1:
        primary_asset_param_name = next(
            param.name for param in fn_params if param.name not in additional_ins.keys()
        )
        all_ins = {**additional_ins, primary_asset_param_name: AssetIn(asset_key)}
        all_deps = additional_deps
    else:
        param_names_not_in_additional_ins = sorted(
            [f"'{name}'" for name in (fn_param_names - set(additional_ins.keys()))]
        )
        raise DagsterInvalidDefinitionError(
            f"When defining check '{name}', multiple assets provided as parameters:"
            f" [{', '.join(param_names_not_in_additional_ins)}]. These should either match"
            " the target asset or be specified in 'additional_ins'."
        )

    return build_asset_ins(
        fn=fn,
        asset_ins=all_ins,
        deps=all_deps,
    )


@experimental
def asset_check(
    *,
    asset: Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset],
    name: Optional[str] = None,
    description: Optional[str] = None,
    blocking: bool = False,
    additional_ins: Optional[Mapping[str, AssetIn]] = None,
    additional_deps: Optional[Iterable[CoercibleToAssetDep]] = None,
    required_resource_keys: Optional[Set[str]] = None,
    resource_defs: Optional[Mapping[str, object]] = None,
    config_schema: Optional[UserConfigSchema] = None,
    compute_kind: Optional[str] = None,
    op_tags: Optional[Mapping[str, Any]] = None,
    retry_policy: Optional[RetryPolicy] = None,
) -> Callable[[AssetCheckFunction], AssetChecksDefinition]:
    """Create a definition for how to execute an asset check.

    Args:
        asset (Union[AssetKey, Sequence[str], str, AssetsDefinition, SourceAsset]): The
            asset that the check applies to.
        name (Optional[str]): The name of the check. If not specified, the name of the decorated
            function will be used. Checks for the same asset must have unique names.
        description (Optional[str]): The description of the check.
        blocking (bool): When enabled, runs that include this check and any downstream assets that
            depend on `asset` will wait for this check to complete before starting the downstream
            assets. If the check fails with severity `AssetCheckSeverity.ERROR`, then the downstream
            assets won't execute.
        additional_ins (Optional[Mapping[str, AssetIn]]): A mapping from input name to
            information about the input. These inputs will apply to the underlying op that
            executes the check. These should not include the `asset` parameter, which is
            always included as a dependency.
        additional_deps (Optional[Iterable[CoercibleToAssetDep]]): Assets that are upstream
            dependencies, but do not correspond to a parameter of the decorated function. These
            dependencies will apply to the underlying op that executes the check. These should not
            include the `asset` parameter, which is always included as a dependency.
        required_resource_keys (Optional[Set[str]]): A set of keys for resources that are required
            by the function that execute the check. These can alternatively be specified by
            including resource-typed parameters in the function signature.
        config_schema (Optional[ConfigSchema): The configuration schema for the check's underlying
            op. If set, Dagster will check that config provided for the op matches this schema and fail
            if it does not. If not set, Dagster will accept any config provided for the op.
        op_tags (Optional[Dict[str, Any]]): A dictionary of tags for the op that executes the check.
            Frameworks may expect and require certain metadata to be attached to a op. Values that
            are not strings will be json encoded and must meet the criteria that
            `json.loads(json.dumps(value)) == value`.
        compute_kind (Optional[str]): A string to represent the kind of computation that executes
            the check, e.g. "dbt" or "spark".
        retry_policy (Optional[RetryPolicy]): The retry policy for the op that executes the check.


    Produces an :py:class:`AssetChecksDefinition` object.


    Example:
        .. code-block:: python

            from dagster import asset, asset_check, AssetCheckResult

            @asset
            def my_asset() -> None:
                ...

            @asset_check(asset=my_asset, description="Check that my asset has enough rows")
            def my_asset_has_enough_rows() -> AssetCheckResult:
                num_rows = ...
                return AssetCheckResult(passed=num_rows > 5, metadata={"num_rows": num_rows})


    Example with a DataFrame Output:
        .. code-block:: python

            from dagster import asset, asset_check, AssetCheckResult
            from pandas import DataFrame

            @asset
            def my_asset() -> DataFrame:
                ...

            @asset_check(asset=my_asset, description="Check that my asset has enough rows")
            def my_asset_has_enough_rows(my_asset: DataFrame) -> AssetCheckResult:
                num_rows = my_asset.shape[0]
                return AssetCheckResult(passed=num_rows > 5, metadata={"num_rows": num_rows})
    """
    check.opt_set_param(required_resource_keys, "required_resource_keys", of_type=str)
    dict(check.opt_mapping_param(resource_defs, "resource_defs", key_type=str))

    def inner(fn: AssetCheckFunction) -> AssetChecksDefinition:
        check.callable_param(fn, "fn")
        resolved_name = name or fn.__name__
        asset_key = AssetKey.from_coercible_or_definition(asset)

        additional_dep_keys = set([dep.asset_key for dep in make_asset_deps(additional_deps) or []])
        input_tuples_by_asset_key = _build_asset_check_input(
            resolved_name,
            asset_key,
            fn,
            additional_ins=additional_ins or {},
            additional_deps=additional_dep_keys,
        )

        # additional_deps on AssetCheckSpec holds the keys passed to additional_deps and
        # additional_ins. We don't want to include the primary asset key in this set.
        additional_ins_and_deps = input_tuples_by_asset_key.keys() - {asset_key}

        spec = AssetCheckSpec(
            name=resolved_name,
            description=description,
            asset=asset_key,
            additional_deps=additional_ins_and_deps,
            blocking=blocking,
        )

        arg_resource_keys = {arg.name for arg in get_resource_args(fn)}

        check.param_invariant(
            len(required_resource_keys or []) == 0 or len(arg_resource_keys) == 0,
            "Cannot specify resource requirements in both @asset_check decorator and as arguments"
            " to the decorated function",
        )

        resource_defs_keys = set(resource_defs.keys() if resource_defs else [])
        decorator_resource_keys = (required_resource_keys or set()) | resource_defs_keys

        op_required_resource_keys = decorator_resource_keys - arg_resource_keys

        out = Out(dagster_type=None)

        op_def = _Op(
            name=spec.get_python_identifier(),
            ins=dict(input_tuples_by_asset_key.values()),
            out=out,
            # Any resource requirements specified as arguments will be identified as
            # part of the Op definition instantiation
            required_resource_keys=op_required_resource_keys,
            tags={
                **({"kind": compute_kind} if compute_kind else {}),
                **(op_tags or {}),
            },
            config_schema=config_schema,
            retry_policy=retry_policy,
        )(fn)

        return AssetChecksDefinition.create(
            keys_by_input_name={
                input_tuple[0]: asset_key
                for asset_key, input_tuple in input_tuples_by_asset_key.items()
            },
            node_def=op_def,
            resource_defs=wrap_resources_for_execution(resource_defs),
            check_specs_by_output_name={op_def.output_defs[0].name: spec},
        )

    return inner
