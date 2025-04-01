import typing

import dagster._check as check
from dagster._config import Permissive
from dagster._core.types.config_schema import DagsterTypeLoader, dagster_type_loader
from dagster._core.types.dagster_type import (
    DagsterType,
    PythonObjectDagsterType,
    String,
    resolve_dagster_type,
)


@dagster_type_loader(Permissive())
def _dict_input(_context, value):
    return value


PythonDict = PythonObjectDagsterType(
    dict,
    "PythonDict",
    loader=_dict_input,
    description="""Represents a python dictionary to pass between ops""",
)


class TypedDictLoader(DagsterTypeLoader):
    def __init__(self, key_dagster_type, value_dagster_type):
        from dagster._config import ConfigTypeKind, Map, ScalarUnion

        self._key_dagster_type = check.inst_param(
            key_dagster_type, "key_dagster_type", DagsterType
        )
        check.param_invariant(self._key_dagster_type.loader, "key_dagster_type")

        # Scalar union config types allow for passing scalar values either directly,
        # or as a dictionary mapping set keys to a value. When a scalar union config type
        # is used as the key type for a dictionary, we extract the scalar type
        # only, so that we only permit passing the scalar value directly.
        if (
            self._key_dagster_type.loader.schema_type.kind
            == ConfigTypeKind.SCALAR_UNION
        ):
            key_schema_type = typing.cast(
                ScalarUnion, self._key_dagster_type.loader.schema_type
            ).scalar_type
        else:
            key_schema_type = self._key_dagster_type.loader.schema_type

        self._value_dagster_type = check.inst_param(
            value_dagster_type, "value_dagster_type", DagsterType
        )
        check.param_invariant(self._value_dagster_type.loader, "value_dagster_type")
        self._schema_type = Map(
            key_type=key_schema_type,
            inner_type=self._value_dagster_type.loader.schema_type,
        )

    @property
    def schema_type(self):
        return self._schema_type

    def construct_from_config_value(self, context, config_value):
        config_value = check.dict_param(config_value, "config_value")
        runtime_value = dict()
        for key, val in config_value.items():
            runtime_value[key] = (
                self._value_dagster_type.loader.construct_from_config_value(
                    context, val
                )
            )
        return runtime_value


class _TypedPythonDict(DagsterType):
    def __init__(self, key_type, value_type):
        self.key_type = check.inst_param(key_type, "key_type", DagsterType)
        self.value_type = check.inst_param(value_type, "value_type", DagsterType)
        can_get_from_config = (
            self.value_type.loader is not None
            and isinstance(self.key_type, type(String))
        )  # True if value_type has a DagsterTypeLoader, meaning we can load the input from config,
        # otherwise False.
        super(_TypedPythonDict, self).__init__(
            key=f"TypedPythonDict.{key_type.key}.{value_type.key}",
            name=None,
            loader=(
                TypedDictLoader(self.key_type, self.value_type)
                if can_get_from_config
                else None
            ),
            type_check_fn=self.type_check_method,
            typing_type=typing.Dict[key_type.typing_type, value_type.typing_type],
        )

    def type_check_method(self, context, value):
        from dagster._core.definitions.events import TypeCheck

        if not isinstance(value, dict):
            return TypeCheck(
                success=False,
                description=f"Value should be a dict, got a {type(value)}",
            )

        for key, value in value.items():
            key_check = self.key_type.type_check(context, key)
            if not key_check.success:
                return key_check
            value_check = self.value_type.type_check(context, value)
            if not value_check.success:
                return value_check

        return TypeCheck(success=True)

    @property
    def display_name(self):
        return f"Dict[{self.key_type.display_name},{self.value_type.display_name}]"

    @property
    def inner_types(self):
        return [self.key_type, self.value_type] + self.value_type.inner_types

    @property
    def type_param_keys(self):
        return [self.key_type.key, self.value_type.key]


def create_typed_runtime_dict(key_dagster_type, value_dagster_type):
    key_type = resolve_dagster_type(key_dagster_type)
    value_type = resolve_dagster_type(value_dagster_type)

    return _TypedPythonDict(key_type, value_type)


class DagsterDictApi:
    def __getitem__(self, *args):
        check.param_invariant(len(args[0]) == 2, "args", "Must be two parameters")
        return create_typed_runtime_dict(args[0][0], args[0][1])


Dict: DagsterDictApi = DagsterDictApi()
