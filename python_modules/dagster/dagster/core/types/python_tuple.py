from dagster import check
from dagster.config.config_type import Array, ConfigAnyInstance

from .config_schema import InputHydrationConfig
from .dagster_type import DagsterType, PythonObjectDagsterType, resolve_dagster_type

PythonTuple = PythonObjectDagsterType(tuple, 'PythonTuple', description='Represents a python tuple')


class TypedTupleInputHydrationConfig(InputHydrationConfig):
    def __init__(self, runtime_types):
        self._runtime_types = check.list_param(runtime_types, 'runtime_types', of_type=DagsterType)

    @property
    def schema_type(self):
        return Array(ConfigAnyInstance)

    def construct_from_config_value(self, context, config_value):
        return tuple(
            (
                self._runtime_types[idx].input_hydration_config.construct_from_config_value(
                    context, item
                )
                for idx, item in enumerate(config_value)
            )
        )


class _TypedPythonTuple(DagsterType):
    def __init__(self, runtime_types):
        all_have_input_configs = all(
            (runtime_type.input_hydration_config for runtime_type in runtime_types)
        )
        self.runtime_types = runtime_types
        super(_TypedPythonTuple, self).__init__(
            key='TypedPythonTuple' + '.'.join(map(lambda t: t.key, runtime_types)),
            name=None,
            input_hydration_config=(
                TypedTupleInputHydrationConfig(runtime_types) if all_have_input_configs else None
            ),
            type_check_fn=self.type_check_method,
        )

    def type_check_method(self, context, value):
        from dagster.core.definitions.events import TypeCheck

        if not isinstance(value, tuple):
            return TypeCheck(
                success=False,
                description='Value should be a tuple, got a {value_type}'.format(
                    value_type=type(value)
                ),
            )

        if len(value) != len(self.runtime_types):
            return TypeCheck(
                success=False,
                description=(
                    'Tuple with key {key} requires {n} entries, received {m} ' 'values'
                ).format(key=self.key, n=len(self.runtime_types), m=len(value)),
            )

        for item, runtime_type in zip(value, self.runtime_types):
            item_check = runtime_type.type_check(context, item)
            if not item_check.success:
                return item_check

        return TypeCheck(success=True)

    @property
    def display_name(self):
        return 'Tuple[{}]'.format(
            ','.join([inner_type.display_name for inner_type in self.runtime_types])
        )

    @property
    def inner_types(self):
        return self.runtime_types


def create_typed_tuple(*dagster_type_args):
    runtime_types = list(map(resolve_dagster_type, dagster_type_args))

    check.invariant(
        not any((runtime_type.is_nothing for runtime_type in runtime_types)),
        'Cannot create a runtime tuple containing inner type Nothing. Use List for fan-in',
    )

    return _TypedPythonTuple(runtime_types)


class DagsterTupleApi:
    def __getitem__(self, tuple_types):
        check.not_none_param(tuple_types, 'tuple_types')
        if isinstance(tuple_types, tuple):
            return create_typed_tuple(*tuple_types)
        else:
            return create_typed_tuple(tuple_types)


Tuple = DagsterTupleApi()
