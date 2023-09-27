from typing import Any, Callable, Mapping, Optional, Set, Tuple, Union, cast

from dagster import _check as check
from dagster._annotations import experimental
from dagster._builtins import Nothing
from dagster._config import UserConfigSchema
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_checks import (
    AssetChecksDefinition,
    AssetChecksDefinitionInputOutputProps,
)
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.output import Out
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.utils import NoValueSentinel
from dagster._core.errors import DagsterInvalidDefinitionError

from ..input import In
from .asset_decorator import (
    get_function_params_without_context_or_config_or_resources,
    stringify_asset_key_to_input_name,
)
from .op_decorator import _Op

AssetCheckFunctionReturn = AssetCheckResult
AssetCheckFunction = Callable[..., AssetCheckFunctionReturn]


def _build_asset_check_input(
    name: str, asset_key: AssetKey, fn: Callable
) -> Mapping[AssetKey, Tuple[str, In]]:
    asset_params = get_function_params_without_context_or_config_or_resources(fn)

    if len(asset_params) == 0:
        input_name = stringify_asset_key_to_input_name(asset_key)
        in_def = In(cast(type, Nothing))
    elif len(asset_params) == 1:
        input_name = asset_params[0].name
        in_def = In(metadata={}, input_manager_key=None, dagster_type=NoValueSentinel)
    else:
        raise DagsterInvalidDefinitionError(
            f"When defining check '{name}', multiple target assets provided as parameters:"
            f" {[param.name for param in asset_params]}. Only one"
            " is allowed."
        )

    return {
        asset_key: (
            input_name,
            in_def,
        )
    }


@experimental
def asset_check(
    *,
    asset: Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset],
    name: Optional[str] = None,
    description: Optional[str] = None,
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

    def inner(fn: AssetCheckFunction) -> AssetChecksDefinition:
        check.callable_param(fn, "fn")
        resolved_name = name or fn.__name__
        asset_key = AssetKey.from_coercible_or_definition(asset)

        out = Out(dagster_type=None)
        input_tuples_by_asset_key = _build_asset_check_input(resolved_name, asset_key, fn)
        if len(input_tuples_by_asset_key) == 0:
            raise DagsterInvalidDefinitionError(
                f"No target asset provided when defining check '{resolved_name}'"
            )

        if len(input_tuples_by_asset_key) > 1:
            raise DagsterInvalidDefinitionError(
                f"When defining check '{resolved_name}', Multiple target assets provided:"
                f" {[key.to_user_string() for key in input_tuples_by_asset_key.keys()]}. Only one"
                " is allowed."
            )

        resolved_asset_key = next(iter(input_tuples_by_asset_key.keys()))
        spec = AssetCheckSpec(
            name=resolved_name,
            description=description,
            asset=resolved_asset_key,
        )

        op_def = _Op(
            name=spec.get_python_identifier(),
            ins=dict(input_tuples_by_asset_key.values()),
            out=out,
            # Any resource requirements specified as arguments will be identified as
            # part of the Op definition instantiation
            required_resource_keys=required_resource_keys,
            tags={
                **({"kind": compute_kind} if compute_kind else {}),
                **(op_tags or {}),
            },
            config_schema=config_schema,
            retry_policy=retry_policy,
        )(fn)

        checks_def = AssetChecksDefinition(
            node_def=op_def,
            resource_defs={},
            specs=[spec],
            input_output_props=AssetChecksDefinitionInputOutputProps(
                asset_keys_by_input_name={
                    input_tuples_by_asset_key[resolved_asset_key][0]: resolved_asset_key
                },
                asset_check_keys_by_output_name={op_def.output_defs[0].name: spec.key},
            ),
        )

        return checks_def

    return inner
