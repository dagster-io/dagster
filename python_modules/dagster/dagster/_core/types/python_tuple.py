import typing

import dagster._check as check
from dagster._config import Array, ConfigAnyInstance
from dagster._core.types.dagster_type import DagsterTypeKind

from .config_schema import DagsterTypeLoader
from .dagster_type import DagsterType, PythonObjectDagsterType, resolve_dagster_type

PythonTuple = PythonObjectDagsterType(tuple, "PythonTuple", description="Represents a python tuple")


class TypedTupleDagsterTypeLoader(DagsterTypeLoader):
    def __init__(self, dagster_types):
        self._dagster_types = check.list_param(dagster_types, "dagster_types", of_type=DagsterType)

    @property
    def schema_type(self):
        return Array(ConfigAnyInstance)

    def construct_from_config_value(self, context, config_value):
        return tuple(
            (
                self._dagster_types[idx].loader.construct_from_config_value(context, item)
                for idx, item in enumerate(config_value)
            )
        )


class _TypedPythonTuple(DagsterType):
    def __init__(self, dagster_types):
        all_have_input_configs = all((dagster_type.loader for dagster_type in dagster_types))
        self.dagster_types = dagster_types
        typing_types = tuple(t.typing_type for t in dagster_types)
        super(_TypedPythonTuple, self).__init__(
            key="TypedPythonTuple" + ".".join(map(lambda t: t.key, dagster_types)),
            name=None,
            loader=(TypedTupleDagsterTypeLoader(dagster_types) if all_have_input_configs else None),
            type_check_fn=self.type_check_method,
            typing_type=typing.Tuple[typing_types],
        )

    def type_check_method(self, context, value):
        from dagster._core.definitions.events import TypeCheck

        if not isinstance(value, tuple):
            return TypeCheck(
                success=False,
                description="Value should be a tuple, got a {value_type}".format(
                    value_type=type(value)
                ),
            )

        if len(value) != len(self.dagster_types):
            return TypeCheck(
                success=False,
                description=(
                    "Tuple with key {key} requires {n} entries, received {m} " "values"
                ).format(key=self.key, n=len(self.dagster_types), m=len(value)),
            )

        for item, dagster_type in zip(value, self.dagster_types):
            item_check = dagster_type.type_check(context, item)
            if not item_check.success:
                return item_check

        return TypeCheck(success=True)

    @property
    def display_name(self):
        return "Tuple[{}]".format(
            ",".join([inner_type.display_name for inner_type in self.dagster_types])
        )

    @property
    def inner_types(self):
        inner_types = self.dagster_types.copy()
        for t in self.dagster_types:
            inner_types += t.inner_types
        return inner_types

    @property
    def type_param_keys(self):
        return [dt.key for dt in self.dagster_types]


def create_typed_tuple(*dagster_type_args):
    dagster_types = list(map(resolve_dagster_type, dagster_type_args))

    check.invariant(
        not any((dagster_type.kind == DagsterTypeKind.NOTHING for dagster_type in dagster_types)),
        "Cannot create a runtime tuple containing inner type Nothing. Use List for fan-in",
    )

    return _TypedPythonTuple(dagster_types)


class DagsterTupleApi:
    def __getitem__(self, tuple_types):
        check.not_none_param(tuple_types, "tuple_types")
        if isinstance(tuple_types, tuple):
            return create_typed_tuple(*tuple_types)
        else:
            return create_typed_tuple(tuple_types)


Tuple = DagsterTupleApi()
