from .runtime import define_python_dagster_type

PythonTuple = define_python_dagster_type(
    tuple, 'PythonTuple', description='Represents a python tuple'
)
