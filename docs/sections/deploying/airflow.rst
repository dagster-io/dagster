.. _airflow:

Deploying to Airflow
--------------------

It's also possible to schedule pipelines for execution by compiling them to a format that can be
understood by a third-party scheduling system, and then defining schedules within that system.

This is the approach we use to deploy Dagster pipelines to Airflow (using the
`dagster-airflow <https://github.com/dagster-io/dagster/tree/master/python_modules/dagster-airflow>`__
package).

We don't recommend deploying Dagster pipelines to Airflow in greenfield installations. (We recommend
the built-in `scheduler and partition system <../intro_tutorial/scheduler.html>`_ for scheduling
pipelines, and the `Celery-based executor <celery.html>`_ for large-scale deployments.) But if you
have a large existing Airflow install, this integration will allow you to follow an incremental
adoption path.

Requirements
^^^^^^^^^^^^

- The ``dagster-airflow`` library requires a preexisting Airflow install.

Overview
~~~~~~~~

A Dagster pipeline is first compiled with a set of config options into an execution plan,
and then the individual execution steps are expressed as Airflow tasks using one of a set of custom
wrapper operators (the same operator is used for each task in the DAG) . The resulting DAG can be
deployed to an existing Airflow install and scheduled and monitored using all the tools being
used for existing Airflow pipelines.

We support two modes of execution (each of which uses its own operator):

1. **Uncontainerized [Default]**: Tasks are invoked directly on the Airflow executors.
2. **Containerized**: Tasks are executed in Docker containers.

Running uncontainerized
~~~~~~~~~~~~~~~~~~~~~~~

To define an Airflow DAG corresponding to a Dagster pipeline, you'll put a new Python file defining
your DAG in the directory in which Airflow looks for DAGs -- this is typically ``$AIRFLOW_HOME/dags``.

You can automatically scaffold this file from your Python code with the ``dagster-airflow`` CLI tool.
For example, (provided that the ``dagster_examples`` directory is on your ``PYTHONPATH`` or that
you've pip installed it):

.. code-block:: shell

    $ dagster-airflow scaffold \
        --module-name dagster_examples.toys.sleepy \
        --pipeline-name sleepy_pipeline

This will create a file in your local ``$AIRFLOW_HOME/dags`` folder named ``sleepy_pipeline.py``.

Inside this file, an Airflow DAG corresponding to your Dagster pipeline will be defined using
instances of :py:class:`~dagster_airflow.DagsterPythonOperator` to represent individual execution
steps in the pipeline.

You can now edit this file, supplying the appropriate environment configuration and Airflow
``DEFAULT_ARGS`` for your particular Airflow instance. When Airflow sweeps this directory looking for
DAGs, it will find and execute this code, dynamically creating an Airflow DAG and steps
corresponding to your Dagster pipeline.

Note that an extra ``storage`` parameter will be injected into your environment dict if it is not
set. By default, this will use filesystem storage, but if your Airflow executors are running on
multiple nodes, you will need either to configure this to point at a network filesystem, or consider
an alternative such as S3 or GCS storage.

You will also need to make sure that all of the Python and system requirements that your Dagster
pipeline requires are available in your Airflow execution environment; e.g., if you're running
Airflow on multiple nodes with Celery, this will be true for the Airflow master and all workers.

You will also want to make sure you have a process in place to update your Airflow DAGs, as well as
the Dagster code available to the Airflow workers, whenever your pipelines change.

Using Presets
^^^^^^^^^^^^^

The Airflow scaffold utility also supports using presets when generating an Airflow DAG:

.. code-block:: shell

    $ pip install -e dagster/examples/
    $ dagster-airflow scaffold \
        --module-name dagster_examples.toys.error_monster \
        --pipeline-name error_monster \
        --preset passing

Running Containerized
~~~~~~~~~~~~~~~~~~~~~

Running containerized, we use a :py:class:`~dagster_airflow.DagsterDockerOperator` to wrap Dagster
pipelines.

In order to run containerized Dagster pipelines, you must have Docker running in your
Airflow environment (just as with the ordinary Airflow
:py:class:`DockerOperator <airflow:airflow.operators.docker_operator.DockerOperator>`).

Running in a containerized context requires a persistent intermediate storage layer available to
the Dagster containers, such as a network filesystem, S3, or GCS.

You'll also need to containerize your Dagster repository.

Containerizing a Dagster repository
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Make sure you have Docker installed, and write a Dockerfile like the following:

.. code-block::

    # You may use any base container with a supported Python runtime: 2.7, 3.5, 3.6, or 3.7
    FROM python:3.7

    # Install any OS-level requirements (e.g. using apt, yum, apk, etc.) that the pipelines in your
    # repository require to run
    # RUN apt-get install some-package some-other-package

    # Set environment variables that you'd like to have available in the built image.
    # ENV IMPORTANT_OPTION=yes

    # If you would like to set secrets at build time (with --build-arg), set args
    # ARG super_secret

    # Install dagster_graphql
    RUN pip install dagster_graphql

    # Install any Python requirements that the pipelines in your repository require to run
    ADD /path/to/requirements.txt .
    RUN pip install -r requirements.txt

    # Add your repository.yaml file so that dagster_graphql knows where to look to find your repository,
    # the Python file in which your repository is defined, and any local dependencies (e.g., unpackaged
    # Python files from which your repository definition imports, or local packages that cannot be
    # installed using the requirements.txt).
    ADD /path/to/repository.yaml .
    ADD /path/to/repository_definition.py .
    # ADD /path/to/additional_file.py .

    # The dagster-airflow machinery will use dagster_graphql to execute steps in your pipelines, so we
    # need to run dagster_graphql when the container starts up
    ENTRYPOINT [ "dagster_graphql" ]

Of course, you may expand on this Dockerfile in any way that suits your needs.

Once you've written your Dockerfile, you can build your Docker image. You'll need the name of the
Docker image (``-t``) that contains your repository later so that the docker-airflow machinery knows
which image to run. E.g., if you want your image to be called ``dagster-airflow-demo-repository``:

.. code-block:: shell

    $ docker build -t dagster-airflow-demo-repository -f /path/to/Dockerfile .


If you want your containerized pipeline to be available to Airflow operators running on other
machines (for example, in environments where Airflow workers are running remotely) you'll need to
push your Docker image to a Docker registry so that remote instances of Docker can pull the image by
name, or otherwise ensure that the image is available on remote nodes.

For most production applications, you'll probably want to use a private Docker registry, rather than
the public DockerHub, to store your containerized pipelines.

Defining your pipeline as a containerized Airflow DAG
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As in the uncontainerized case, you'll put a new Python file defining your DAG in the directory in
which Airflow looks for DAGs.

.. code-block:: python

    from dagster_airflow.factory import make_airflow_dag_containerized

    from my_package import define_my_pipeline

    pipeline = define_my_pipeline()

    image = 'dagster-airflow-demo-repository'

    dag, steps = make_airflow_dag_containerized(
        pipeline,
        image,
        environment_dict={'storage': {'filesystem': {'config': {'base_dir': '/tmp'}}}},
        dag_id=None,
        dag_description=None,
        dag_kwargs=None,
        op_kwargs=None
    )

You can pass ``op_kwargs`` through to the the :py:class`~dagster_airflow.DagsterDockerOperator` to
use custom TLS settings, the private registry of your choice, etc., just as you would configure the
ordinary Airflow :py:class:`DockerOperator <airflow:airflow.operators.docker_operator.DockerOperator>`.

Docker bind-mount for filesystem intermediate storage
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, the :py:class`~dagster_airflow.DagsterDockerOperator` will bind-mount ``/tmp`` on the
host into ``/tmp`` in the Docker container. You can control this by setting the ``op_kwargs`` in
:py:func:`~dagster_airflow.make_airflow_dag`. For instance, if you'd prefer to mount ``/host_tmp``
on the host into ``/container_tmp`` in the container, and use this volume for intermediate storage,
you can run:

.. code-block:: python

    dag, steps = make_airflow_dag(
        pipeline,
        image,
        environment_dict={'storage': {'filesystem': {'config' : {'base_dir': '/container_tmp'}}}},
        dag_id=None,
        dag_description=None,
        dag_kwargs=None,
        op_kwargs={'host_tmp_dir': '/host_tmp', 'tmp_dir': '/container_tmp'}
    )

Compatibility
^^^^^^^^^^^^^

Note that Airflow versions less than 1.10.3 are incompatible with Python 3.7+.
