from typing import TYPE_CHECKING, Any, Callable, Mapping, NamedTuple, Optional, Union, cast

import dagster._check as check
from dagster._builtins import BuiltinEnum
from dagster._config import (
    ConfigType,
    is_supported_config_python_builtin,
    process_config,
    resolve_defaults,
    validate_config,
)
from dagster._core.definitions.definition_config_schema import IDefinitionConfigSchema
from dagster._core.errors import DagsterInvalidConfigError

from .definition_config_schema import convert_user_facing_definition_config_schema

if TYPE_CHECKING:
    from .pipeline_definition import PipelineDefinition


def is_callable_valid_config_arg(config: Union[Callable[..., Any], Mapping[str, object]]) -> bool:
    return BuiltinEnum.contains(config) or is_supported_config_python_builtin(config)


class ConfigMapping(
    NamedTuple(
        "_ConfigMapping",
        [
            ("config_fn", Callable[[Any], Any]),
            ("config_schema", IDefinitionConfigSchema),
            ("receive_processed_config_values", Optional[bool]),
        ],
    )
):
    """Defines a config mapping for a graph (or job).

    By specifying a config mapping function, you can override the configuration for the child
    ops and graphs contained within a graph.

    Config mappings require the configuration schema to be specified as ``config_schema``, which will
    be exposed as the configuration schema for the graph, as well as a configuration mapping
    function, ``config_fn``, which maps the config provided to the composite solid to the config
    that will be provided to the child nodes.

    Args:
        config_fn (Callable[[dict], dict]): The function that will be called
            to map the graph config to a config appropriate for the child nodes.
        config_schema (ConfigSchema): The schema of the graph config.
        receive_processed_config_values (Optional[bool]): If true, config values provided to the config_fn
            will be converted to their dagster types before being passed in. For example, if this
            value is true, enum config passed to config_fn will be actual enums, while if false,
            then enum config passed to config_fn will be strings.
    """

    def __new__(
        cls,
        config_fn: Callable[[Any], Any],
        config_schema: Optional[Any] = None,
        receive_processed_config_values: Optional[bool] = None,
    ):
        return super(ConfigMapping, cls).__new__(
            cls,
            config_fn=check.callable_param(config_fn, "config_fn"),
            config_schema=convert_user_facing_definition_config_schema(config_schema),
            receive_processed_config_values=check.opt_bool_param(
                receive_processed_config_values, "receive_processed_config_values"
            ),
        )

    def resolve_from_unvalidated_config(self, config: Any) -> Any:
        """Validates config against outer config schema, and calls mapping against validated config."""

        receive_processed_config_values = check.opt_bool_param(
            self.receive_processed_config_values, "receive_processed_config_values", default=True
        )
        if receive_processed_config_values:
            outer_evr = process_config(
                self.config_schema.config_type,
                config,
            )
        else:
            outer_evr = validate_config(
                self.config_schema.config_type,
                config,
            )
        if not outer_evr.success:
            raise DagsterInvalidConfigError(
                "Error in config mapping ",
                outer_evr.errors,
                config,
            )

        outer_config = outer_evr.value
        if not receive_processed_config_values:
            outer_config = resolve_defaults(
                cast(ConfigType, self.config_schema.config_type),
                outer_config,
            ).value

        return self.config_fn(outer_config)

    def resolve_from_validated_config(self, config: Any) -> Any:
        if self.receive_processed_config_values is not None:
            check.failed(
                "`receive_processed_config_values` parameter has been set, but only applies to "
                "unvalidated config."
            )

        return self.config_fn(config)
