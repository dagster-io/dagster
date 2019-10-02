# Deploying to Airflow

## Introduction

Dagster is designed for incremental adoption, and to work with all of your existing Airflow
infrastructure.

You can use all of Dagster's features and abstractions—the programming model, type systems, etc.
while scheduling, executing, and monitoring your Dagster pipelines with Airflow, right alongside all
of your existing Airflow DAGs.

This integration is fairly simple. As with vanilla Dagster pipeline execution, Dagster compiles your
pipeline and configuration together into an execution plan. In the case of Airflow, these execution
plans are then mapped to a DAG, with a bijection between solids and Airflow operators.

### Requirements

- The `dagster-airflow` library requires an Airflow install.

### Overview

We support two modes of execution:

1. **Uncontainerized [Default]**: Tasks are invoked directly on the Airflow executors.
2. **Containerized**: Tasks are executed in Docker containers.

Instructions on setting up Dagster + Airflow in these modes are provided in the next two sections.

## Running Uncontainerized

To define an Airflow DAG corresponding to a Dagster pipeline, you'll put a new Python file defining
your DAG in the directory in which Airflow looks for DAGs -- this is typically `$AIRFLOW_HOME/dags`.

You can automatically scaffold this file from your Python code with the `dagster-airflow` CLI tool.
For example, if you've checked out Dagster to `$DAGSTER_ROOT`:

```bash
pip install -e dagster/examples/
dagster-airflow scaffold \
    --module-name dagster_examples.toys.sleepy \
    --pipeline-name sleepy_pipeline
```

This will create a file in your local `$AIRFLOW_HOME/dags` folder named `sleepy_pipeline.py`. You
can simply edit this file, supplying the appropriate environment configuration and Airflow
`DEFAULT_ARGS` for your particular Airflow instance. When Airflow sweeps this directory looking for
DAGs, it will find and execute this code, dynamically creating an Airflow DAG and steps
corresponding to your Dagster pipeline.

These are ordinary Airflow objects, and you can do eveything you would expect with them—for example,
adding `ExternalTaskSensor` dependencies between the dynamically generated Airflow operators in this
DAG and operators that you define in your other existing Airflow DAGs.

### Using Presets
The Airflow scaffold utility also supports using presets when generating an Airflow DAG:

```bash
pip install -e dagster/examples/
dagster-airflow scaffold \
    --module-name dagster_examples.toys.error_monster \
    --pipeline-name error_monster \
    --preset passing
```

### Implementation Notes

- We use a `DagsterPythonOperator` to wrap Dagster solids and define an Airflow DAG that corresponds
  to a Dagster pipeline and can run in your Airflow environment uncontainerized.
- Note that an extra `storage` parameter will be injected into your environment dict if it is not set.
  You can set this for any Dagster pipeline (and intermediate values will be automatically
  materialized in either `filesystem` or `s3` storage), but you **must** set it when converting a
  pipeline to an Airflow DAG.
- To execute your pipeline, you will also need to make sure that all of the Python and system
  requirements that your Dagster pipeline requires are available in your Airflow environment; if
  you're running Airflow on multiple nodes with the Celery executor, this will be true for the Airflow
  master and all workers.

## Running Containerized

We use a `DagsterDockerOperator`, based on the ordinary Airflow `DockerOperator`, to wrap Dagster
pipelines. In order to run containerized Dagster pipelines, you must have Docker running in your
Airflow environment (the same as for the ordinary Airflow `DockerOperator`).

During execution, Dagster caches and transfers intermediate state between execution steps. This
feature enables quick re-execution of execution steps from the Dagit UI.

When running uncontainerized on a single machine, this transfer can take place in memory or on the
local file system, but running in a containerized context requires a persistent intermediate storage
layer available to the Dagster containers.

Presently, we support S3 for persisting this intermediate state. To use it, you'll just need to set
up an S3 bucket and expose AWS credentials via the usual Boto credentials chain. We plan on
supporting other persistence targets like GCS, HDFS, and NFS in the future—please reach out to us if
you require a different intermediate store for your use case!

We use the `DagsterDockerOperator` to define an Airflow DAG that can run in completely isolated
containers corresponding to your Dagster solids. To run containerized, you'll first need to
containerize your repository. Then, you can define your Airflow DAG.

### Containerizing your repository

Make sure you have Docker installed, and write a Dockerfile like the following:

```Dockerfile
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
```

Of course, you may expand on this Dockerfile in any way that suits your needs.

Once you've written your Dockerfile, you can build your Docker image. You'll need the name of the
Docker image (`-t`) that contains your repository later so that the docker-airflow machinery knows
which image to run. E.g., if you want your image to be called `dagster-airflow-demo-repository`:

```bash
docker build -t dagster-airflow-demo-repository -f /path/to/Dockerfile .
```

If you want your containerized pipeline to be available to Airflow operators running on other
machines (for example, in environments where Airflow workers are running remotely) you'll need to
push your Docker image to a Docker registry so that remote instances of Docker can pull the image by
name.

For most production applications, you'll probably want to use a private Docker registry, rather than
the public DockerHub, to store your containerized pipelines.

### Defining your pipeline as a containerized Airflow DAG

As in the uncontainerized case, you'll put a new Python file defining your DAG in the directory in
which Airflow looks for DAGs.

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

You can pass `op_kwargs` through to the the DagsterDockerOperator to use custom TLS settings, the
private registry of your choice, etc., just as you would configure the ordinary Airflow
DockerOperator.

### Docker bind-mount for filesystem intermediate storage

By default, the DagsterDockerOperator will bind-mount `/tmp` on the host into `/tmp` in the Docker
container. You can control this by setting the `op_kwargs` in make_airflow_dag. For instance, if
you'd prefer to mount `/host_tmp` on the host into `/container_tmp` in the container, and use this
volume for intermediate storage, you can run:

    dag, steps = make_airflow_dag(
        pipeline,
        image,
        environment_dict={'storage': {'filesystem': {'config' : {'base_dir': '/container_tmp'}}}},
        dag_id=None,
        dag_description=None,
        dag_kwargs=None,
        op_kwargs={'host_tmp_dir': '/host_tmp', 'tmp_dir': '/container_tmp'}
    )

### Using S3 with dagster-airflow

You can also use S3 for dagster-airflow intermediate storage, and you must use S3 when running your
DAGs with distributed executors.

You'll need to create an S3 bucket, and provide AWS credentials granting read and write permissions
to this bucket within your Docker containers. We recommend that you use credentials for an IAM user
which has the [least
privilege](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#grant-least-privilege)
required to access the S3 bucket for dagster-airflow.

You can configure S3 storage as follows:

    {'storage': {'s3': {'s3_bucket': 'my-cool-bucket'}}}

### Compatibility

Note that Airflow versions less than 1.10.3 are incompatible with Python 3.7+.
