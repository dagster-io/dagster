Inputs
------
So far we have only demonstrated pipelines whose solids yield hardcoded values and then flow them
through the pipeline. In order to be useful a pipeline must also interact with its external
environment.

Let's return to our hello world example. But this time, we'll make the string
the solid returns be parameterized based on inputs.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/inputs.py
   :lines: 1-38
   :linenos:
   :caption: inputs.py

Note that the input `word` to solid `add_hello_to_word` has no dependency specified. This
means that the operator of the pipeline must specify the input at pipeline execution
time.

Recall that there are three primary ways to execute a pipeline: using the python API, from 
the command line, and from dagit. We'll go through each of these.

That configuration is specified in the second argument to
:py:func:`execute_pipeline <dagster.execute_pipeline>`, which must be a dict. This dict specifies
*all* of the configuration to execute an entire pipeline. It may have many sections, but we're only
using one of them here: per-solid configuration specified under the key ``solids``:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/inputs.py
   :lines: 23-35
   :dedent: 8 

The ``solids`` dict is keyed by solid name, and each solid its own section.
In this case we are only interested in the ``inputs`` section, so that we can
specify that value of the ``word`` input.

The function ``execute_with_another_world`` demonstrates how one would invoke
using the python API.

Next let's use the CLI. In order to do that we'll need to provide the environment
information via a config file. We'll use the same values as before, but in the form
of YAML rather than python dictionaries:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/inputs_env.yml
   :linenos:
   :caption: inputs_env.yml

And now specify that config file via the -e flag.

.. code-block:: console

    $ dagster pipeline execute -f inputs.py \
    -n define_hello_inputs_pipeline -e inputs_env.yml 

As always one can load the pipeline and execute it within dagit.

.. code-block:: console

   $ dagit -f inputs.py -n define_hello_inputs_pipeline
   Serving on http://127.0.0.1:3000

Got to the execute console and you can enter your config like so

.. image:: inputs_figure_one.png

You'll notice that the config editor is auto-completing. As it knows the structure
of the config, the editor can provide rich error information. We can also improve
the experience by appropriately typing the inputs, making everything less error-prone.

Typing
^^^^^^

Right now the inputs and outputs in this solid is totally untyped. (Any input or output
without a type is automatically assigne the ``Any`` type.) This means that mistakes
are often not fixed until the pipeline is executed.

For example, imagine if our environment for our pipeline was:

.. code-block:: YAML

    solids:
        add_hello_to_word:
            inputs:
                word: 2343

If we execute this pipeline this is going to fail and do so at runtime.

Enter this config in dagit and execute and you'll see the transform fail:

.. image:: inputs_figure_two_untyped_execution.png

Click on the red dot on the execution step that failed and a detailed stacktrace will pop up.

.. image:: inputs_figure_three_error_modal.png

It would be better if this error was caught earlier. So let us make the inputs typed.

A user can apply types to inputs and outputs. In this case we just want to type them as the
built-in ``String`` 

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/inputs.py
   :lines: 39-50
   :linenos:
   :caption: inputs.py

By using this input instead we can catch this error prior to execution.

.. image:: inputs_figure_four_error_prechecked.png
