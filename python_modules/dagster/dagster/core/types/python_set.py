from dagster import check
from dagster.config.config_type import Array

from .config_schema import InputHydrationConfig
from .dagster_type import DagsterType, PythonObjectDagsterType, resolve_dagster_type

PythonSet = PythonObjectDagsterType(
    set, 'PythonSet', description='''Represents a python dictionary to pass between solids'''
)


class TypedSetInputHydrationConfig(InputHydrationConfig):
    def __init__(self, item_runtime_type):
        self._item_runtime_type = check.inst_param(
            item_runtime_type, 'item_runtime_type', DagsterType
        )

    @property
    def schema_type(self):
        return Array(self._item_runtime_type.input_hydration_config.schema_type)

    def construct_from_config_value(self, context, config_value):
        runtime_value = set()
        for item in config_value:
            runtime_value.add(
                self._item_runtime_type.input_hydration_config.construct_from_config_value(
                    context, item
                )
            )
        return runtime_value


class _TypedPythonSet(DagsterType):
    def __init__(self, item_runtime_type):
        self.item_type = item_runtime_type
        super(_TypedPythonSet, self).__init__(
            key='TypedPythonSet.{}'.format(item_runtime_type.key),
            name=None,
            input_hydration_config=(
                TypedSetInputHydrationConfig(item_runtime_type)
                if item_runtime_type.input_hydration_config
                else None
            ),
            type_check_fn=self.type_check_method,
        )

    def type_check_method(self, context, value):
        from dagster.core.definitions.events import TypeCheck

        if not isinstance(value, set):
            return TypeCheck(
                success=False,
                description='Value should be a set, got a{value_type}'.format(
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
        return 'Set[{}]'.format(self.item_type.display_name)

    @property
    def inner_types(self):
        return [self.item_type]


def create_typed_runtime_set(item_dagster_type):
    item_runtime_type = resolve_dagster_type(item_dagster_type)

    check.invariant(
        not item_runtime_type.is_nothing,
        'Cannot create the runtime type Set[Nothing]. Use List type for fan-in.',
    )

    return _TypedPythonSet(item_runtime_type)


class DagsterSetApi:
    def __getitem__(self, inner_type):
        return create_typed_runtime_set(inner_type)


Set = DagsterSetApi()
