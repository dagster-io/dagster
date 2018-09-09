Repositories and Tools
----------------------

Dagster is a not just a programming model for pipeliens, it is also a platform for
tool-building. Included within dagster is a CLI tool, the first tool you'll use
to interact with pipelines.

In order for a tool to interact with a pipeline, it must be made aware of the pipelines.

Dagster has a concept of a repositories which is used to organize a collection of pipelines
(and eventually other concepts). Dagster tools are pointed a repository or many repositories
into order to function.

Repostories are declared like the following:

.. code-block:: python

    from dagster import *

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

Save this file as "part_six.py"

For tools to operate they must be able to access and create a repo. The current mechanism is to
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


For a given project with 1 or more pipelines, you should define a repository for that
project so it is accessible via tools. If you are writing code within a python module
as opposed to a standalone file you can (and should) load the repository via that module.

To do that you can specify a module instead of a file in the repository.yml file.

.. code-block:: yaml

    # this works if you this works in your python enviroment
    # from some_module import define_some_repository
    repository:
        module: some_module 
        fn: define_some_repository 

Dagit
^^^^^

Dagit is an essential tool for managaging and visualizing dagster pipelines. Install dagit
via pypi (``pip install dagit``) and then run it on your repository in the same way as
the CLI tool.

.. code-block:: sh

    $ dagit
    Serving on http://localhost:3000

Now navigate to http:://localhost:3000 in your web browser and you can visualize your pipelines!
