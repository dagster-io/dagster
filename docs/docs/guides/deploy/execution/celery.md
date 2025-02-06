---
title: "Executing Dagster on Celery"
sidebar_position: 700
---

[Celery](https://docs.celeryq.dev/) is an open-source Python distributed task queue system, with support for a variety of queues (brokers) and result persistence strategies (backends).

The `dagster-celery` executor uses Celery to satisfy three common requirements when running jobs in production:

- Parallel execution capacity that scales horizontally across multiple compute nodes.
- Separate queues to isolate execution and control external resource usage at the op level.
- Priority-based execution at the op level.

The dagster-celery executor compiles a job and its associated configuration into a concrete execution plan, and then submits each execution step to the broker as a separate Celery task. The dagster-celery workers then pick up tasks from the queues to which they are subscribed, according to the priorities assigned to each task, and execute the steps to which the tasks correspond.

## Prerequisites

To complete the steps in this guide, you'll need to install `dagster` and `dagster-celery`:

  ```shell
  pip install dagster dagster-celery
  ```

- You will also need **a running broker**, which is required to run the Celery executor. Refer to the [Celery documentation](https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html#choosing-a-broker) for more info about choosing a broker.

## Part 1: Write and execute a job

To demonstrate, we'll start by constructing a parallel toy job that uses the Celery executor.

In your Dagster project, create a new file named `celery_job.py` and paste in the following:

<CodeExample path="docs_snippets/docs_snippets/deploying/celery_job.py" />

Now, run the Celery executor. In our case, we're running RabbitMQ as our broker. With Docker, this is something like the following:

```shell
docker run -p 5672:5672 rabbitmq:3.8.2
```

You'll also need to run a Celery worker to execute tasks. From the same directory where you saved the `celery_job.py` file, run:

```shell
dagster-celery worker start -A dagster_celery.app
```

Next, execute this job with Celery by running the following:

```shell
dagster dev -f celery_job.py
```

Now you can execute the parallel job from the [Dagster UI](/guides/operate/webserver).

## Part 2: Ensuring workers are in sync

In Part 1, we took a few shortcuts:

- **We ran a single Celery worker on the same node as the Dagster webserver.** This allowed us to share local ephemeral run storage and event log storage between them and use the filesystem I/O manager to exchange values between the worker's task executions.
- **We ran the Celery worker in the same directory as `celery_job.py`**. This meant that our Dagster code was available to both the webserver and the worker, specifically that they could both find the job definition in the same file (`-f celery_job.py`)

In production, more configuration is required.

### Step 1: Configure persistent run and event log storage

First, configure appropriate persistent run and event log storage, e.g., `PostgresRunStorage` and `PostgresEventLogStorage` on your [Dagster instance](/guides/deploy/dagster-instance-configuration) (via [`dagster.yaml`](/guides/deploy/dagster-yaml)). This allows the webserver and workers to communicate information about the run and events with each other. Refer to the [Dagster storage section of the Dagster instance documentation](/guides/deploy/dagster-instance-configuration#dagster-storage) for information on how to do this.

:::note

The same instance config must be present in the webserver's environment and in the workers' environments. Refer to the [Dagster instance](/guides/deploy/dagster-instance-configuration) documentation for more information.

:::

### Step 2: Configure a persistent I/O manager

When using the Celery executor for job runs, you'll need to use storage that's accessible from all nodes where Celery workers are running. This is necessary because data is exchanged between ops that might be in different worker processes, possibly on different nodes. Common options for such accessible storage include an Amazon S3 or Google Cloud Storage (GCS) bucket or an NFS mount.

To do this, include an appropriate I/O manager in the job's resource. For example, any of the following I/O managers would be suitable:

- <PyObject section="libraries" module="dagster_aws" object="s3.s3_pickle_io_manager" />
- <PyObject section="libraries" module="dagster_azure" object="adls2.adls2_pickle_io_manager" />
- <PyObject section="libraries" module="dagster_gcp" object="gcs_pickle_io_manager" />

### Step 3: Supply executor and worker config

If using custom config for your runs - such as using a different Celery broker URL or backend - you'll need to ensure that your workers start up with the config.

To do this:

1. Make sure the engine config is in a YAML file accessible to the workers
2. Start the workers with the `-y` parameter as follows:

   ```shell
   dagster-celery worker start -y /path/to/celery_config.yaml
   ```

### Step 4: Ensure Dagster code is accessible

Lastly, you'll need to make sure that the Dagster code you want the workers to execute is:

1. Present in the workers' environment, and
2. The code is in sync with the code present on the node running the webserver

The easiest way to do this is typically to package the code into a Python module and to configure your project's [`workspace.yaml`](/guides/deploy/code-locations/workspace-yaml) to have the webserver load from that module.

In Part 1, we accomplished this by starting the webserver with the `-f` parameter:

```shell
dagster dev -f celery_job.py
```

This told the webserver the file containing the job (`celery_job.py`) and to start the Celery worker from the same point in the file system, so the job was available in the same location.

## Additional information

### Using the dagster-celery CLI

In the walkthrough, we started our workers using the `dagster-celery` CLI instead of invoking Celery directly. This CLI is intended as a convenient wrapper that shields you from the complexity of full Celery configuration. **Note**: It's still possible to directly start Celery workers - let us know if your use case requires this.

For all of these commands, it's essential that your broker is running.

```shell
## Start new workers
dagster-celery worker start

## View running workers
dagster-celery worker list

## Terminate workers
dagster-celery worker terminate
```

:::note

If running Celery with custom config, include the config file path in these commands to ensure workers start with the correct config. Refer to [Step 3](#step-3-supply-executor-and-worker-config) of the walkthrough for more information.

:::

While `dagster-celery` is designed to make the full range of Celery configuration available on an as-needed basis, keep in mind that some combinations of config may not be compatible with each other. However, if you're may be comfortable tuning Celery, changing some of the settings may work better for your use case.

### Monitoring and debugging

There are several available tools for monitoring and debugging your queues and workers. First is the Dagster UI, which will display event logs and the `stdout`/`stderr` from runs. You can also view the logs generated by the broker and by the worker processes.

To debug broker/queue level issues, use the monitoring tools provided by the broker you're running. RabbitMQ includes a [monitoring API](https://www.rabbitmq.com/monitoring.html) and has first class support for Prometheus and Grafana integration in production.

To monitor celery workers and queues, you can use Celery's [Flower](https://flower.readthedocs.io/en/latest/) tool. This can be useful in understanding how workers interact with the queue.

### Broker and backend

`dagster-celery` has been tested using the RabbitMQ broker and default RPC backend.
