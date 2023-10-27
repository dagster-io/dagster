import pickle

import dagster._check as check
import dagster._seven as seven
from dagster._config import (
    ConfigAnyInstance,
    ConfigBoolInstance,
    ConfigFloatInstance,
    ConfigIntInstance,
    ConfigStringInstance,
    ConfigType,
    ConfigTypeKind,
    Field,
    ScalarUnion,
    Selector,
)
from dagster._utils.warnings import disable_dagster_warnings

from .config_schema import dagster_type_loader


def define_typed_input_schema_dict(value_config_type):
    check.inst_param(value_config_type, "value_config_type", ConfigType)
    return Selector(
        {
            "value": Field(value_config_type),
            "json": define_path_dict_field(),
            "pickle": define_path_dict_field(),
        },
    )


def load_type_input_schema_dict(value):
    file_type, file_options = next(iter(value.items()))
    if file_type == "value":
        return file_options
    elif file_type == "json":
        with open(file_options["path"], "r", encoding="utf8") as ff:
            value_dict = seven.json.load(ff)
            return value_dict["value"]
    elif file_type == "pickle":
        with open(file_options["path"], "rb") as ff:
            return pickle.load(ff)
    else:
        check.failed(f"Unsupported key {file_type}")


def define_any_input_schema():
    @dagster_type_loader(define_typed_input_schema_dict(ConfigAnyInstance))
    def _any_input_schema(_, config_value):
        return load_type_input_schema_dict(config_value)

    return _any_input_schema


def define_builtin_scalar_input_schema(scalar_name, config_scalar_type):
    def _external_version_fn(val):
        from dagster._core.execution.resolve_versions import join_and_hash

        return join_and_hash(
            str(val),
        )

    check.str_param(scalar_name, "scalar_name")
    check.inst_param(config_scalar_type, "config_scalar_type", ConfigType)
    check.param_invariant(config_scalar_type.kind == ConfigTypeKind.SCALAR, "config_scalar_type")
    # TODO: https://github.com/dagster-io/dagster/issues/3084
    with disable_dagster_warnings():

        @dagster_type_loader(
            ScalarUnion(
                scalar_type=config_scalar_type,
                non_scalar_schema=define_typed_input_schema_dict(config_scalar_type),
            ),
            loader_version=scalar_name,  # different for each scalar type this is called upon
            external_version_fn=_external_version_fn,
        )
        def _builtin_input_schema(_context, value):
            return load_type_input_schema_dict(value) if isinstance(value, dict) else value

    return _builtin_input_schema


def define_path_dict_field():
    return {"path": Field(ConfigStringInstance)}


class BuiltinSchemas:
    ANY_INPUT = define_any_input_schema()

    BOOL_INPUT = define_builtin_scalar_input_schema("Bool", ConfigBoolInstance)

    FLOAT_INPUT = define_builtin_scalar_input_schema("Float", ConfigFloatInstance)

    INT_INPUT = define_builtin_scalar_input_schema("Int", ConfigIntInstance)

    STRING_INPUT = define_builtin_scalar_input_schema("String", ConfigStringInstance)
