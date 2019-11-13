User-defined types
------------------

Note that this section requires Python 3.

We've seen how we can type the inputs and outputs of solids using Python 3's typing system, and
how to use Dagster's built-in config types, such as :py:class:`dagster.String`, to define config
schemas for our solids.

But what about when you want to define your own types?

Let's look back at our simple ``read_csv`` solid.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/inputs_typed.py
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

To do this, we'll use the :py:func:`@dagster_type <dagster.dagster_type>` decorator:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/custom_types.py
   :lines: 3-14
   :linenos:
   :lineno-start: 3
   :caption: custom_types.py

Now we can annotate the rest of our pipeline with our new type:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/custom_types.py
   :lines: 17-43
   :emphasize-lines: 2, 7, 11 
   :linenos:
   :lineno-start: 17
   :caption: custom_types.py


The type metadata now appears in dagit and the system will ensure the input and output to this
solid are indeed instances of SimpleDataFrame. As usual, run:

.. code-block:: console

   $ dagit -f custom_types.py -n custom_type_pipeline

.. thumbnail:: custom_types_figure_one.png

You can see that the output of ``read_csv`` (which by default has the name ``result``) is marked
to be of type ``SimpleDataFrame``.


Custom type checks
^^^^^^^^^^^^^^^^^^

The Dagster framework will fail type checks when a value isn't an instance of the type we're
expecting, e.g., if ``read_csv`` were to return a ``str`` rather than a ``SimpleDataFrame``.

Sometimes we know more about the types of our values, and we'd like to do deeper type checks. For
example, in the case of the ``SimpleDataFrame``, we expect to see a list of OrderedDicts, and for
each of these OrderedDicts to have the same fields, in the same order.

The :py:func:`@dagster_type <dagster.dagster_type>` decorator lets us specify custom type checks
like this.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/custom_types_2.py
   :lines: 3-40
   :linenos:
   :lineno-start: 3
   :emphasize-lines: 4, 35
   :caption: custom_types_2.py

Now, if our solid logic fails to return the right type, we'll see a type check failure. Let's
replace our ``read_csv`` solid with the following bad logic:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/custom_types_2.py
   :lines: 43-49
   :linenos:
   :lineno-start: 43
   :emphasize-lines: 7
   :caption: custom_types_2.py

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

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/inputs_env.yaml
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

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/custom_type_input.yaml
   :language: YAML
   :linenos:
   :caption: custom_type_input.yaml

In order for the Dagster machinery to be able to decode the config value ``{'csv': 'cereal.csv'}``
into an input of the correct ``LessSimpleDataFrame`` value, we need to write what we call an
input hydration config. 

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/custom_types_3.py
   :lines: 44-50
   :linenos:
   :lineno-start: 44
   :caption: custom_types_3.py
   :emphasize-lines: 1

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

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/custom_types_3.py
   :lines: 53-60
   :emphasize-lines: 5
   :linenos:
   :lineno-start: 53
   :caption: custom_types_3.py

Now if you run a pipeline with this solid from dagit you will be able to provide sources for
these inputs via config:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/custom_types_3.py
   :lines: 86-92
   :linenos:
   :dedent: 8
   :lineno-start: 86
   :caption: custom_types_3.py


Metadata and data quality checks
--------------------------------

Custom types can also yield metadata about the type check. For example, in the case of our data
frame, we might want to record the number of rows and columns in the dataset.

User-defined types can provide a metadata function that takes the value being type-checked and
returns a :py:class:`TypeCheck <dagster.TypeCheck>` object containing metadata entries about the
instance of the type that has successfully passed its typecheck.

Let's see how to use this to emit some summary statistics about our DataFrame type:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/custom_types_4.py
   :lines: 55-86
   :linenos:
   :lineno-start: 55
   :emphasize-lines: 1, 29
   :caption: custom_types_4.py

A :py:class:`TypeCheck <dagster.TypeCheck>` is constructed out of a list of
:py:class:`EventMetadataEntry <dagster.EventMetadataEntry>` objects. You should use the
static constructors on :py:class:`EventMetadataEntry <dagster.EventMetadataEntry>`, which are
flexible enough to support arbitrary metadata in JSON or Markdown format.

Dagit knows how to display and archive structured metadata of this kind for future review:

.. thumbnail:: custom_types_figure_two.png


Expectations
^^^^^^^^^^^^

Custom type checks and metadata are appropriate for checking that a value will behave as we expect,
and for collecting summary information about values.

But sometimes we want to make more specific, data- and business logic-dependent assertions about
the semantics of values. It typically isn't appropriate to embed assertions like these into data
types directly.

For one, they will usually vary substantially between instantiations -- for example, we don't
expect all data frames to have the same number of columns, and over-specifying data types (e.g.,
``SixColumnedDataFrame``) makes it difficult for generic logic to work generically (e.g., over all
data frames).

What's more, these additional, deeper semantic assertions are often non-stationary. Typically,
you'll start running a pipeline with certain expectations about the data that you'll see; but
over time, you'll learn more about your data (making your expectations more precise), and the
process in the world that generates your data will shift (making some of your expectations invalid.)

To support this kind of assertion, Dagster includes support for expressing your expectations about
data in solid logic.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/custom_types_5.py
   :lines: 91-133
   :linenos:
   :lineno-start: 91
   :emphasize-lines: 1-3, 31
   :caption: custom_types_5.py

Until now, every solid we've encountered has returned its result value, or ``None``. But solids can
also yield events of various types for side-channel communication about the results of their
computations. We've already encountered the :py:class:`TypeCheck <dagster.TypeCheck>` event, which
is typically yielded by the type machinery (but can also be yielded manually from the body of a
solid's compute function); :py:class:`ExpectationResult <dagster.ExpectationResult>` is another
kind of structured side-channel result that a solid can yield. These extra events don't get passed
to downstream solids and they aren't used to define the data dependencies of a pipeline DAG.

If you're already using the `Great Expectations <https://greatexpectations.io/>`_ library
to express expectations about your data, you may be interested in the ``dagster_ge`` wrapper
library.

This part of this system remains relatively immature, but yielding structured expectation results
from your solid logic means that in future, tools like Dagit will be able to aggregate and track
expectation results, as well as implement sophisticated policy engines to drive alerting and
exception handling on a deep semantic basis.
