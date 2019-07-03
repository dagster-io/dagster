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
        -f multiple_outputs_yield.py \
        -n multiple_outputs_yield_pipeline

    2019-07-03 15:19:54 - dagster - INFO -
            orig_message = "Solid 'yield_outputs' emitted output 'out_one' value 23"
          log_message_id = "3e223b44-3b1d-436a-bda3-4b36421893ca"
           log_timestamp = "2019-07-03T22:19:54.854159"
                  run_id = "68fd5aa6-a788-4ad9-922d-c288050c0c1f"
                pipeline = "multiple_outputs_yield_pipeline"
    execution_epoch_time = 1562192394.848578
                step_key = "yield_outputs.compute"
                   solid = "yield_outputs"
        solid_definition = "yield_outputs"
    2019-07-03 15:19:54 - dagster - INFO -
            orig_message = "Solid 'yield_outputs' emitted output 'out_two' value 45"
          log_message_id = "ec12d827-efc3-4db1-ade7-2821bbd99133"
           log_timestamp = "2019-07-03T22:19:54.854632"
                  run_id = "68fd5aa6-a788-4ad9-922d-c288050c0c1f"
                pipeline = "multiple_outputs_yield_pipeline"
    execution_epoch_time = 1562192394.848578
                step_key = "yield_outputs.compute"
                   solid = "yield_outputs"
        solid_definition = "yield_outputs"


Conditional Outputs
^^^^^^^^^^^^^^^^^^^

Multiple outputs are the mechanism by which we implement branching or conditional execution. Let's
modify the first solid above to conditionally emit one output or the other based on config
and then execute that pipeline.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/multiple_outputs_conditional.py
    :linenos:
    :caption: multiple_outputs_conditional.py

You must create a config file

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/conditional_outputs.yaml
    :linenos:
    :caption: conditional_outputs.yaml

And then run it.

.. code-block:: console

    $ dagster pipeline execute -f multiple_outputs_conditional.py \
    -n multiple_outputs_conditional_pipeline \
    -e conditional_outputs.yaml

    2019-07-03 15:22:55 - dagster - INFO -
            orig_message = "Solid 'conditional' emitted output 'out_two' value 45"
          log_message_id = "c3baeee8-f642-4f67-a649-50e2e0985782"
           log_timestamp = "2019-07-03T22:22:55.173293"
                  run_id = "16a7f229-ed66-46ba-ab47-d3725639662c"
                pipeline = "multiple_outputs_conditional_pipeline"
    execution_epoch_time = 1562192575.166923
                step_key = "conditional.compute"
                   solid = "conditional"
        solid_definition = "conditional"
    2019-07-03 15:22:55 - dagster - INFO -
            orig_message = "Solid conditional did not fire outputs {'out_one'}"
          log_message_id = "e07b2b81-708d-4b83-9c0c-69698bb8eb26"
           log_timestamp = "2019-07-03T22:22:55.173857"
                  run_id = "16a7f229-ed66-46ba-ab47-d3725639662c"
                pipeline = "multiple_outputs_conditional_pipeline"
    execution_epoch_time = 1562192575.166923
                step_key = "conditional.compute"
                   solid = "conditional"
        solid_definition = "conditional"

Note that we are configuring this solid to *only* emit ``out_two`` which will end up
only triggering ``log_num_squared``. The solid ``log_num`` will never be executed.

Next, let's look at :doc:`Reusing Solids <reusing_solids>` so we can avoid duplicating
common data pipeline work.
