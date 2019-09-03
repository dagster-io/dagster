from .config_schema import input_hydration_config
from .field_utils import PermissiveDict
from .runtime import define_python_dagster_type


@input_hydration_config(PermissiveDict())
def _dict_input(_context, value):
    return value


PythonDict = define_python_dagster_type(
    dict,
    'PythonDict',
    input_hydration_config=_dict_input,
    description='''Represents a python dictionary pass between solids''',
)
