Types
=========

.. currentmodule:: dagster

Dagster includes facilities for typing the input and output values of ops ("runtime" types).

.. _builtin:

Built-in primitive types
-------------------------

.. attribute:: Any

    Use this type for any input, output, or config field whose type is unconstrained

    All values are considered to be instances of ``Any``.

    **Examples:**

    .. code-block:: python

        @op
        def identity(_, x: Any) -> Any:
            return x

        # Untyped inputs and outputs are implicitly typed Any
        @op
        def identity_imp(_, x):
            return x

        # Explicitly typed
        @op(
            ins={'x': In(dagster_type=Any)},
            out=Out(dagster_type=Any),
        )
        def identity(_, x):
            return x

        @op(config_schema=Field(Any))
        def any_config(context):
            return context.op_config


.. attribute:: Bool

    Use this type for any boolean input, output, or config_field. At runtime, this will perform an
    ``isinstance(value, bool)`` check. You may also use the ordinary :py:class:`~python:bool`
    type as an alias.

    **Examples:**

    .. code-block:: python

        @op
        def boolean(_, x: Bool) -> String:
            return 'true' if x else 'false'

        @op
        def empty_string(_, x: String) -> bool:
            return len(x) == 0

        # Explicit
        @op(
            ins={'x': In(dagster_type=Bool)},
            out=Out(dagster_type=String),
        )
        def boolean(_, x):
            return 'true' if x else 'false'

        @op(
            ins={'x': In(dagster_type=String)},
            out=Out(dagster_type=bool),
        )
        def empty_string(_, x):
            return len(x) == 0

        @op(config_schema=Field(Bool))
        def bool_config(context):
            return 'true' if context.op_config else 'false'


.. attribute:: Int

    Use this type for any integer input or output. At runtime, this will perform an
    ``isinstance(value, int)`` check. You may also use the ordinary :py:class:`~python:int`
    type as an alias.

    **Examples:**

    .. code-block:: python

        @op
        def add_3(_, x: Int) -> int:
            return x + 3

        # Explicit
        @op(
            ins={'x', In(dagster_type=Int)},
            out=Out(dagster_type=Int),
        )
        def add_3(_, x):
            return x + 3


.. attribute:: Float

    Use this type for any float input, output, or config value. At runtime, this will perform an
    ``isinstance(value, float)`` check. You may also use the ordinary :py:class:`~python:float`
    type as an alias.

    **Examples:**

    .. code-block:: python

        @op
        def div_2(_, x: Float) -> float:
            return x / 2

        # Explicit
        @op(
            ins={'x', In(dagster_type=Float)},
            out=Out(dagster_type=float),
        )
        def div_2(_, x):
            return x / 2

        @op(config_schema=Field(Float))
        def div_y(context, x: Float) -> float:
            return x / context.op_config


.. attribute:: String

    Use this type for any string input, output, or config value. At runtime, this will perform an
    ``isinstance(value, str)`` check. You may also use the ordinary :py:class:`~python:str` type
    as an alias.

    **Examples:**

    .. code-block:: python

        @op
        def concat(_, x: String, y: str) -> str:
            return x + y

        # Explicit
        @op(
            ins= {
                'x': In(dagster_type=String),
                'y': In(dagster_type=str),
            },
            out= Out(dagster_type=str),
        )
        def concat(_, x, y):
            return x + y

        @op(config_schema=Field(String))
        def hello(context) -> str:
            return 'Hello, {friend}!'.format(friend=context.op_config)


.. attribute:: Nothing

    Use this type only for inputs and outputs, in order to establish an execution dependency without
    communicating a value. Inputs of this type will not be pased to the op compute function, so
    it is necessary to use the explicit :py:class:`InputDefinition` API to define them rather than
    the Python 3 type hint syntax.

    All values are considered to be instances of ``Nothing``.

    **Examples:**

    .. code-block:: python

        @op
        def wait(_) -> Nothing:
            time.sleep(1)
            return

        @op(
            ins={"ready": In(dagster_type=Nothing)},
        )
        def done(_) -> str:
            return 'done'

        @job
        def nothing_job():
            done(wait())

        # Any value will pass the type check for Nothing
        @op
        def wait_int(_) -> Int:
            time.sleep(1)
            return 1

        @job
        def nothing_int_job():
            done(wait_int())


.. attribute:: Optional

    Use this type only for inputs and outputs, if the value can also be ``None``.

    **Examples:**

    .. code-block:: python

        @op
        def nullable_concat(_, x: str, y: Optional[str]) -> str:
            return x + (y or '')

        # Explicit
        @op(
            ins={
                'x': In(String),
                'y': In(Optional[String]),
            },
            out=Out(String),
        )
        def nullable_concat(_, x, y):
            return x + (y or '')

.. attribute:: List

    Use this type for inputs, or outputs.

    Lists are also the appropriate input types when fanning in multiple outputs using a
    :py:class:`MultiDependencyDefinition` or the equivalent composition function syntax.

    **Examples:**

    .. code-block:: python

        @op
        def concat_list(_, xs: List[str]) -> str:
            return ''.join(xs)

        # Explicit
        @op(
            ins={'xs': In(dagster_type=List[str])},
            out=Out(dagster_type=String),
        )
        def concat_list(_, xs) -> str:
            return ''.join(xs)

        # Fanning in multiple outputs
        @op
        def emit_1(_) -> int:
            return 1

        @op
        def emit_2(_) -> int:
            return 2

        @op
        def emit_3(_) -> int:
            return 3

        @op
        def sum_op(_, xs: List[int]) -> int:
            return sum(xs)

        @job
        def sum_job():
            sum_op([emit_1(), emit_2(), emit_3()])


.. attribute:: Dict

    Use this type for inputs, or outputs that are dicts.

    For inputs and outputs, you may optionally specify the key and value types using the square
    brackets syntax for Python typing.

    **Examples:**

    .. code-block:: python

        @op
        def repeat(_, spec: Dict) -> str:
            return spec['word'] * spec['times']

        # Explicit
        @op(
            ins={'spec': In(Dict)},
            out=Out(String),
        )
        def repeat(_, spec):
            return spec['word'] * spec['times']


.. attribute:: Set

    Use this type for inputs, or outputs that are sets. Alias for
    :py:class:`python:typing.Set`.

    You may optionally specify the inner type using the square brackets syntax for Python typing.

    **Examples:**

    .. code-block:: python

        @op
        def set_op(_, set_input: Set[String]) -> List[str]:
            return sorted([x for x in set_input])

        # Explicit
        @op(
            ins={"set_input": In(dagster_type=Set[String])},
            out=Out(List[String]),
        )
        def set_op(_, set_input):
            return sorted([x for x in set_input])

.. attribute:: Tuple

    Use this type for inputs or outputs that are tuples. Alias for
    :py:data:`python:typing.Tuple`.

    You may optionally specify the inner types using the square brackets syntax for Python typing.

    Config values should be passed as a list (in YAML or the Python config dict).

    **Examples:**

    .. code-block:: python

        @op
        def tuple_op(_, tuple_input: Tuple[str, int, float]) -> List:
            return [x for x in tuple_input]

        # Explicit
        @op(
            ins={'tuple_input': In(dagster_type=Tuple[String, Int, Float])},
            out=Out(List),
        )
        def tuple_op(_, tuple_input):
            return [x for x in tuple_input]


.. autoclass:: FileHandle
   :members:

.. autoclass:: LocalFileHandle

Making New Types
----------------

.. autoclass:: DagsterType

.. autofunction:: PythonObjectDagsterType

.. autofunction:: dagster_type_loader

.. autoclass:: DagsterTypeLoader

.. autofunction:: dagster_type_materializer

.. autoclass:: DagsterTypeMaterializer

.. autofunction:: usable_as_dagster_type

.. autofunction:: make_python_type_usable_as_dagster_type

Testing Types
^^^^^^^^^^^^^

.. autofunction:: check_dagster_type
