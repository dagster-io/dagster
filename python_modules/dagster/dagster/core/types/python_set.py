from .runtime import define_python_dagster_type

PythonSet = define_python_dagster_type(
    set, 'PythonSet', description='''Represents a python dictionary to pass between solids'''
)
