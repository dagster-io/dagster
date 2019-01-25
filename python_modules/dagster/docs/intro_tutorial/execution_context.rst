Execution Context
=================

One of the most important objects in the system is the execution context. The execution
context, the logger, and the resources are threaded throughout the entire computation (
via the ``info`` object passed to user code) and contains handles to logging facilities
and external resources. Interactions with logging systems, databases, and external
clusters (e.g. a Spark cluster) should be managed through these properties of the 
info object.

This provides a powerful layer of indirection that allows a solid to abstract
away its surrounding environment. Using an execution context allows the system and
pipeline infrastructure to provide different implementations for different
environments, giving the engineer the opportunity to design pipelines that
can be executed on your local machine or your CI/CD pipeline as readily as
your production cluster environment.

Logging
~~~~~~~

One of the most basic pipeline-level facilities is logging.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/execution_context.py
   :lines: 1-16
   :caption: execution_context.py

Run this example pipeline in dagit:

.. code-block:: console

    $ dagster pipeline execute -m dagster.tutorials.intro_tutorial.tutorial_repository -n define_repository execution_context_pipeline 

And you'll notice log messages like this:

.. code-block:: console

    2019-01-15 04:59:37 - dagster - ERROR - orig_message="An error occurred." log_message_id="b0cbb1be-e476-4a4e-aaac-a29ddb15309a" run_id="d8f41da0-3825-4ac0-b8e0-4f38ba45b8e0" pipeline="execution_context_pipeline" solid="error_message" solid_definition="error_message"

These log messages are annonated with a bunch of key value pairs that indicate where in the
computation each log message was emitted. This happened because we logged through the execution
context.

Notice that even though the user only logged the message "An error occurred", by routing logging
through the context we are able to provide richer error information -- including the name of the
solid and a timestamp -- in a semi-structured format.

You'll notice that `'A debug message.'` does not appear in the execution logs. This
is because the default log level is ``INFO``, so debug-level messages will not appear.

Let's change that by specifying some config.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/execution_context.yml
   :language: YAML
   :linenos:
   :caption: execution_context.yml

Save it as execution_context.yml and then run:

.. code-block:: console

    $ dagster pipeline execute  \
    -m dagster.tutorials.intro_tutorial.tutorial_repository \
    -n define_repository execution_context_pipeline \
    -e execution_context.yml

You'll see now that debug messages print out to the console.

Although logging is a universally useful case for the execution context, this example only touches
on the capabilities of the context. Any pipeline-level facilities that pipeline authors might want
to make configurable for different environments -- for instance, access to file systems, databases,
or compute substrates -- can be configured using the context.

We'll see how to use some of these other capabilities in the next section:
:doc:`Resources <resources>`.
