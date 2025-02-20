---
title: "Deploying Dagster to Amazon Web Services"
description: To deploy Dagster to AWS, EC2 or ECS can host the Dagster webserver, RDS can store runs and events, and S3 can act as an IO manager.
sidebar_position: 50
---

This guide provides instructions for deploying Dagster on Amazon Web Services (AWS). You can use EC2 or ECS to host the Dagster webserver and the Dagster daemon, RDS to store runs and events, and S3 as an I/O manager to store op inputs and outputs.

## Hosting Dagster on EC2

To host Dagster on a bare VM or in Docker on EC2, see "[Running Dagster as a service](/guides/deploy/deployment-options/deploying-dagster-as-a-service).

## Using RDS for run and event log storage

You can use a hosted RDS PostgreSQL database for your Dagster run/events data by configuring your `dagster.yaml` file:

<CodeExample path="docs_snippets/docs_snippets/deploying/dagster-pg.yaml" />

In this case, you'll want to ensure that:

- You provide the right connection strings for your RDS instance
- The node or container hosting the webserver is able to connect to RDS

Be sure that this file is present and `DAGSTER_HOME` is set on the node where the webserver is running.

:::note

Using RDS for run and event log storage doesn't require that the webserver be running in the cloud. If you're connecting a local webserver instance to a remote RDS storage, verify that your local node is able to connect to RDS.

:::

## Deploying in ECS

<CodeReferenceLink filePath="examples/deploy_ecs" />

The Deploying on ECS example on GitHub demonstrates how to configure the [Docker Compose CLI integration with ECS](https://docs.docker.com/cloud/ecs-integration/) to manage all of the required AWS resources that Dagster needs to run on ECS. The example includes:

- A webserver container for loading and launching jobs
- A `dagster-daemon` container for managing a run queue and submitting runs from schedules and sensors
- A Postgres container for persistent storage
- A container with user job code

The [Dagster instance](/guides/deploy/dagster-instance-configuration) uses the <PyObject section="libraries" module="dagster_aws" object="ecs.EcsRunLauncher" /> to launch each run in its own ECS task.

### Launching runs in ECS

The <PyObject section="libraries" module="dagster_aws" object="ecs.EcsRunLauncher" /> launches an ECS task per run. It assumes that the rest of your Dagster deployment is also running in ECS.

By default, each run's task registers its own task definition. To simplify configuration, these task definitions inherit most of their configuration (networking, cpu, memory, environment, etc.) from the task that launches the run but overrides its container definition with a new command to launch a Dagster run.

When using the <PyObject section="internals" module="dagster._core.run_coordinator" object="DefaultRunCoordinator" />, runs launched via the Dagster UI or GraphQL inherit their task definitions from the webserver task while runs launched from a sensor or schedule inherit their task definitions from the daemon task.

Alternatively, you can define your own task definition in your `dagster.yaml`:

```yaml
run_launcher:
  module: "dagster_aws.ecs"
  class: "EcsRunLauncher"
  config:
    task_definition: "arn:aws:ecs:us-east-1:1234567890:task-definition/my-task-definition:1"
    container_name: "my_container_name"
```

### Customizing CPU, memory, and ephemeral storage in ECS

You can set the `run_launcher.config.run_resources` field to customize the default resources for Dagster runs. For example:

```yaml
run_launcher:
  module: "dagster_aws.ecs"
  class: "EcsRunLauncher"
  config:
    run_resources:
      cpu: "256"
      memory: "512" # In MiB
      ephemeral_storage: 128 # In GiB
```

:::note

Fargate tasks only support [certain combinations of CPU and memory](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-cpu-memory-error.html) and values of ephemeral storage between 21 and 200 GiB (the default is set to 20 GiB).

:::

You can also use job tags to customize the CPU, memory, or ephemeral storage of every run for a particular job:

```py
from dagster import job, op

@op()
def my_op(context):
  context.log.info('running')

@job(
  tags = {
    "ecs/cpu": "256",
    "ecs/memory": "512",
    "ecs/ephemeral_storage": "40",
  }
)
def my_job():
  my_op()
```

If these tags are set, they will override any defaults set on the run launcher.

### Customizing the launched run's task

The <PyObject section="libraries" module="dagster_aws" object="ecs.EcsRunLauncher" /> creates a new task for each run, using the current ECS task to determine network configuration. For example, the launched run will use the same ECS cluster, subnets, security groups, and launch type (e.g. Fargate or EC2).

To adjust the configuration of the launched run's task, set the `run_launcher.config.run_task_kwargs` field to a dictionary with additional key-value pairs that should be passed into the `run_task` boto3 API call. For example, to launch new runs in EC2 from a task running in Fargate, you could apply this configuration:

```yaml
run_launcher:
  module: "dagster_aws.ecs"
  class: "EcsRunLauncher"
  config:
    run_task_kwargs:
      launchType: "EC2"
```

or to set the capacity provider strategy to run in Fargate Spot instances:

```yaml
run_launcher:
  module: "dagster_aws.ecs"
  class: "EcsRunLauncher"
  config:
    run_task_kwargs:
      capacityProviderStrategy:
        - capacityProvider: "FARGATE_SPOT"
```

You can also use the `ecs/run_task_kwargs` tag to customize the ECS task of every run for a particular job:

```py
from dagster import job, op

@op()
def my_op(context):
  context.log.info('running')

@job(
  tags = {
    "ecs/run_task_kwargs": {
      "capacityProviderStrategy": [
        {
          "capacityProvider": "FARGATE_SPOT",
        },
      ],
    },
  }
)
def my_job():
  my_op()
```

Refer to the [boto3 docs](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html#ECS.Client.run_task) for the full set of available arguments to `run_task`. Additionally, note that:

- Keys are in camelCase as they correspond to arguments in boto's API
- All arguments with the exception of `taskDefinition` and `overrides` can be used in `run_launcher.config.run_task_kwargs`. `taskDefinition` can be overridden by configuring the `run_launcher.config.task_definition` field instead.

### Secrets management in ECS

ECS can bind [AWS Secrets Managers secrets as environment variables when runs launch](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/specifying-sensitive-data-secrets.html). By default, Dagster will fetch any Secrets Manager secrets tagged with the `dagster` key and set them as environment variables.

Alternatively, you can set your own tag name in your `dagster.yaml`:

```yaml
run_launcher:
  module: "dagster_aws.ecs"
  class: "EcsRunLauncher"
  config:
    secrets_tag: "my-tag-name"
```

In this example, any secret tagged with a key `my-tag-name` will be included as an environment variable with the name and value as that secret. The value of the tag is ignored.

Additionally, you can pass specific secrets using the [same structure as the ECS API](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_Secret.html):

```yaml
run_launcher:
  module: "dagster_aws.ecs"
  class: "EcsRunLauncher"
  config:
    secrets:
      - name: "MY_API_TOKEN"
        valueFrom: "arn:aws:secretsmanager:us-east-1:123456789012:secret:FOO-AbCdEf:token::"
      - name: "MY_PASSWORD"
        valueFrom: "arn:aws:secretsmanager:us-east-1:123456789012:secret:FOO-AbCdEf:password::"
```

In this example, any secret tagged with `dagster` will be included in the environment. `MY_API_TOKEN` and `MY_PASSWORD` will also be included in the environment.

## Using S3 for I/O management

To enable parallel computation (e.g., with the multiprocessing or Dagster celery executors), you'll need to configure persistent [I/O managers](/guides/build/io-managers/). For example, using an S3 bucket to store data passed between ops.

You'll need to use <PyObject section="libraries" module="dagster_aws" object="s3.s3_pickle_io_manager"/> as your I/O Manager or customize your own persistent I/O managers. Refer to the [I/O managers documentation](/guides/build/io-managers/) for an example.

<CodeExample path="docs_snippets/docs_snippets/deploying/aws/io_manager.py" />

Then, add the following YAML block in your job's config:

<CodeExample path="docs_snippets/docs_snippets/deploying/aws/io_manager.yaml" />

The resource uses `boto` under the hood. If you're accessing your private buckets, you'll need to provide the `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` environment variables or follow [one of the other boto authentication methods](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#configuring-credentials).

With this in place, your job runs will store data passed between ops on S3 in the location `s3://<bucket>/dagster/storage/<job run id>/<op name>.compute`.

