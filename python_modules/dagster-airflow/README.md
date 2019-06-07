# dagster-airflow

An Airflow integration for DAGs defined using Dagster. Schedule and monitor your DAGs with Airflow,
defining them using the Dagster abstractions and running them in your Airflow environment or in
fully isolated containers.

### Compatibility

Note that until [AIRFLOW-2876](https://github.com/apache/airflow/pull/3723) is resolved (landed on
master and expected in 1.10.3), Airflow (and, as a consequence, dagster-airflow) is incompatible
with Python 3.7.

# Requirements

dagster-airflow requires an Airflow install.

In order to run containerized Dagster pipelines, you must have Docker running in your Airflow
environment (as for the ordinary Airflow DockerOperator). You will also need to set S3 up to store
intermediate results, and make AWS credentials available inside the Docker container you build on
the ordinary boto3 credential chain.

# Running a Dagster pipeline in Airflow

## Running uncontainerized (DagsterPythonOperator)

We use the DagsterPythonOperator to wrap Dagster solids and define an Airflow DAG that corresponds
to a Dagster pipeline and can run in your Airflow environment uncontainerized.

You will need to make sure that all of the Python and system requirements that your Dagster pipeline
requires are available in your Airflow environment.

To define an Airflow DAG corresponding to a pipeline, you'll put a new Python file defining your DAG
in the directory in which Airflow looks for DAGs -- this is typically `$AIRFLOW_HOME/dags`:

    from dagster_airflow.factory import make_airflow_dag

    from my_package import define_my_pipeline

    pipeline = define_my_pipeline()

    dag, steps = make_airflow_dag(
        pipeline,
        environment_dict={'storage': {'filesystem': {'config': {'base_dir': '/tmp'}}}},
        dag_id=None,
        dag_description=None,
        dag_kwargs=None,
        op_kwargs=None
    )

When Airflow sweeps this directory looking for DAGs, it will find and execute this code, dynamically
creating an Airflow DAG and steps corresponding to your Dagster pipeline. These are ordinary
Airflow objects, and you can do eveything you would expect with them -- for instance, embedding the
DAG as a sub-DAG in another Airflow DAG, or adding dependencies between the dynamically generated
Airflow steps and steps that you define in your own code.

Note the extra `storage` parameter in the environment dict. You can set this for any Dagster
pipeline (and intermediate values will be automatically materialized in either `filesystem` or `s3`
storage), but you **must** set it when converting a pipeline to an Airflow DAG.

## Running containerized (DagsterDockerOperator)

We use the DagsterDockerOperator to define an Airflow DAG that can run in completely isolated
containers corresponding to your Dagster solids. To run containerized, you'll first need to
containerize your repository. Then, you can define your Airflow DAG.

### Containerizing your repository

Make sure you have Docker installed, and write a Dockerfile like the following:

```
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

```
docker build -t dagster-airflow-demo-repository -f /path/to/Dockerfile .
```

If you want your containerized pipeline to be available to Airflow operators running on other
machines (for example, in environments where Airflow workers are running remotely) you'll need to
push your Docker image to a Docker registry so that remote instances of Docker can pull the image
by name.

For most production applications, you'll probably want to use a private Docker registry, rather
than the public DockerHub, to store your containerized pipelines.

## Defining your pipeline as a containerized Airflow DAG

As in the uncontainerized case, you'll put a new Python file defining your DAG in the directory in
which Airflow looks for DAGs.

    from dagster_airflow.factory import make_airflow_dag_containerized

    from my_package import define_my_pipeline

    pipeline = define_my_pipeline()

    image = 'dagster-airflow-demo-repository'

    dag, steps = make_airflow_dag(
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
container. You can control this by setting the `op_kwargs` in make_airflow_dag. For instance,
if you'd prefer to mount `/host_tmp` on the host into `/container_tmp` in the container, and
use this volume for interediate storage, you can run:

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

You can also use S3 for dagster-airflow intermediate storage, and you must use S3 when running
your DAGs with distributed executors.

You'll need to create an S3 bucket, and provide AWS credentials granting read and write permissions
to this bucket within your Docker containers. We recommend that you use credentials for an IAM user
which has the [least privilege](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#grant-least-privilege)
required to access the S3 bucket for dagster-airflow.

You can configure S3 storage as follows:

    {'storage': {'s3': {'s3_bucket': 'my-cool-bucket'}}}

<!-- FIXME give an example with a Sensor and a SubDAG ### Customizing your DAG

Once you've scaffolded your DAG, you can make changes as your business logic requires to take
advantage of Airflow functionality that is external to the logical structure of your pipelines.

FIXME discuss SubDAGs and structure.

For instance, you may want to add Sensors to your Airflow DAGs to change the way that scheduled
DAG runs interact with their environment, or you may want to manually edit DAG args such as
`start_date` or `email`. -->

<!-- FIXME document new test fixtures
# Testing

Docker must be running for the test suite to pass. -->

# Running tests

To run the dagster-airflow tests, you will need to build the dagster-airflow-demo image. Run:

    cd dagster_airflow_tests/test_project
    . build.sh
