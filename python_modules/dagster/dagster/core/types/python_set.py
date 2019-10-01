from .runtime import RuntimeType, define_python_dagster_type, resolve_to_runtime_type

PythonSet = define_python_dagster_type(
    set, 'PythonSet', description='''Represents a python dictionary to pass between solids'''
)


def create_typed_runtime_set(item_dagster_type):
    item_runtime_type = resolve_to_runtime_type(item_dagster_type)

    class _TypedPythonSet(RuntimeType):
        def __init__(self):
            super(_TypedPythonSet, self).__init__(
                key='TypedPythonSet.{}'.format(item_runtime_type.key), name=None, is_builtin=True
            )

            self.item_type = item_runtime_type

        def type_check(self, value):
            from dagster.core.definitions.events import Failure

            if not isinstance(value, set):
                raise Failure('Value {value} should be a set'.format(value=value))

            for item in value:
                item_runtime_type.type_check(item)

    return _TypedPythonSet
