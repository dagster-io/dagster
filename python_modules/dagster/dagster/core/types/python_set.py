import typing

import dagster._check as check
from dagster.config.config_type import Array
from dagster.core.types.dagster_type import DagsterTypeKind

from .config_schema import DagsterTypeLoader
from .dagster_type import DagsterType, PythonObjectDagsterType, resolve_dagster_type

PythonSet = PythonObjectDagsterType(
    set, "PythonSet", description="""Represents a python dictionary to pass between solids"""
)


class TypedSetLoader(DagsterTypeLoader):
    def __init__(self, item_dagster_type):
        self._item_dagster_type = check.inst_param(
            item_dagster_type, "item_dagster_type", DagsterType
        )

    @property
    def schema_type(self):
        return Array(self._item_dagster_type.loader.schema_type)

    def construct_from_config_value(self, context, config_value):
        runtime_value = set()
        for item in config_value:
            runtime_value.add(
                self._item_dagster_type.loader.construct_from_config_value(context, item)
            )
        return runtime_value


class _TypedPythonSet(DagsterType):
    def __init__(self, item_dagster_type):
        self.item_type = item_dagster_type
        super(_TypedPythonSet, self).__init__(
            key="TypedPythonSet.{}".format(item_dagster_type.key),
            name=None,
            loader=(TypedSetLoader(item_dagster_type) if item_dagster_type.loader else None),
            type_check_fn=self.type_check_method,
            typing_type=typing.Set[item_dagster_type.typing_type],
        )

    def type_check_method(self, context, value):
        from dagster.core.definitions.events import TypeCheck

        if not isinstance(value, set):
            return TypeCheck(
                success=False,
                description="Value should be a set, got a{value_type}".format(
                    value_type=type(value)
                ),
            )

        for item in value:
            item_check = self.item_type.type_check(context, item)
            if not item_check.success:
                return item_check

        return TypeCheck(success=True)

    @property
    def display_name(self):
        return "Set[{}]".format(self.item_type.display_name)

    @property
    def inner_types(self):
        return [self.item_type] + self.item_type.inner_types

    @property
    def type_param_keys(self):
        return [self.item_type.key]


def create_typed_runtime_set(item_dagster_type):
    item_dagster_type = resolve_dagster_type(item_dagster_type)

    check.invariant(
        not item_dagster_type.kind == DagsterTypeKind.NOTHING,
        "Cannot create the runtime type Set[Nothing]. Use List type for fan-in.",
    )

    return _TypedPythonSet(item_dagster_type)


class DagsterSetApi:
    def __getitem__(self, inner_type):
        return create_typed_runtime_set(inner_type)


Set = DagsterSetApi()
