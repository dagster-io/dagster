Execution Context
-----------------

In this tutorial part, we'll go over the other property of the ``info`` parameter,
``context``.

The context is an object of type :py:class:`ExecutionContext`. For every execution
of a particular pipeline, one instance of this context is created, no matter how
many solids are involved. Runtime state or information that is particular to
to a run rather than particular to an individual solid should be associated with
the context.

Let's use the context for one of its core capabilities: logging.

.. code-block:: python

    from dagster import (
        PipelineDefinition,
        solid,
    )

    @solid
    def solid_one(info):
        info.context.info('Something you should know about occurred.')


    @solid
    def solid_two(info):
        info.context.error('An error occurred.')


    def define_step_one_pipeline():
        return PipelineDefinition(solids=[solid_one, solid_two])


Save this as part_five.py and run

.. code-block:: sh

    $ dagster pipeline execute -f part_five.py -n define_step_one_pipeline 
    ...
    2018-09-09 07:14:19 - dagster - ERROR - message="An error occurred." pipeline=<<unnamed>> solid=solid_two
    2018-09-20 17:44:47 - dagster - INFO - orig_message="Something you should know about occurred." log_message_id="c59070a1-f24c-4ac2-a3d4-42f52122e4c5" pipeline="<<unnamed>>" solid="solid_one" solid_definition="solid_one"
    ...

Notice that even though the user only logged the message "An error occurred", by 
routing logging through the context we are able to provide richer error information and then
log that in a semi-structured format. (Note that the order of execution of these
two solids is indeterminate.)

For example, let's change the example by adding a name to the pipeline. (Naming things is good practice).

.. code-block:: python

    def define_step_two_pipeline():
        return PipelineDefinition(name='part_five_step_two', solids=[solid_one, solid_two])

And then run it:

.. code-block:: sh

    $ dagster pipeline execute -f part_five.py -n define_step_two_pipeline
    2018-09-09 07:17:31 - dagster - ERROR - message="An error occurred." pipeline=part_five_step_two solid=solid_two

You'll note that the metadata in the log message now has the pipeline name.

But what about the info message? The default context provided by dagster logs error messages only at 
``INFO`` level to the console. The context must be configured in order to do something that is
not default. Just like we used the configuration system to configure a particular solid, we also
use that same system to configure a context.

.. code-block:: python

    def define_step_three_pipeline():
        return PipelineDefinition(name='part_five_step_three', solids=[solid_one, solid_two])

And now we want to configure this. We use a config file:

.. code-block:: yaml

    context:
        config:
            log_level: DEBUG


Save this as ``step_three.yaml``.

If we re-run the pipeline, you'll see a lot more output.

.. code-block:: sh

    $ dagster pipeline execute -f part_five.py -n define_step_two_pipeline
    ...
    2018-09-09 07:49:51 - dagster - INFO - message="Something you should know about occurred." pipeline=part_five solid=solid_one
    2018-09-09 07:49:51 - dagster - INFO - metric:core_transform_time_ms=0.137 pipeline=part_five solid=solid_one
    2018-09-09 07:49:51 - dagster - DEBUG - message="Executing core transform for solid solid_two." pipeline=part_five solid=solid_two
    2018-09-09 07:49:51 - dagster - ERROR - message="An error occurred." pipeline=part_five solid=solid_two
    ...

This just touches on the capabilities of the execution context. The context is
the system by which pipeline authors actually are able to make their pipelines
executable in different operating contexts (e.g. unit-testing, CI/CD, prod, etc) without
changing business logic.
