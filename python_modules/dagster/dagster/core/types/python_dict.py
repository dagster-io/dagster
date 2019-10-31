from .config_schema import input_hydration_config
from .field_utils import PermissiveDict
from .runtime import RuntimeType, define_python_dagster_type, resolve_to_runtime_type


@input_hydration_config(PermissiveDict())
def _dict_input(_context, value):
    return value


PythonDict = define_python_dagster_type(
    dict,
    'PythonDict',
    input_hydration_config=_dict_input,
    description='''Represents a python dictionary to pass between solids''',
)


def create_typed_runtime_dict(key_dagster_type, value_dagster_type):
    key_type = resolve_to_runtime_type(key_dagster_type)
    value_type = resolve_to_runtime_type(value_dagster_type)

    class _TypedPythonDict(RuntimeType):
        def __init__(self):
            self.key_type = key_type
            self.value_type = value_type
            super(_TypedPythonDict, self).__init__(
                key='TypedPythonDict.{}.{}'.format(key_type.key, value_type.key),
                name=None,
                is_builtin=True,
            )

        def type_check(self, value):
            from dagster.core.definitions.events import Failure

            if not isinstance(value, dict):
                raise Failure('Value {value} should be a dict'.format(value=value))

            for key, value in value.items():
                key_type.type_check(key)
                value_type.type_check(value)

        @property
        def display_name(self):
            return 'Dict[{key},{value}]'.format(
                key=self.key_type.display_name, value=self.value_type.display_name
            )

    return _TypedPythonDict
