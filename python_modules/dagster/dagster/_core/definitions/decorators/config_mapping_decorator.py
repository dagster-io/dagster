from typing import Any, Callable, Optional, Union, overload

import dagster._check as check
from dagster._config import UserConfigSchema

from ..config import ConfigMapping, ConfigMappingFn


class _ConfigMapping:
    def __init__(
        self,
        config_schema: Optional[UserConfigSchema] = None,
        receive_processed_config_values: Optional[bool] = None,
    ):
        self.config_schema = config_schema
        self.receive_processed_config_values = check.opt_bool_param(
            receive_processed_config_values, "receive_processed_config_values"
        )

    def __call__(self, fn: Callable[..., Any]) -> ConfigMapping:
        check.callable_param(fn, "fn")

        return ConfigMapping(
            config_fn=fn,
            config_schema=self.config_schema,
            receive_processed_config_values=self.receive_processed_config_values,
        )


@overload
def config_mapping(
    config_fn: ConfigMappingFn,
) -> ConfigMapping:
    ...


@overload
def config_mapping(
    *,
    config_schema: UserConfigSchema = ...,
    receive_processed_config_values: Optional[bool] = ...,
) -> Callable[[ConfigMappingFn], ConfigMapping]:
    ...


def config_mapping(
    config_fn: Optional[Callable[..., Any]] = None,
    *,
    config_schema: Optional[UserConfigSchema] = None,
    receive_processed_config_values: Optional[bool] = None,
) -> Union[Callable[[ConfigMappingFn], ConfigMapping], ConfigMapping]:
    """Create a config mapping with the specified parameters from the decorated function.

    The config schema will be inferred from the type signature of the decorated function if not explicitly provided.

    Args:
        config_schema (ConfigSchema): The schema of the composite config.
        receive_processed_config_values (Optional[bool]): If true, config values provided to the config_fn
            will be converted to their dagster types before being passed in. For example, if this
            value is true, enum config passed to config_fn will be actual enums, while if false,
            then enum config passed to config_fn will be strings.


    Examples:
        .. code-block:: python

            @op
            def my_op(context):
                return context.op_config["foo"]

            @graph
            def my_graph():
                my_op()

            @config_mapping
            def my_config_mapping(val):
                return {"ops": {"my_op": {"config": {"foo": val["foo"]}}}}

            @config_mapping(config_schema={"foo": str})
            def my_config_mapping(val):
                return {"ops": {"my_op": {"config": {"foo": val["foo"]}}}}

            result = my_graph.to_job(config=my_config_mapping).execute_in_process()

    """
    # This case is for when decorator is used bare, without arguments. e.g. @config_mapping versus @config_mapping()
    if config_fn is not None:
        check.invariant(config_schema is None)
        check.invariant(receive_processed_config_values is None)

        return _ConfigMapping()(config_fn)

    check.invariant(config_fn is None)
    return _ConfigMapping(
        config_schema=config_schema,
        receive_processed_config_values=receive_processed_config_values,
    )
