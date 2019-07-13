Pipeline CLI Execution
----------------------

Up until now we've been focusing on using the dagit tool for executing pipelines. However, we
also have a CLI utility for use in scripting contexts. It has its own features which are useful in
a production context.

Just as in the last part of the tutorial, we'll define a pipeline and a repository, and create
a yaml file to tell the CLI tool about the repository.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/pipeline_cli_execution.py
   :linenos:
   :caption: pipeline_cli_execution.py

And now the repository file:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/pipeline_execution_repository.yaml
   :linenos:
   :language: YAML
   :caption: repository.yaml

Finally, we'll need to define the pipeline config in a yaml file in order to
execute our pipeline from the command line.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/pipeline_execution_env.yaml
   :linenos:
   :language: YAML
   :caption: env.yaml

With these elements in place we can now drive execution from the CLI specifying only the pipeline
name. The tool loads the repository using the ``repository.yaml`` file and looks up the pipeline by
name.

.. code-block:: console

    $ dagster pipeline execute demo_execution_pipeline -e env.yaml

Config Splitting
^^^^^^^^^^^^^^^^

Suppose that we want to keep some settings (like our context-level logging config) constant across
a bunch of our pipeline executions, and vary only pipeline-specific settings. It'd be tedious to
copy the broadly-applicable settings into each of our config yamls, and error-prone to try to keep
those copies in sync. So the command line tools allow us to specify more than one yaml file to use
for config.

Let's split up our env.yaml into two parts:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/constant_env.yaml
   :language: YAML
   :caption: constant_env.yaml

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/specific_env.yaml
   :language: YAML
   :caption: specific_env.yaml

Now we can run our pipeline as follows:

.. code-block:: console

    $ dagster pipeline execute demo_execution_pipeline -e constant_env.yaml -e specific_env.yaml

Order matters when specifying yaml files to use -- values specified in later files will override
values in earlier files, which can be useful. You can also use globs in the CLI arguments to consume
multiple yaml files.

Next, we'll look at how :doc:`User-Defined Types <types>` can enrich documentation and type-safety
in pipelines.
