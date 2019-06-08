.. _execution_context:

Execution Context
=================
The execution context is threaded throughout the entire execution of a pipeline via a ``context``
object passed to user code. It wraps the logging system along with external resources, such as object store sessions;
database and data warehouse connections; and access points for computational runtimes (e.g. a Spark context).

Execution contexts provide a powerful layer of indirection that allows a solid to abstract away its
surrounding environment. Using an execution context allows the system and pipeline infrastructure to
provide different implementations for different environments, giving the engineer the opportunity to
design pipelines that can be executed on your local machine or your CI/CD pipeline as readily as
your production cluster environment.

Logging
~~~~~~~

One of the most common places you'll interact with the execution context is when logging:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/execution_context.py
   :lines: 3-20
   :caption: execution_context.py

Run this example pipeline on the dagster CLI:

.. code-block:: console

    $ dagster pipeline execute -f execution_context.py -n execution_context_pipeline

And you'll notice log messages like this:

.. code-block:: console

    2019-04-05 16:54:31 - dagster - ERROR -
            orig_message = "An error occurred."
          log_message_id = "d567e965-31a1-4b99-8b6c-f2f7cfccfcca"
           log_timestamp = "2019-04-05T23:54:31.678344"
                  run_id = "28188449-51bc-4c75-8b70-38cccb8e82e7"
                pipeline = "execution_context_pipeline"
                step_key = "error_message.transform"
                   solid = "error_message"
        solid_definition = "error_message"

These log messages are annotated with a bunch of key value pairs that indicate where in the
computation each log message was emitted. This happened because we logged through the execution
context.

Notice that even though the user only logged the message "An error occurred", by routing execution_context
through the context we are able to provide richer error information -- including the name of the
solid and a timestamp -- in a semi-structured format.

You'll notice that ``'A debug message.'`` does not appear in the execution logs. This
is because the default log level is ``INFO``, so debug-level messages will not appear.

Let's change that by specifying some config.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/execution_context.yaml
   :language: YAML
   :linenos:
   :caption: execution_context.yaml

Save it as execution_context.yaml and then run:

.. code-block:: console

    $ dagster pipeline execute \
    -f execution_context.py \
    -n execution_context_pipeline  \
    -e execution_context.yaml

You'll see now that debug messages print out to the console.

Note that in our YAML fragment, we specified the logger we wanted to configure (in this case, the
default `console` logger).

Although logging is a universally useful case for the execution context, this example only touches
on the capabilities of the context. Any pipeline-level facilities that pipeline authors might want
to make configurable for different environments -- for instance, access to file systems, databases,
or compute substrates -- can be configured using the context.

We'll see how to use some of these other capabilities in the next section:
:doc:`Resources <resources>`.
