Logging through the Execution Context
=====================================

One of the most basic pipeline-level facilities is logging:

.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/logging.py
   :lines: 1-16
   :caption: logging.py

Run this example pipeline in dagit:

.. code-block:: console

    $ dagster pipeline execute -m dagster.tutorials.intro_tutorial.tutorial_repository -n define_repository logging_pipeline 

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

Notice that even though the user only logged the message "An error occurred", by routing logging
through the context we are able to provide richer error information -- including the name of the
solid and a timestamp -- in a semi-structured format.

You'll notice that ``'A debug message.'`` does not appear in the execution logs. This
is because the default log level is ``INFO``, so debug-level messages will not appear.

Let's change that by specifying some config.

.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/logging.yml
   :language: YAML
   :linenos:
   :caption: logging.yml

Save it as logging.yml and then run:

.. code-block:: console

    $ dagster pipeline execute  \
    -m dagster.tutorials.intro_tutorial.tutorial_repository \
    -n define_repository logging_pipeline \
    -e logging.yml

You'll see now that debug messages print out to the console.

Note that in our YAML fragment, we specified the logger we wanted to configure (in this case, the
default `console` logger).

Although logging is a universally useful case for the execution context, this example only touches
on the capabilities of the context. Any pipeline-level facilities that pipeline authors might want
to make configurable for different environments -- for instance, access to file systems, databases,
or compute substrates -- can be configured using the context.

We'll see how to use some of these other capabilities in the next section:
:doc:`Resources <resources>`.
