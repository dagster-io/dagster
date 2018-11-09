Repositories and Tools
----------------------

Dagster is a not just a programming model for pipelines, it is also a platform for
tool-building. Included within dagster is a CLI tool, the first tool you'll use
to interact with pipelines.

In previous examples we have specified what file and function a pipeline definition resides
in order to load. However it can get tedious to load individual pipelines. We will want to
be able to browse many pipelines at once and then be able to launch tools against that set
of pipelines without having to specify arguments. This is where repositories and repository
config files come into play.

Dagster has a concept of a repositories which is used to organize a collection of pipelines
(and eventually other concepts). Dagster tools must be pointed to a repository or many repositories
into order to function.

Repostories are declared like this:

.. code-block:: python

    @lambda_solid
    def hello_world():
        pass


    def define_part_six_pipeline():
        return PipelineDefinition(name='part_six', solids=[hello_world])


    def define_part_six_repo():
        return RepositoryDefinition(
            name='part_six_repo',
            pipeline_dict={
                'part_six': define_part_six_pipeline,
            },
        )

Save this file as ``part_six.py``.

Dagster tools are easiest to used when they can operate on a repository. It is particularily convenient
to create a config file containing the location and name of the function to create that repository. This
avoids unnecessary and repetitive typing for CL+I tools. The  current mechanism is to
create a yaml file (default name: 'repository.yml') where you state the module or file and the
function that creates the repository you want to operate on.

.. code-block:: yaml

    repository:
        file: part_six.py
        fn: define_part_six_repo

Save this file as "repository.yml"

Now you should be able to list the pipelines in this repo:

.. code-block:: sh

    $ dagster pipeline list
    Repository part_six_repo
    Pipeline: part_six
    Solids: (Execution Order)
        hello_world


You can also specify a module instead of a file in the repository.yml file.

.. code-block:: yaml

    repository:
        module: some_module 
        fn: define_some_repository 

Dagit
^^^^^

Dagit is an essential tool for managing and visualizing dagster pipelines. Install dagit
via pypi (``pip install dagit``) and then run it on your repository in the same way as
the CLI tool.

.. code-block:: sh

    $ dagit
    Serving on http://localhost:3000

Now navigate to http://localhost:3000 in your web browser and you can visualize your pipelines!
