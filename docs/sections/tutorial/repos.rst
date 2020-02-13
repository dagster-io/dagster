Organizing pipelines in repositories
------------------------------------

In all of the examples we've seen so far, we've specified a file (``-f``) or a module (``-m``) and
named a pipeline definition function (``-n``) in order to tell the CLI tools how to load a pipeline,
e.g.:

.. code-block:: console

    $ dagit -f hello_cereal.py -n hello_cereal_pipeline
    $ dagster pipeline execute -f hello_cereal.py \
        -n hello_cereal_pipeline

But most of the time, especially when working on long-running projects with other people, we will
want to be able to target many pipelines at once with our tools.

Dagster provides the concept of a repository, a collection of pipelines that the Dagster tools can
target as a whole. Repositories are declared using the
:py:func:`RepositoryDefinition <dagster.RepositoryDefinition>` API as follows:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/repos.py
   :linenos:
   :lines: 14-24
   :lineno-start: 14
   :caption: repos.py

Note that the name of the pipeline in the ``RepositoryDefinition`` must match the name we declared
for it in its ``pipeline`` (the default is the function name). Don't worry, if these names don't
match, you'll see a helpful error message.

If you save this file as ``repos.py``, you can then run the command line tools on it. Try running:

.. code-block:: console

    $ dagit -f repos.py -n define_repo

Now you can see the list of all pipelines in the repo via the dropdown at the top:

.. thumbnail:: repos.png

Typing the name of the file and function defining the repository gets tiresome and repetitive, so
let's create a declarative config file with this information to make using the command line tools
easier. Save this file as ``repository.yaml``. This is the default name for a repository config file,
although you can tell the CLI tools to use any file you like with the ``-y`` flag.

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/repository.yaml
   :language: YAML
   :caption: repository.yaml

Now you should be able to list the pipelines in this repo without all the typing:

.. code-block:: console

    $ dagit
