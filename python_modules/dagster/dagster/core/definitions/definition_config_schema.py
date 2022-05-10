from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Union

import dagster._check as check
from dagster.config.config_schema import ConfigSchemaType
from dagster.config.config_type import ConfigAnyInstance, ConfigType
from dagster.config.evaluate_value_result import EvaluateValueResult
from dagster.config.field import Field
from dagster.config.field_utils import convert_potential_field
from dagster.config.validate import process_config
from dagster.core.errors import DagsterConfigMappingFunctionError, user_code_error_boundary

if TYPE_CHECKING:
    from dagster.core.definitions.configurable import ConfigurableDefinition


def convert_user_facing_definition_config_schema(
    potential_schema: Optional[Union["IDefinitionConfigSchema", ConfigSchemaType]]
) -> "IDefinitionConfigSchema":
    if potential_schema is None:
        return DefinitionConfigSchema(Field(ConfigAnyInstance, is_required=False))
    elif isinstance(potential_schema, IDefinitionConfigSchema):
        return potential_schema
    else:
        return DefinitionConfigSchema(convert_potential_field(potential_schema))


# This structure is used to represent the config schema attached to a definition
# and to implement the @configured capability. For each application of configured
# on a definition, there is an instance of ConfiguredDefinitionConfigSchema which
# contains a back pointer to the parent definition, the new schema, and the
# configuration (or config function) that translates a chunk of config (validated
# by the new schema) that will pass the parent definition's config schema.
#
class IDefinitionConfigSchema(ABC):
    @abstractmethod
    def as_field(self) -> Field:
        raise NotImplementedError()

    @property
    def config_type(self) -> Optional[ConfigType]:
        field = self.as_field()
        return field.config_type if field else None

    @property
    def is_required(self) -> bool:
        field = self.as_field()
        return field.is_required if field else False

    @property
    def default_provided(self) -> bool:
        field = self.as_field()
        return field.default_provided if field else False

    @property
    def default_value(self) -> Any:
        field = self.as_field()
        check.invariant(self.default_provided, "Asking for default value when none was provided")
        return field.default_value if field else None

    @property
    def default_value_as_json_str(self) -> str:
        field = self.as_field()
        check.invariant(self.default_provided, "Asking for default value when none was provided")
        return field.default_value_as_json_str

    @property
    def description(self) -> Optional[str]:
        field = self.as_field()
        return field.description if field else None


class DefinitionConfigSchema(IDefinitionConfigSchema):
    def __init__(self, config_field: Field):
        self._config_field = check.inst_param(config_field, "config_field", Field)

    def as_field(self) -> Field:
        return self._config_field


def _get_user_code_error_str_lambda(
    configured_definition: "ConfigurableDefinition",
) -> Callable[[], str]:
    return lambda: (
        "The config mapping function on a `configured` {} has thrown an unexpected "
        "error during its execution."
    ).format(configured_definition.__class__.__name__)


class ConfiguredDefinitionConfigSchema(IDefinitionConfigSchema):
    def __init__(self, parent_definition, config_schema, config_or_config_fn):
        from .configurable import ConfigurableDefinition

        self.parent_def = check.inst_param(
            parent_definition, "parent_definition", ConfigurableDefinition
        )
        check.opt_inst_param(config_schema, "config_schema", DefinitionConfigSchema)

        self._current_field = config_schema.as_field() if config_schema else None

        if not callable(config_or_config_fn):
            self._config_fn = lambda _: config_or_config_fn
        else:
            self._config_fn = config_or_config_fn

    def as_field(self) -> Field:
        return self._current_field

    def _invoke_user_config_fn(self, processed_config: Dict[str, Any]) -> Dict[str, Any]:
        with user_code_error_boundary(
            DagsterConfigMappingFunctionError,
            _get_user_code_error_str_lambda(self.parent_def),
        ):
            return {"config": self._config_fn(processed_config.get("config", {}))}

    def resolve_config(self, processed_config: Dict[str, Any]) -> EvaluateValueResult:
        check.dict_param(processed_config, "processed_config")
        # Validate resolved config against the inner definitions's config_schema (on self).
        config_evr = process_config(
            {"config": self.parent_def.config_field or {}},
            self._invoke_user_config_fn(processed_config),
        )
        if config_evr.success:
            return self.parent_def.apply_config_mapping(config_evr.value)  # Recursive step
        else:
            return config_evr  # Bubble up the errors
