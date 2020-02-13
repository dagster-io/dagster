.. py:currentmodule:: dagster

Parametrizing solids with inputs
--------------------------------

.. toctree::
  :maxdepth: 1
  :hidden:

So far, we've only seen solids whose behavior is the same every time they're run:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/serial_pipeline.py
   :lines: 6-15
   :linenos:
   :lineno-start: 6
   :caption: serial_pipeline.py

In general, though, rather than relying on hardcoded values like ``dataset_path``, we'd like to be
able to parametrize our solid logic. Appropriately parameterized solids are more testable, and
also more reusable. Consider the following more generic solid:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/inputs.py
   :lines: 6-12
   :linenos:
   :lineno-start: 6
   :caption: inputs.py

Here, rather than hardcoding the value of ``dataset_path``, we use an input, ``csv_path``. It's
easy to see why this is better. We can reuse the same solid in all the different places we
might need to read in a .csv from a filepath. We can test the solid by pointing it at some known
test csv file. And we can use the output of another upstream solid to determine which file to load.

Let's rebuild a pipeline we've seen before, but this time using our newly parameterized solid.

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/inputs.py
   :lines: 1-36
   :linenos:
   :emphasize-lines: 36
   :caption: inputs.py

As you can see above, what's missing from this setup is a way to specify the ``csv_path``
input to our new ``read_csv`` solid in the absence of any upstream solids whose outputs we can
rely on.

Dagster provides the ability to stub inputs to solids that aren't satisfied by the pipeline
topology as part of its flexible configuration facility. We can specify config for a pipeline
execution regardless of which modality we use to execute the pipeline -- the Python API, the Dagit
GUI, or the command line.


Specifying config in the Python API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We previously encountered the :py:func:`execute_pipeline` function. Pipeline configuration is
specified by the second argument to this function, which must be a dict (the "environment dict").

This dict contains all of the user-provided configuration with which to execute a pipeline. As such,
it can have :ref:`a lot of sections <config_schema>`, but we'll only use one of them here:
per-solid configuration, which is specified under the key ``solids``:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/inputs.py
    :linenos:
    :lineno-start: 40
    :lines: 40-44
    :dedent: 4
    :caption: inputs.py

The ``solids`` dict is keyed by solid name, and each solid is configured by a dict that may itself
have several sections. In this case we are only interested in the ``inputs`` section, so
that we can specify the value of the input ``csv_path``.

Now you can pass this environment dict to :py:func:`execute_pipeline`:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/inputs.py
    :linenos:
    :lines: 45-47
    :dedent: 4
    :lineno-start: 45
    :caption: inputs.py


Specifying config using YAML fragments and the dagster CLI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When executing pipelines with the dagster CLI, we'll need to provide the environment dict in a
config file. We use YAML for the file-based representation of an environment dict, but the values
are the same as before:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/inputs_env.yaml
   :language: YAML
   :linenos:
   :caption: inputs_env.yaml

We can pass config files in this format to the dagster CLI tool with the ``-e`` flag.

.. code-block:: console

    $ dagster pipeline execute -f inputs.py -n inputs_pipeline -e inputs_env.yaml

In practice, you might have different sections of your environment dict in different yaml files --
if, for instance, some sections change more often (e.g. in test and prod) while other are more
static. In this case, you can set multiple instances of the ``-e`` flag on CLI invocations, and
the CLI tools will assemble the YAML fragments into a single environment dict.


Writing tests that supply inputs to solids
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You'll frequently want to provide test inputs to solids. You can use :py:func:`execute_pipeline` and
the environment dict to do this, but you can also pass input values directly using the
:py:func:`execute_solid` API. This can be especially useful when it is cumbersome or impossible to
parametrize an input through the environment dict.

For example, we may want to test ``sort_by_calories`` on a controlled data set where we know the
most and least caloric cereals in advance, but without having to flow its input from an upstream
solid implementing a data ingest process.

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/test_inputs.py
   :lines: 9-22
   :lineno-start: 9
   :linenos:
   :caption: test_inputs.py

When we execute this test (e.g., using pytest), we'll be reminded again of one of the reasons why
it's always a good idea to write unit tests, even for the most seemingly trivial components.

.. code-block:: shell
   :emphasize-lines: 17

    ================================ FAILURES =================================
    __________________________ test_sort_by_calories __________________________

        def test_sort_by_calories():
            res = execute_solid(
                sort_by_calories,
                input_values={
                    'cereals': [
                        {'name': 'just_lard', 'calories': '1100'},
                        {'name': 'dry_crust', 'calories': '20'}
                    ]
                }
            )
            assert res.success
            output_value = res.output_value()
    >       assert output_value['most_caloric'] == 'just_lard'
    E       AssertionError: assert {'calories': '20', 'name': 'dry_crust'} == 'just_lard'

    test_inputs.py:18: AssertionError

It looks as though we've forgotten to coerce our calorie counts to integers before sorting by them.
(Alternatively, we could modify our ``load_cereals`` logic to extend the basic functionality
provided by :py:class:`python:csv.DictReader` and add a facility to specify column-wise datatype
conversion.)
