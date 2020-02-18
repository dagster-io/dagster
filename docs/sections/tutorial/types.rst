User-defined types
------------------

.. toctree::
  :maxdepth: 1
  :hidden:

Note that this section requires Python 3.

We've seen how we can type the inputs and outputs of solids using Python 3's typing system, and
how to use Dagster's built-in config types, such as :py:class:`dagster.String`, to define config
schemas for our solids.

But what about when you want to define your own types?

Let's look back at our simple ``read_csv`` solid.

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/inputs_typed.py
   :language: python
   :lines: 6-12
   :caption: inputs_typed.py
   :linenos:
   :lineno-start: 6

The ``lines`` object returned by Python's built-in ``csv.DictReader`` is a list of
``collections.OrderedDict``, each of which represents one row of the dataset:

.. code-block:: python

    [
        OrderedDict([
            ('name', '100% Bran'), ('mfr', 'N'), ('type', 'C'), ('calories', '70'), ('protein', '4'),
            ('fat', '1'), ('sodium', '130'), ('carbo', '5'), ('sugars', '6'), ('potass', '280'),
            ('vitamins', '25'), ('shelf', '3'), ('weight', '1'), ('cups', '0.33'),
            ('rating', '68.402973')
        ]),
        OrderedDict([
            ('name', '100% Natural Bran'), ('mfr', 'Q'), ('type', 'C'), ('calories', '120'),
            ('protein', '3'), ('fat', '5'), ('sodium', '15'), ('fiber', '2'), ('carbo', '8'),
            ('sugars', '8'), ('potass', '135'), ('vitamins', '0'), ('shelf', '3'), ('weight', '1'),
            ('cups', '1'), ('rating', '33.983679')
        ]),
        ...
    ]

This is a simple representation of a "data frame", or a table of data. We'd like to be able to
use Dagster's type system to type the output of ``read_csv``, so that we can do type checking when
we construct the pipeline, ensuring that any solid consuming the output of ``read_csv`` expects to
receive a data frame.

To do this, we'll use the :py:class:`DagsterType <dagster.dagster_type>` class:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/custom_types.py
   :lines: 5-9
   :linenos:
   :lineno-start: 5
   :caption: custom_types.py
   :language: python

Now we can annotate the rest of our pipeline with our new type:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/custom_types.py
   :lines: 13-35
   :emphasize-lines: 1, 10
   :linenos:
   :lineno-start: 13
   :caption: custom_types.py
   :language: python

The type metadata now appears in dagit and the system will ensure the input and output to this
solid are indeed instances of SimpleDataFrame. As usual, run:

.. code-block:: console

   $ dagit -f custom_types.py -n custom_type_pipeline

.. thumbnail:: custom_types_figure_one.png

You can see that the output of ``read_csv`` (which by default has the name ``result``) is marked
to be of type ``SimpleDataFrame``.


Complex type checks
^^^^^^^^^^^^^^^^^^^

The Dagster framework will fail type checks when a value isn't an instance of the type we're
expecting, e.g., if ``read_csv`` were to return a ``str`` rather than a ``SimpleDataFrame``.

Sometimes we know more about the types of our values, and we'd like to do deeper type checks. For
example, in the case of the ``SimpleDataFrame``, we expect to see a list of OrderedDicts, and for
each of these OrderedDicts to have the same fields, in the same order.

The type check function allows us to do this.

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/custom_types_2.py
   :lines: 6-29
   :linenos:
   :lineno-start: 6
   :emphasize-lines: 1, 21
   :caption: custom_types_2.py
   :language: python

Now, if our solid logic fails to return the right type, we'll see a type check failure. Let's
replace our ``read_csv`` solid with the following bad logic:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/custom_types_2.py
   :lines: 30-35
   :linenos:
   :lineno-start: 30
   :caption: custom_types_2.py
   :language: python

When we run the pipeline with this solid, we'll see an error like:

.. code-block:: console

    2019-10-12 13:19:19 - dagster - ERROR - custom_type_pipeline - 266c6a93-75e2-46dc-8bd7-d684ce91d0d1 - STEP_FAILURE - Execution of step "bad_read_csv.compute" failed.
                cls_name = "Failure"
                solid = "bad_read_csv"
        solid_definition = "bad_read_csv"
                step_key = "bad_read_csv.compute"
    user_failure_data = {"description": "LessSimpleDataFrame should be a list of OrderedDicts, got <class 'str'> for row 1", "label": "intentional-failure", "metadata_entries": []}

.. input_hydration_config:

Providing input values for custom types in config
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We saw earlier how, when a solid doesn't receive all of its inputs from other solids further
upstream in the pipeline, we can specify its input values in config:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/inputs_env.yaml
   :language: YAML
   :linenos:
   :caption: inputs_env.yaml

The Dagster framework knows how to intepret values provided via config as scalar inputs. In this
case, ``read_csv`` just takes the string representation of the filepath from which it'll read a csv.
But for more complex, custom types, we need to tell Dagster how to interpret config values.

Consider our LessSimpleDataFrame. It might be convenient if Dagster knew automatically how to read a
data frame in from a csv file, without us needing to separate that logic into the ``read_csv``
solid -- especially if we knew the provenance and format of that csv file (e.g., if we were using
standard csvs as an internal interchange format) and didn't need the full configuration surface of
a general purpose ``read_csv`` solid.

What we want to be able to do is write:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/custom_type_input.yaml
   :language: YAML
   :linenos:
   :caption: custom_type_input.yaml

In order for the Dagster machinery to be able to decode the config value ``{'csv': 'cereal.csv'}``
into an input of the correct ``LessSimpleDataFrame`` value, we need to write what we call an
input hydration config.

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/custom_types_3.py
   :lines: 31-37
   :linenos:
   :lineno-start: 31
   :caption: custom_types_3.py
   :emphasize-lines: 1
   :language: python

A function decorated with :py:func:`@input_hydration_config <dagster.input_hydration_config>` should
take the context object, as usual, and a parameter representing the parsed config field. The schema
for this field is defined by the argument to the
:py:func:`@input_hydration_config <dagster.input_hydration_config>` decorator.

Here, we introduce the :py:class:`Selector <dagster.Selector>` type, which lets you specify
mutually exclusive options in config schemas. Here, there's only one option, ``csv``, but you can
imagine a more sophisticated data frame type that might also know how to hydrate its inputs from
other formats and sources, and might have a selector with fields like ``parquet``, ``xlsx``,
``sql``, etc.

Then insert this into the original declaration:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/custom_types_3.py
   :lines: 40-47
   :emphasize-lines: 5
   :linenos:
   :lineno-start: 45
   :caption: custom_types_3.py
   :language: python

Now if you run a pipeline with this solid from dagit you will be able to provide sources for
these inputs via config:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/custom_types_3.py
   :lines: 69-78
   :linenos:
   :lineno-start: 69
   :caption: custom_types_3.py
   :language: python

Testing custom types
^^^^^^^^^^^^^^^^^^^^

As you write your own custom types, you'll also want to set up unit tests that ensure your types
are doing what you expect them to. Dagster includes a utility function,
:py:func:`check_dagster_type <dagster.check_dagster_type>`, that lets you type check any Dagster
type against any value.

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/custom_types_test.py
   :lines: 100-112
   :linenos:
   :lineno-start: 100
   :caption: custom_types_test.py
   :language: python

Well tested library types can be reused across solids and pipelines to provide standardized type
checking within your organization's data applications.

MyPy Compliance
^^^^^^^^^^^^^^^

In cases where DagsterTypes are created that do not have corresponding usable Python types, and
the user wishes to remain mypy compliant, there are two options.

One is using ``InputDefinition`` and ``OutputDefinition`` exclusively for dagster types,
and reserving type annotations for naked Python types *only*. This is verbose, but
is explicit and clear.

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/custom_types_mypy_verbose.py
   :lines: 20-44
   :linenos:
   :lineno-start: 20
   :emphasize-lines: 1-5,13-14
   :caption: custom_types_mypy_verbose.py
   :language: python

If one wishes to use type annotations exclusively but still use dagster types without
a 1:1 python type counterpart, the typechecking behavior must be modified. For this
we recommend using the ``typing.TYPE_CHECKING`` property in the python typing module.

While inelegant, this centralizes boilerplate to the type instantiation, rather than
have it on all places where the type is referenced.

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/custom_types_mypy_typing_trick.py
   :lines: 6-22
   :linenos:
   :lineno-start: 6 
   :emphasize-lines: 1-8
   :caption: custom_types_mypy_typing_trick.py
   :language: python
