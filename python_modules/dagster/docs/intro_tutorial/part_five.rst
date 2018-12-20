Execution Context
-----------------
We use **configuration** to set parameters on a per-solid basis. The **execution context** lets
us set parameters for the entire pipeline.

The execution context is exposed to individual solids as the ``context`` property of the ``info``
object. The context is an object of type :py:class:`ExecutionContext <dagster.ExecutionContext>`.
For every execution of a particular pipeline, one instance of this context is created, no matter how
many solids are involved. Runtime state or information that is particular to a single execution,
rather than particular to an individual solid, should be associated with the context.

One of the most basic pipeline-level facilities is logging.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/part_five.py
   :lines: 1-2,4-21
   :caption: part_five.py

If you run this either on the command line or in dagit, you'll see our new error message pop up
in the logs.

.. code-block:: console

    $ dagster pipeline execute -f part_five.py -n define_execution_context_pipeline_step_one
    ...
    2018-12-17 16:06:53 - dagster - ERROR - orig_message="An error occurred." log_message_id="89211a12-4f75-4aa0-a1d6-786032641986" run_id="40a9b608-c98f-4200-9f4a-aab70a2cb603" pipeline="<<unnamed>>" solid="solid_two" solid_definition="solid_two"
    ...

Notice that even though the user only logged the message "An error occurred", by routing logging
through the context we are able to provide richer error information -- including the name of the
solid and a timestamp -- in a semi-structured format. (Note that the order of execution of these
two solids is indeterminate -- they don't depend on each other.)

Let's change the example by adding a name to the pipeline. (Naming things is good practice).

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/part_five.py
   :lines: 24-25
   :caption: part_five.py

And then run it:

.. code-block:: console

    $ dagster pipeline execute -f part_five.py -n define_execution_context_pipeline_step_two
    ...
    2018-12-17 16:06:53 - dagster - ERROR - orig_message="An error occurred." log_message_id="89211a12-4f75-4aa0-a1d6-786032641986" run_id="40a9b608-c98f-4200-9f4a-aab70a2cb603" pipeline="part_five_pipeline" solid="solid_two" solid_definition="solid_two"
    ...

You'll note that the metadata in the log message now includes the pipeline name.

But what about the ``DEBUG`` message in ``solid_one``? The default context provided by dagster
logs error messages to the console only at the ``INFO`` level or above. (In dagit, you can always
filter error messages at any level.) In order to print ``DEBUG`` messages to the console, we'll
use the configuration system again -- this time, to configure the context rather than an individual
solid.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/part_five.py
   :lines: 28-29
   :caption: part_five.py

We could use the same config syntax as before in order to configure the pipeline:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/part_five.py
   :lines: 3,30-31,33-44
   :dedent: 4

But instead, this time we'll use a yaml file to declaratively specify our config. Separating
config into external files is a nice pattern because it allows users who might not be comfortable
in a general-purpose programming environment like Python to do meaningful work configuring
pipelines in a restricted DSL. Fragments of config expressed in yaml can also be reused (for
instance, pipeline-level config that is common across many projects) or kept out of source control
(for instance, credentials or information specific to a developer environment) and combined at
pipeline execution time.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/part_five.yaml
   :caption: part_five.yaml

If we re-run the pipeline, you'll see a lot more output, including our custom ``DEBUG`` message.

.. code-block:: console

    $ dagster pipeline execute -f part_five.py -n define_execution_context_pipeline_step_three -e part_five.yaml
    ...
    2018-12-17 17:18:06 - dagster - DEBUG - orig_message="A debug message." log_message_id="497c9d47-571a-44f6-a04c-8f24049b0f66" run_id="5b233906-9b36-4f15-a220-a850a1643b9f" pipeline="part_five_pipeline" solid="solid_one" solid_definition="solid_one"
    ...

Although logging is a universal case for the execution context, this example only touches on the
capabilities of the context. Any pipeline-level facilities that pipeline authors might want to
make configurable for different environments -- for instance, access to file systems, databases,
or compute substrates -- can be configured using the context. This is how pipelines can be made
executable in different operating environments (e.g. unit-testing, CI/CD, prod, etc) without
changing business logic.

Next, we'll see how to declare :doc:`Repositories <part_six>` -- groups of pipelines -- so that
the dagster tools can manage them.
