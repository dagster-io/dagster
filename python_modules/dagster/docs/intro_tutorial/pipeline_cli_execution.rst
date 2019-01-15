Pipeline CLI Execution
----------------------

Up until now we've been focusing on using the dagit tool for executing pipeline. However, we
also have a CLI utility for use in scripting contexts. It has its own features useful for
production context, which we will go over here.

Just as in the last part of the tutorial, we'll define a pipeline and a repository, and create
a yaml file to tell the CLI tool about the repository.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/pipeline_execution.py
   :linenos:
   :caption: pipeline_execution.py

And now the repository file:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/pipeline_execution_repository.yml
   :linenos:
   :caption: repository.yml

Finally, we'll need to define the pipeline config in a yaml file in order to
execute our pipeline from the command line.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/pipeline_execution_env.yml
   :linenos:
   :caption: env.yml

With these elements in place we can now drive execution from the CLI specifying only the pipeline
name. The tool loads the repository using the `repository.yml` file and looks up the pipeline by
name.

.. code-block:: console

    $ dagster pipeline execute demo_pipeline -e env.yml

Config Splitting
^^^^^^^^^^^^^^^^

Suppose that we want to keep some settings (like our context-level logging config) constant across
a bunch of our pipeline executions, and vary only pipeline-specific settings. It'd be tedious to
copy the broadly-applicable settings into each of our config yamls, and error-prone to try to keep
those copies in sync. So the command line tools allow us to specify more than one yaml file to use
for config.

Let's split up our env.yml into two parts:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/pipeline_execution_env.yml
   :lines: 1-4
   :caption: constant_env.yml

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/pipeline_execution_env.yml
   :lines: 6-9
   :caption: specific_env.yml

Now we can run our pipeline as follows:

.. code-block:: console

    $ dagster pipeline execute part_seven -e constant_env.yml -e specific_env.yml

Order matters when specifying yaml files to use -- values specified in later files will override
values in earlier files, which can be useful. You can also use globs in the CLI arguments to consume
multiple yaml files.

Next, we'll look at defining strongly-typed :doc:`Configuration Schemas <configuration_schemas>`
to guard against bugs and enrich pipeline documentation.
