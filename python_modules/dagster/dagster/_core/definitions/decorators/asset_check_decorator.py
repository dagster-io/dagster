from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Callable, Optional, Union

from typing_extensions import TypeAlias

from dagster import _check as check
from dagster._config import UserConfigSchema
from dagster._core.decorator_utils import format_docstring_for_description
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.asset_dep import AssetDep, CoercibleToAssetDep
from dagster._core.definitions.asset_in import AssetIn, CoercibleToAssetIn
from dagster._core.definitions.asset_key import AssetCheckKey
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.decorators.asset_decorator import make_asset_deps
from dagster._core.definitions.decorators.decorator_assets_definition_builder import (
    DecoratorAssetsDefinitionBuilder,
    DecoratorAssetsDefinitionBuilderArgs,
    NamedIn,
    build_and_validate_named_ins,
    compute_required_resource_keys,
    get_function_params_without_context_or_config_or_resources,
    validate_named_ins_subset_of_deps,
)
from dagster._core.definitions.decorators.op_decorator import _Op
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.output import Out
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.utils import DEFAULT_OUTPUT
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.execution.build_resources import wrap_resources_for_execution
from dagster._core.storage.tags import COMPUTE_KIND_TAG
from dagster._utils.warnings import disable_dagster_warnings

AssetCheckFunctionReturn: TypeAlias = AssetCheckResult
AssetCheckFunction: TypeAlias = Callable[..., AssetCheckFunctionReturn]


def _build_asset_check_named_ins(
    name: str,
    asset_key: AssetKey,
    fn: Callable[..., Any],
    additional_ins: Mapping[str, AssetIn],
    additional_deps: Mapping[AssetKey, AssetDep],
) -> Mapping[AssetKey, NamedIn]:
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

    # if all the fn_params are in additional_ins, then we add the primary asset as a dep
    if len(fn_params) == len(additional_ins):
        all_deps = {**additional_deps, **{asset_key: AssetDep(asset_key)}}
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

    return build_and_validate_named_ins(
        fn=fn,
        asset_ins=all_ins,
        deps=all_deps.values(),
    )


def asset_check(
    *,
    asset: Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset],
    name: Optional[str] = None,
    description: Optional[str] = None,
    blocking: bool = False,
    additional_ins: Optional[Mapping[str, AssetIn]] = None,
    additional_deps: Optional[Iterable[CoercibleToAssetDep]] = None,
    required_resource_keys: Optional[set[str]] = None,
    resource_defs: Optional[Mapping[str, object]] = None,
    config_schema: Optional[UserConfigSchema] = None,
    compute_kind: Optional[str] = None,
    op_tags: Optional[Mapping[str, Any]] = None,
    retry_policy: Optional[RetryPolicy] = None,
    metadata: Optional[Mapping[str, Any]] = None,
    automation_condition: Optional[AutomationCondition[AssetCheckKey]] = None,
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
        metadata (Optional[Mapping[str, Any]]): A dictionary of static metadata for the check.
        automation_condition (Optional[AutomationCondition]): An AutomationCondition which determines
            when this check should be executed.

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

        additional_dep_keys = (
            {dep.asset_key: dep for dep in make_asset_deps(additional_deps) or []}
            if additional_deps
            else {}
        )
        named_in_by_asset_key = _build_asset_check_named_ins(
            resolved_name,
            asset_key,
            fn,
            additional_ins=additional_ins or {},
            additional_deps=additional_dep_keys,
        )

        # additional_deps on AssetCheckSpec holds the keys passed to additional_deps and
        # additional_ins. We don't want to include the primary asset key in this set.
        additional_ins_and_deps = named_in_by_asset_key.keys() - {asset_key}

        spec = AssetCheckSpec(
            name=resolved_name,
            description=description or format_docstring_for_description(fn),
            asset=asset_key,
            additional_deps=additional_ins_and_deps,
            blocking=blocking,
            metadata=metadata,
            automation_condition=automation_condition,
        )

        resource_defs_for_execution = wrap_resources_for_execution(resource_defs)

        builder_args = DecoratorAssetsDefinitionBuilderArgs(
            decorator_name="@asset_check",
            name=name,
            # @asset_check previous behavior is to not set description on underlying op
            op_description=None,
            required_resource_keys=required_resource_keys or set(),
            config_schema=config_schema,
            retry_policy=retry_policy,
            specs=[],
            check_specs_by_output_name={DEFAULT_OUTPUT: spec},
            can_subset=False,
            compute_kind=compute_kind,
            op_tags=op_tags,
            op_def_resource_defs=resource_defs_for_execution,
            assets_def_resource_defs=resource_defs_for_execution,
            upstream_asset_deps=[],
            # unsupported capabiltiies in asset checks
            partitions_def=None,
            code_version=None,
            backfill_policy=None,
            group_name=None,
            # non-sensical args in this context
            asset_deps={},
            asset_in_map={},
            asset_out_map={},
            execution_type=None,
            pool=None,
        )

        builder = DecoratorAssetsDefinitionBuilder(
            named_ins_by_asset_key=named_in_by_asset_key,
            named_outs_by_asset_key={},
            internal_deps={},
            op_name=spec.get_python_identifier(),
            args=builder_args,
            fn=fn,
        )

        op_def = builder.create_op_definition()

        return AssetChecksDefinition.create(
            keys_by_input_name={
                input_tuple[0]: asset_key
                for asset_key, input_tuple in named_in_by_asset_key.items()
            },
            node_def=op_def,
            resource_defs=resource_defs_for_execution,
            check_specs_by_output_name={op_def.output_defs[0].name: spec},
            can_subset=False,
        )

    return inner


MultiAssetCheckFunctionReturn: TypeAlias = Iterable[AssetCheckResult]
MultiAssetCheckFunction: TypeAlias = Callable[..., MultiAssetCheckFunctionReturn]


def multi_asset_check(
    *,
    name: Optional[str] = None,
    specs: Sequence[AssetCheckSpec],
    description: Optional[str] = None,
    can_subset: bool = False,
    compute_kind: Optional[str] = None,
    op_tags: Optional[Mapping[str, Any]] = None,
    resource_defs: Optional[Mapping[str, object]] = None,
    required_resource_keys: Optional[set[str]] = None,
    retry_policy: Optional[RetryPolicy] = None,
    config_schema: Optional[UserConfigSchema] = None,
    ins: Optional[Mapping[str, CoercibleToAssetIn]] = None,
) -> Callable[[Callable[..., Any]], AssetChecksDefinition]:
    """Defines a set of asset checks that can be executed together with the same op.

    Args:
        specs (Sequence[AssetCheckSpec]): Specs for the asset checks.
        name (Optional[str]): The name of the op. If not specified, the name of the decorated
            function will be used.
        description (Optional[str]): Description of the op.
        required_resource_keys (Optional[Set[str]]): A set of keys for resources that are required
            by the function that execute the checks. These can alternatively be specified by
            including resource-typed parameters in the function signature.
        config_schema (Optional[ConfigSchema): The configuration schema for the asset checks' underlying
            op. If set, Dagster will check that config provided for the op matches this schema and fail
            if it does not. If not set, Dagster will accept any config provided for the op.
        op_tags (Optional[Dict[str, Any]]): A dictionary of tags for the op that executes the checks.
            Frameworks may expect and require certain metadata to be attached to a op. Values that
            are not strings will be json encoded and must meet the criteria that
            `json.loads(json.dumps(value)) == value`.
        compute_kind (Optional[str]): A string to represent the kind of computation that executes
            the checks, e.g. "dbt" or "spark".
        retry_policy (Optional[RetryPolicy]): The retry policy for the op that executes the checks.
        can_subset (bool): Whether the op can emit results for a subset of the asset checks
            keys, based on the context.selected_asset_check_keys argument. Defaults to False.
        ins (Optional[Mapping[str, Union[AssetKey, AssetIn]]]): A mapping from input name to AssetIn depended upon by
            a given asset check. If an AssetKey is provided, it will be converted to an AssetIn with the same key.


    Examples:
        .. code-block:: python

            @multi_asset_check(
                specs=[
                    AssetCheckSpec("enough_rows", asset="asset1"),
                    AssetCheckSpec("no_dupes", asset="asset1"),
                    AssetCheckSpec("enough_rows", asset="asset2"),
                ],
            )
            def checks():
                yield AssetCheckResult(passed=True, asset_key="asset1", check_name="enough_rows")
                yield AssetCheckResult(passed=False, asset_key="asset1", check_name="no_dupes")
                yield AssetCheckResult(passed=True, asset_key="asset2", check_name="enough_rows")

    """
    required_resource_keys = check.opt_set_param(
        required_resource_keys, "required_resource_keys", of_type=str
    )
    resource_defs = wrap_resources_for_execution(
        check.opt_mapping_param(resource_defs, "resource_defs", key_type=str)
    )
    config_schema = check.opt_mapping_param(
        config_schema,  # type: ignore
        "config_schema",
        additional_message="Only dicts are supported for asset config_schema.",
    )

    def inner(fn: MultiAssetCheckFunction) -> AssetChecksDefinition:
        op_name = name or fn.__name__
        op_required_resource_keys = compute_required_resource_keys(
            required_resource_keys, resource_defs, fn=fn, decorator_name="@multi_asset_check"
        )

        outs = {
            spec.get_python_identifier(): Out(None, is_required=not can_subset) for spec in specs
        }
        all_deps_by_key = {
            **{spec.asset_key: AssetDep(spec.asset_key) for spec in specs},
            **{dep.asset_key: dep for spec in specs for dep in (spec.additional_deps or [])},
        }

        named_ins_by_asset_key = build_and_validate_named_ins(
            fn=fn,
            asset_ins={
                inp_name: AssetIn.from_coercible(coercible) for inp_name, coercible in ins.items()
            }
            if ins
            else {},
            deps=all_deps_by_key.values(),
        )
        validate_named_ins_subset_of_deps(named_ins_by_asset_key, all_deps_by_key)

        with disable_dagster_warnings():
            op_def = _Op(
                name=op_name,
                description=description,
                ins=dict(named_ins_by_asset_key.values()),
                out=outs,
                required_resource_keys=op_required_resource_keys,
                tags={
                    **({COMPUTE_KIND_TAG: compute_kind} if compute_kind else {}),
                    **(op_tags or {}),
                },
                config_schema=config_schema,
                retry_policy=retry_policy,
            )(fn)

        return AssetChecksDefinition.create(
            node_def=op_def,
            resource_defs=wrap_resources_for_execution(resource_defs),
            keys_by_input_name={
                input_tuple[0]: asset_key
                for asset_key, input_tuple in named_ins_by_asset_key.items()
            },
            check_specs_by_output_name={spec.get_python_identifier(): spec for spec in specs},
            can_subset=can_subset,
        )

    return inner
