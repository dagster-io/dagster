Repositories
------------
Dagster is a not just a programming model for pipelines, it is also a platform for
tool-building. You've already met the dagster and dagit CLI tools, which let you programmatically
run and visualize pipelines.

In previous examples we have specified a file (``-f``) or a module (``-m``) and named a pipeline definition function
(``-n``) in order to tell the CLI tools how to load a pipeline, e.g.:

.. code-block:: console

    $ dagit -f hello_world.py -n define_hello_world_pipeline
    $ dagster pipeline execute -f hello_world.py \
        -n define_hello_world_pipeline

But most of the time, especially when working on long-running projects with other people, we will
want to be able to target many pipelines at once with our tools. 

A **repository** is a collection of pipelines at which dagster tools may be pointed.

Repostories are declared using a new API,
:py:func:`RepositoryDefinition <dagster.RepositoryDefinition>`:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/repos.py
   :linenos:
   :caption: repos.py

If you save this file as ``repos.py``, you can then run the command line tools on it. Try running:

.. code-block:: console

    $ dagit -f repos.py -n define_repo

Now you can see the list of all pipelines in the repo via the dropdown at the top.

.. image:: repos_figure_one.png 

Typing the name of the file and function defining the repository gets tiresome and repetitive, so
let's create a declarative config file with this information to make using the command line tools
easier. Save this file as ``repository.yml``. This is the default name for a repository config file,
although you can tell the CLI tools to use any file you like.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/repos_1.yml
   :linenos:
   :language: YAML
   :caption: repository.yml

Now you should be able to list the pipelines in this repo without all the typing:

.. code-block:: console

    $ dagit 

You can also specify a module instead of a file in the repository.yml file.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/repos_2.yml
   :linenos:
   :language: YAML
   :caption: repository.yml

In the next part of the tutorial, we'll get to know :doc:`Pipeline Execution <pipeline_execution>`
a little better, and learn how to execute pipelines in a repository from the command line by name,
with swappable config.
