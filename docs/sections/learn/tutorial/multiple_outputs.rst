Multiple Outputs
----------------

So far all of our examples have been solids that have a single output. But
solids can have an arbitrary number of outputs. Downstream solids can
depend on any number of these outputs. Additionally, these outputs do
not *necessarily* have to be fired, therefore unlocking the ability for
downstream solids to be invoked conditionally based on something that
happened during the computation.

Example
~~~~~~~

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/multiple_outputs_yield.py
   :linenos:
   :caption: multiple_outputs.py
   :lines: 5-13 

Above is an example of a solid that returns multiple outputs. It does so by yielding two Output objects.

Notice how ``return_dict_results`` has two outputs. For the first time
we have provided the name argument to an :py:class:`OutputDefinition <dagster.OutputDefinition>`.
Output names must be unique and each result returned by a solid's compute function must have a name
that corresponds to one of these outputs.

With this we can run the pipeline (condensed here for brevity):

.. code-block:: console

    $ dagster pipeline execute \
        -f multiple_outputs.py \
        -n multiple_outputs_yield_pipeline

    ... log spew
    2019-04-05 22:23:37 - dagster - INFO -
            orig_message = "Solid yield_outputs emitted output \"out_one\" value 23"
            ...
        solid_definition = "return_dict_results"
    ...
    2019-04-05 22:23:37 - dagster - INFO -
            orig_message = "Solid yield_outputs emitted output \"out_two\" value 45"
            ...
        solid_definition = "return_dict_results"
    ... more log spew


Conditional Outputs
^^^^^^^^^^^^^^^^^^^

Multiple outputs are the mechanism by which we implement branching or conditional execution. Let's
modify the first solid above to conditionally emit one output or the other based on config
and then execute that pipeline.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/multiple_outputs_conditional.py
    :linenos:
    :caption: multiple_outputs.py

You must create a config file

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/conditional_outputs.yaml
    :linenos:
    :caption: conditional_outputs.yaml

And then run it.

.. code-block:: console

    $ dagster pipeline execute -f multiple_outputs.py \
    -n define_multiple_outputs_step_three_pipeline \
    -e conditional_outputs.yaml

    ... log spew
    2019-04-05 22:29:31 - dagster - INFO -
            orig_message = "Solid conditional emitted output \"out_two\" value 45"
            ...

    2019-04-05 22:29:31 - dagster - INFO -
            orig_message = "Solid conditional did not fire outputs {'out_one'}"
            ...
    ... log spew

Note that we are configuring this solid to *only* emit ``out_two`` which will end up
only triggering ``log_num_squared``. The solid ``log_num`` will never be executed.

Next, let's look at writing :doc:`Reusable Solids <reusable_solids>` so we can avoid duplicating
common data pipeline work.
