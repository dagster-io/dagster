Pipeline Execution
------------------
Just as in the last part of the tutorial, we'll define a pipeline and a repository, and create
a yaml file to tell the CLI tool about the repository.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/part_seven.py
   :linenos:
   :caption: part_seven.py

And now the repository file:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/part_seven_repository.yml
   :linenos:
   :caption: repository.yml

Now, just as in part five, we'll need to define the pipeline config in a yaml file in order to
execute our pipeline from the command line.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/part_seven_env.yml
   :linenos:
   :caption: env.yml

With these elements in place we can now drive execution from the CLI specifying only the pipeline
name. The tool loads the repository using the repository.yml file and looks up the pipeline by name.

.. code-block:: console

    $ dagster pipeline execute part_seven -e env.yml
