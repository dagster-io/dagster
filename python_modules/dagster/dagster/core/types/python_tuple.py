from .runtime import RuntimeType, define_python_dagster_type, resolve_to_runtime_type

PythonTuple = define_python_dagster_type(
    tuple, 'PythonTuple', description='Represents a python tuple'
)


def create_typed_tuple(*dagster_type_args):
    runtime_types = list(map(resolve_to_runtime_type, dagster_type_args))

    class _TypedPythonTuple(RuntimeType):
        def __init__(self):
            super(_TypedPythonTuple, self).__init__(
                key='TypedPythonTuple' + '.'.join(map(lambda t: t.key, runtime_types)),
                name=None,
                is_builtin=True,
            )

        def type_check(self, value):
            from dagster.core.definitions.events import Failure

            if not isinstance(value, tuple):
                raise Failure('Value {value} should be a python tuple'.format(value=value))

            if len(value) != len(runtime_types):
                raise Failure(
                    'Tuple with key {key} requires {n} entries. Received tuple with {m} values'.format(
                        key=self.key, n=len(runtime_types), m=len(value)
                    )
                )

            for item, runtime_type in zip(value, runtime_types):
                runtime_type.type_check(item)

    return _TypedPythonTuple
