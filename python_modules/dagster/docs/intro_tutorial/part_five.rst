Execution Context
-----------------

In addition to its configuration and its inputs, a solid also receives a ``context``
argument. In this tutorial part, we'll go over this ``context`` variable which was
ignored in the previous step of the tutorial.

The context is an object of type :py:class:`ExecutionContext`. For every execution
of a particular pipeline, one instance of this context is created, no matter how
many solids are involved. Runtime state or information that is particular to
to a run rather than particular to an individual solid should be associated with
the context.

Let's use the context for one of its core capabilities: logging.

.. code-block:: python

    from dagster import *

    @solid
    def solid_one(context, _conf):
        context.info('Something you should know about occurred.')


    @solid
    def solid_two(context, _conf):
        context.error('An error occurred.')


    if __name__ == '__main__':
        execute_pipeline(
            PipelineDefinition(solids=[solid_one, solid_two])
        )


Save this as part_five.py and run

.. code-block:: sh

    $ python3 part_five.py
    2018-09-09 07:14:19 - dagster - ERROR - message="An error occurred." pipeline=<<unnamed>> solid=solid_two

Notice that even though the user only logged the message "An error occurred", by 
routing logging through the context we are able to provide richer error information and then
log that in a semi-structured format.

For example, let's change the example so that the pipeline has a name. (This is good practice anyways).

.. code-block:: python

    execute_pipeline(
        PipelineDefinition(
            name='part_five',
            solids=[solid_one, solid_two]
        )
    )

And then run it:

.. code-block:: sh

    $ python3 part_five.py
    2018-09-09 07:17:31 - dagster - ERROR - message="An error occurred." pipeline=part_five solid=solid_two

You'll note that the metadata in the log message now has the pipeline name.

But what about the info message? The default context provided by dagster logs error messages only at 
``ERROR`` level to the console. The context must be configured inorder to do something that is
not default. Just like we used the configuration system to configure a particular solid, we also
use that same system to configure a context.


.. code-block:: python

    execute_pipeline(
        PipelineDefinition(
            name='part_five',
            solids=[solid_one, solid_two]
        ),
        config.Environment(
            context=config.Context(config={'log_level': 'DEBUG'})
        ),
    )

If we re-run the pipeline, you'll see a lot more output.

.. code-block:: sh

    $ python3 part_five.py
    ...
    2018-09-09 07:49:51 - dagster - INFO - message="Something you should know about occurred." pipeline=part_five solid=solid_one
    2018-09-09 07:49:51 - dagster - INFO - metric:core_transform_time_ms=0.137 pipeline=part_five solid=solid_one
    2018-09-09 07:49:51 - dagster - DEBUG - message="Executing core transform for solid solid_two." pipeline=part_five solid=solid_two
    2018-09-09 07:49:51 - dagster - ERROR - message="An error occurred." pipeline=part_five solid=solid_two
    ...

This just touches on the capabilities of the execution context. The context will end up
being the system by which pipeline authors actually are able to make their pipelines
executable in different operating contexts (e.g. unit-testing, CI/CD, prod, etc) without
changing business logic.
