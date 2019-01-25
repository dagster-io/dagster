# dagster-airflow
An Airflow integration for DAGs defined using Dagster. Schedule and monitor your DAGs with Airflow,
while defining them using the Dagster abstractions and running them in fully isolated containers.

# Packaging a Dagster repository for Airflow
In order to schedule, run, and monitor Dagster pipelines using Airflow, you'll need to take a few
extra steps after you've defined your pipelines in the ordinary way:
1. Containerize your repository
2. Set up an S3 bucket for dagster-airflow
3. Install the dagster-airflow plugin
4. Define your pipeline as an Airflow DAG

## Containerizing your repository
A Dagster repository must be containerized in order to be run using dagster-airflow.

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

# Install Dagit
RUN pip install dagit

# Install Python requirements for your repository
ADD /path/to/requirements.txt .
RUN pip install -r requirements.txt

# Add your repository.yml file so that Dagit knows where to look to find your repository, the
# Python file in which your repository is defined, and any local dependencies (e.g., unpackaged
# Python files from which your repository definition imports, or local packages that cannot be
# installed using the requirements.txt).
ADD /path/to/repository.yml .
ADD /path/to/repository_definition.py .
# ADD /path/to/additional_file.py .

# The dagster-airflow machinery will use Dagit's GraphQL server to execute steps in your
# pipelines, so we need to run Dagit (by default on port 3000) when the container starts up
ENTRYPOINT [ "dagit" ]
EXPOSE 3000
```

Of course, you may expand on this Dockerfile in any way that suits your needs.

Once you've written your Dockerfile, you can build your Docker image. You'll need the name of the
Docker image (`-t`) that contains your repository later so that the docker-airflow machinery knows
which image to run. E.g., if you want your image to be called `dagster-airflow-demo-repository`:

```
docker build -t dagster-airflow-demo-repository -f /path/to/Dockerfile .
```

If you want your containerized pipeline to be available to Airflow DAGs running on other machines,
you'll need to push your Docker image to a Docker registry so that remote instances of Docker can
pull the image.

For most production applications, you'll probably want to use a private Docker registry, rather
than the public DockerHub, to store your containerized pipelines.

## Setting up S3 for dagster-airflow
We need a place to store intermediate results from execution of steps in your pipeline. By default,
dagster-airflow uses Amazon S3 as a lake for this purpose.

You will need to configure an Airflow [Connection](https://airflow.apache.org/howto/manage-connections.html)
with credentials that Airflow can use to connect to AWS. By default, dagster-airflow will try to
use the connection whose `conn_id` is `aws_default`, but we'll see later how you can edit this to
be any value you like.

You'll also need to create an S3 bucket that dagster-airflow can use to store intermediate results.
Make sure that the AWS user for which you've configured an Airflow connection has read and write
permissions on this bucket.

Results will appear in this bucket prefixed by the `run_id` that Airflow generates each time a DAG
is run (and passes to each operator in its `context` argument), so you can easily search for and
examine the results produced by each step in any of your DAG runs.

## Installing the dagster-airflow plugin
Airflow needs to know about our the custom `DagsterOperator` that we'll use to execute steps in
containerized pipelines. We use Airflow's [plugin machinery](https://airflow.apache.org/plugins.html)
to accomplish this.

Airflow looks for plugins in a magic directory, `$AIRFLOW_HOME/plugins/`. The dagster plugin is
defined in `dagster_airflow/dagster_plugin.py`. You can copy that file to the plugin directory
yourself, or just run our convenience CLI tool:

```
dagster-airflow install
```

## Defining your pipeline as an Airflow DAG
Airflow DAGs are declaratively defined in Python files that live in another magic directory,
`$AIRFLOW_HOME/dags/`. Code in these files doesn't do any actual processing -- it's just a way of
telling Airflow about the structure of your pipelines. The pipeline steps themselves are fully
containerized, and the `DagsterOperator` manages their execution.

You don't need to construct any Airflow DAG files yourself in order to run Dagster pipelines in
Airflow -- we've provided facilities to scaffold them for you. This CLI utility takes the ordinary
command-line arguments that the other Dagster CLI tools (e.g., `dagster pipeline execute`) use to
locate pipelines (`-n/--fn-name`, `-m/--module-name`, `-f/--python-file`, `-y/--repository-yaml`,
`-p`) and specify config (`-e/--env`). Note that you must specify both a pipeline and a
corresponding config in order to scaffold the pipeline for Airflow. E.g., from a directory
containing a `repository.yml` file:

```
dagster-airflow scaffold demo_pipeline -e env.yml
```

This will print the autogenerated Airflow DAG definition to stdout. We can also automagically
create a dag definition file at `$AIRFLOW_HOME/dags/{repository_name}_{pipeline_name}.py` by
running:

```
dagster-airflow scaffold demo_pipeline -e env.yml --install
```

### Customizing your DAG
Once you've scaffolded your DAG, you can make changes as your business logic requires to take 
advantage of Airflow functionality that is external to the logical structure of your pipelines.

For instance, you may want to add Sensors to your Airflow DAGs to change the way that scheduled
DAG runs interact with their environment, or you may want to manually edit DAG args such as
`start_date` or `email`.

### Configuring your connection to Amazon S3
If you want to use an Airflow connection other than `aws_default` to connect to S3, you'll need to
edit the lines in the scaffolded definition that read:

```
# Set your S3 connection id here, if you do not want to use the default `aws_default` connection
S3_CONN_ID = "aws_default"
```

Just change S3_CONN_ID to whatever you'd prefer, and the pipeline will use that connection to access
S3.

### Setting up a custom Docker registry


#### An example Airflow DAG definition
For example, consider the following Dagster pipeline definition (which should be familiar from the
Dagster tutorial):

```
from collections import defaultdict

from dagster import (
    DependencyDefinition,
    Dict,
    Field,
    InputDefinition,
    Int,
    PipelineDefinition,
    RepositoryDefinition,
    String,
    lambda_solid,
    solid,
)


@solid(inputs=[InputDefinition('word', String)], config_field=Field(Dict({'factor': Field(Int)})))
def multiply_the_word(info, word):
    return word * info.config['factor']


@lambda_solid(inputs=[InputDefinition('word')])
def count_letters(word):
    counts = defaultdict(int)
    for letter in word:
        counts[letter] += 1
    return dict(counts)


def define_demo_execution_pipeline():
    return PipelineDefinition(
        name='demo_pipeline',
        solids=[multiply_the_word, count_letters],
        dependencies={'count_letters': {'word': DependencyDefinition('multiply_the_word')}},
    )


def define_demo_execution_repo():
    return RepositoryDefinition(
        name='demo_execution_repo', pipeline_dict={'demo_pipeline': define_demo_execution_pipeline}
    )
```

Scaffolding this will produce the following representation of the pipeline as an Airflow DAG:

```
"""Autogenerated by dagster-airflow from pipeline demo_pipeline with env_config:

{
    "context": {"default": {"config": {"log_level": "DEBUG"}}},
    "solids": {
        "multiply_the_word": {"inputs": {"word": {"value": "bar"}}, "config": {"factor": 2}}
    },
}

"""

import datetime

from airflow import DAG
from airflow.operators.dagster_plugin import ModifiedDockerOperator as DagsterOperator

dag = DAG(
    dag_id="demo_pipeline",
    description="***Autogenerated by dagster-airflow***",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "start_date": datetime.datetime(2019, 1, 24, 21, 50, 9, 626934),
        "email": ["airflow@example.com"],
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": datetime.timedelta(0, 300),
    },
)

multiply__the__word_word_input__thunk_task = DagsterOperator(
    step="multiply__the__word_word_input__thunk",
    dag=dag,
    image="dagster-airflow-demo",
    task_id="multiply__the__word_word_input__thunk",
)
multiply__the__word_transform_task = DagsterOperator(
    step="multiply__the__word_transform",
    dag=dag,
    image="dagster-airflow-demo",
    task_id="multiply__the__word_transform",
)
count__letters_transform_task = DagsterOperator(
    step="count__letters_transform",
    dag=dag,
    image="dagster-airflow-demo",
    task_id="count__letters_transform",
)

multiply__the__word_word_input__thunk_task.set_downstream(multiply__the__word_transform_task)
multiply__the__word_transform_task.set_downstream(count__letters_transform_task)
```

Now you can visualize and schedule this DAG in Airflow:

![Example DAG](example_dag.png)


# TODO
- Need to figure out how to scaffold an S3 hook so that the DagsterOperator has access to S3 for
  persisting outputs
- Need to figure out how to scaffold a Docker hook so that we can use a custom registry
