from dagster import check

from .config import List
from .config_schema import InputHydrationConfig
from .runtime import RuntimeType, define_python_dagster_type, resolve_to_runtime_type

PythonSet = define_python_dagster_type(
    set, 'PythonSet', description='''Represents a python dictionary to pass between solids'''
)


class TypedSetInputHydrationConfig(InputHydrationConfig):
    def __init__(self, item_runtime_type):
        self._item_runtime_type = check.inst_param(
            item_runtime_type, 'item_runtime_type', RuntimeType
        )

    @property
    def schema_type(self):
        return List(self._item_runtime_type.input_hydration_config.schema_type)

    def construct_from_config_value(self, context, config_value):
        runtime_value = set()
        for item in config_value:
            runtime_value.add(
                self._item_runtime_type.input_hydration_config.construct_from_config_value(
                    context, item
                )
            )
        return runtime_value


def create_typed_runtime_set(item_dagster_type):
    item_runtime_type = resolve_to_runtime_type(item_dagster_type)

    check.invariant(
        not item_runtime_type.is_nothing,
        'Cannot create the runtime type Set[Nothing]. Use List type for fan-in.',
    )

    class _TypedPythonSet(RuntimeType):
        def __init__(self):
            self.item_type = item_runtime_type
            super(_TypedPythonSet, self).__init__(
                key='TypedPythonSet.{}'.format(item_runtime_type.key),
                name=None,
                is_builtin=True,
                input_hydration_config=(
                    TypedSetInputHydrationConfig(item_runtime_type)
                    if item_runtime_type.input_hydration_config
                    else None
                ),
            )

        def type_check(self, value):
            from dagster.core.definitions.events import TypeCheck

            if not isinstance(value, set):
                return TypeCheck(
                    success=False,
                    description='Value should be a set, got a{value_type}'.format(
                        value_type=type(value)
                    ),
                )

            for item in value:
                item_check = item_runtime_type.type_check(item)
                if not item_check.success:
                    return item_check

            return TypeCheck(success=True)

        @property
        def display_name(self):
            return 'Set[{}]'.format(self.item_type.display_name)

    return _TypedPythonSet
