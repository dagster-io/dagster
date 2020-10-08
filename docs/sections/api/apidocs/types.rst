Types
=========

.. currentmodule:: dagster

Dagster includes facilities for typing the input and output values of solids ("runtime" types).

.. _builtin:

Built-in primitive types
-------------------------

.. attribute:: Any

    Use this type for any input, output, or config field whose type is unconstrained

    All values are considered to be instances of ``Any``.

    **Examples:**

    .. code-block:: python

        @solid
        def identity(_, x: Any) -> Any:
            return x

        # Untyped inputs and outputs are implicitly typed Any
        @solid
        def identity_imp(_, x):
            return x

        # Explicitly typed on Python 2
        @solid(
            input_defs=[InputDefinition('x', dagster_type=Any)],
            output_defs=[OutputDefinition(dagster_type=Any)]
        )
        def identity_py2(_, x):
            return x

        @solid(config_schema=Field(Any))
        def any_config(context):
            return context.solid_config


.. attribute:: Bool

    Use this type for any boolean input, output, or config_field. At runtime, this will perform an
    ``isinstance(value, bool)`` check. You may also use the ordinary :py:class:`~python:bool`
    type as an alias.

    **Examples:**

    .. code-block:: python

        @solid
        def boolean(_, x: Bool) -> String:
            return 'true' if x else 'false'

        @solid
        def empty_string(_, x: String) -> bool:
            return len(x) == 0

        # Python 2
        @solid(
            input_defs=[InputDefinition('x', dagster_type=Bool)],
            output_defs=[OutputDefinition(dagster_type=String)]
        )
        def boolean_py2(_, x):
            return 'true' if x else 'false'

        @solid(
            input_defs=[InputDefinition('x', dagster_type=String)],
            output_defs=[OutputDefinition(dagster_type=bool)]
        )
        def empty_string_py2(_, x):
            return len(x) == 0

        @solid(config_schema=Field(Bool))
        def bool_config(context):
            return 'true' if context.solid_config else 'false'


.. attribute:: Int

    Use this type for any integer input or output. At runtime, this will perform an
    ``isinstance(value, six.integer_types)`` check -- that is, on Python 2, both ``long`` and
    ``int`` will pass this check. In Python 3, you may also use the ordinary :py:class:`~python:int`
    type as an alias.

    **Examples:**

    .. code-block:: python

        @solid
        def add_3(_, x: Int) -> int:
            return x + 3

        # Python 2
        @solid(
            input_defs=[InputDefinition('x', dagster_type=Int)],
            output_defs=[OutputDefinition(dagster_type=int)]
        )
        def add_3_py2(_, x):
            return x + 3


.. attribute:: Float

    Use this type for any float input, output, or config value. At runtime, this will perform an
    ``isinstance(value, float)`` check. You may also use the ordinary :py:class:`~python:float`
    type as an alias.

    **Examples:**

    .. code-block:: python

        @solid
        def div_2(_, x: Float) -> float:
            return x / 2

        @solid(
            input_defs=[InputDefinition('x', dagster_type=Float)],
            output_defs=[OutputDefinition(dagster_type=float)]
        )
        def div_2_py_2(_, x):
            return x / 2

        @solid(config_schema=Field(Float))
        def div_y(context, x: Float) -> float:
            return x / context.solid_config


.. attribute:: String

    Use this type for any string input, output, or config value. At runtime, this will perform an
    ``isinstance(value, six.string_types)`` -- that is on Python 2, both ``unicode`` and ``str``
    will pass this check. In Python 3, you may also use the ordinary :py:class:`~python:str` type
    as an alias.

    **Examples:**

    .. code-block:: python

        @solid
        def concat(_, x: String, y: str) -> str:
            return x + y

        @solid(
            input_defs=[
                InputDefinition('x', dagster_type=String),
                InputDefinition('y', dagster_type=str)
            ],
            output_defs=[OutputDefinition(dagster_type=str)]
        )
        def concat_py_2(_, x, y):
            return x + y

        @solid(config_schema=Field(String))
        def hello(context) -> str:
            return 'Hello, {friend}!'.format(friend=context.solid_config)


.. attribute:: Nothing

    Use this type only for inputs and outputs, in order to establish an execution dependency without
    communicating a value. Inputs of this type will not be pased to the solid compute function, so
    it is necessary to use the explicit :py:class:`InputDefinition` API to define them rather than
    the Python 3 type hint syntax.

    All values are considered to be instances of ``Nothing``.

    **Examples:**

    .. code-block:: python

        @solid
        def wait(_) -> Nothing:
            time.sleep(1)
            return

        @solid(
            InputDefinition('ready', dagster_type=Nothing)
        )
        def done(_) -> str:
            return 'done'

        @pipeline
        def nothing_pipeline():
            done(wait())

        # Any value will pass the type check for Nothing
        @solid
        def wait_int(_) -> Int:
            time.sleep(1)
            return 1

        @pipeline
        def nothing_int_pipeline():
            done(wait_int())


.. attribute:: Optional

    Use this type only for inputs and outputs, if the value can also be ``None``.

    **Examples:**

    .. code-block:: python

        @solid
        def nullable_concat(_, x: String, y: Optional[String]) -> String:
            return x + (y or '')

        # Python 2
        @solid(
            input_defs=[
                InputDefinition('x', dagster_type=String),
                InputDefinition('y', dagster_type=Optional[String])
            ],
            output_defs=[OutputDefinition(dagster_type=String)]
        )
        def nullable_concat_py2(_, x, y):
            return x + (y or '')

.. attribute:: List

    Use this type for inputs, or outputs.

    Lists are also the appropriate input types when fanning in multiple outputs using a
    :py:class:`MultiDependencyDefinition` or the equivalent composition function syntax.

    **Examples:**

    .. code-block:: python

        @solid
        def concat_list(_, xs: List[String]) -> String:
            return ''.join(xs)

        # Python 2
        @solid(
            input_defs=[InputDefinition('xs', dagster_type=List[String])],
            output_defs=[OutputDefinition(dagster_type=String)]
        )
        def concat_list_py2(_, xs) -> String:
            return ''.join(xs)

        # Fanning in multiple outputs
        @solid
        def emit_1(_) -> int:
            return 1

        @solid
        def emit_2(_) -> int:
            return 2

        @solid
        def emit_3(_) -> int:
            return 3

        @solid
        def sum_solid(_, xs: List[int]) -> int:
            return sum(xs)

        @pipeline
        def sum_pipeline():
            sum_solid([emit_1(), emit_2(), emit_3()])


.. attribute:: Dict

    Use this type for inputs, or outputs that are dicts.

    For inputs and outputs, you may optionally specify the key and value types using the square
    brackets syntax for Python typing.

    **Examples:**

    .. code-block:: python

        @solid
        def repeat(_, spec: Dict) -> str:
            return spec['word'] * spec['times']

        # Python 2
        @solid(
            input_defs=[InputDefinition('spec', dagster_type=Dict)],
            output_defs=[OutputDefinition(String)]
        )
        def repeat_py2(_, spec):
            return spec['word'] * spec['times']


.. attribute:: Set

    Use this type for inputs, or outputs that are sets. Alias for
    :py:class:`python:typing.Set`.

    You may optionally specify the inner type using the square brackets syntax for Python typing.

    **Examples:**

    .. code-block:: python

        @solid
        def set_solid(_, set_input: Set[String]) -> List[String]:
            return sorted([x for x in set_input])

        # Python 2
        @solid(
            input_defs=[InputDefinition('set_input', dagster_type=Set[String])],
            output_defs=[OutputDefinition(List[String])],
        )
        def set_solid_py2(_, set_input):
            return sorted([x for x in set_input])

.. attribute:: Tuple

    Use this type for inputs or outputs that are tuples. Alias for
    :py:data:`python:typing.Tuple`.

    You may optionally specify the inner types using the square brackets syntax for Python typing.

    Config values should be passed as a list (in YAML or the Python config dict).

    **Examples:**

    .. code-block:: python

        @solid
        def tuple_solid(_, tuple_input: Tuple[String, Int, Float]) -> List:
            return [x for x in tuple_input]

        # Python 2
        @solid(
            input_defs=[InputDefinition('tuple_input', dagster_type=Tuple[String, Int, Float])],
            output_defs=[OutputDefinition(List)],
        )
        def tuple_solid_py2(_, tuple_input):
            return [x for x in tuple_input]


.. autoclass:: FileHandle
   :members:

.. autoclass:: LocalFileHandle

Making New Types
----------------

.. autoclass:: DagsterType

.. autofunction:: PythonObjectDagsterType

.. autofunction:: dagster_type_loader

.. autofunction:: dagster_type_materializer

.. autofunction:: input_hydration_config

.. autofunction:: output_materialization_config

.. autofunction:: usable_as_dagster_type

.. autofunction:: make_python_type_usable_as_dagster_type

Testing Types
^^^^^^^^^^^^^

.. autofunction:: check_dagster_type
