---
title: "Dagster instance"
description: "Define configuration options for your Dagster instance."
sidebar_position: 200
---

:::note

This article applies to Dagster Open Source (OSS) deployments. For information on Dagster+, see the [Dagster+ documentation](/dagster-plus/deployment/management/settings/customizing-agent-settings).

:::

The Dagster instance defines the configuration that Dagster needs for a single deployment - for example, where to store the history of past runs and their associated logs, where to stream the raw logs from op compute functions, and how to launch new runs.

All of the processes and services that make up your Dagster deployment should share a single instance config file, named `dagster.yaml`, so that they can effectively share information.

:::warning

Some important configuration, like [execution parallelism](/guides/operate/run-executors), is set on a per-job basis rather than on the instance.

:::

## Default local behavior

When a Dagster process like the Dagster webserver or Dagster CLI commands are launched, Dagster tries to load your instance. If the environment variable `DAGSTER_HOME` is set, Dagster looks for an instance config file at `$DAGSTER_HOME/dagster.yaml`. This file contains the configuration settings that make up the instance.

If `DAGSTER_HOME` isn't set, Dagster tools will use a temporary directory for storage that is cleaned up when the process exits. This can be useful when using Dagster for temporary local development or testing, when you don't care about the results being persisted.

If `DAGSTER_HOME` is set but `dagster.yaml` isn't present or is empty, Dagster will persist data on the local filesystem, structured like the following:

```
$DAGSTER_HOME
├── dagster.yaml
├── history
│   ├── runs
│   │   ├── 00636713-98a9-461c-a9ac-d049407059cd.db
│   │   └── ...
│   └── runs.db
└── storage
    ├── 00636713-98a9-461c-a9ac-d049407059cd
    │   └── compute_logs
    │       └── ...
    └── ...
```

Here's a breakdown of the files and directories that are generated:

| File or directory | Description |
|-------------------|-------------|
| history/          | A directory containing historical information for runs. |
| history/runs.db   | SQLite database file that contains information about runs. |
| history/[run_id].db | SQLite database file that contains per-run event logs. |
| storage/          | A directory of subdirectories, one for each run. |
| storage/[run_id]/compute_logs | A directory specific to the run that contains the `stdout` and `stderr` logs from the execution of the compute functions of each op. |

## Configuration reference

In persistent Dagster deployments, you'll typically want to configure many of the components on the instance. For example, you may want to use a Postgres instance to store runs and the corresponding event logs, but stream compute logs to an Amazon S3 bucket.

To do this, provide a `$DAGSTER_HOME/dagster.yaml` file, which the webserver and all other Dagster tools will look for on startup. In this file, you can configure different aspects of your Dagster instance, including:

| Name                   | Key                       | Description  |
|------------------------|---------------------------|--------------|
|  Dagster storage       |  `storage`                |  Controls how job and asset history is persisted. This includes run, event log, and schedule/sensor tick metadata, as well as other useful data. |
|  Run launcher          |  `run_launcher`           | Determines where runs are executed. |
|  Run coordinator       |  `run_coordinator`        |  Determines the policy used to set prioritization rules and concurrency limits for runs. |
|  Compute log storage   |  `compute_logs`           |  Controls the capture and persistence of raw stdout and{" "} stderr ext logs. |
|  Local artifact storage|  `local_artifact_storage` |  Configures storage for artifacts that require a local disk or when using the filesystem I/O manager (  ). |
|  Telemetry             |  `telemetry`              |  Used to opt in/out of Dagster collecting anonymized usage statistics. |
|  gRPC servers          |  `code_servers`           | Configures how Dagster loads the code in a code location. |
|  Data retention        |  `data_retention`         |  Controls how long Dagster retains certain types of data that have diminishing value over time, such as schedule/sensor tick data. |
|  Sensor evaluation     |  `sensors`                | Controls how sensors are evaluated. |
|  Schedule evaluation   |  `schedules`              | Controls how schedules are evaluated. |
|  Auto-materialize      |  `auto_materialize`       | Controls how assets are auto-materialized.|

:::note

Environment variables in YAML configuration are supported by using an `env:` key instead of a literal string value. Sample configurations in this reference include examples using environment variables.

:::

### Dagster storage

The `storage` key allows you to configure how job and asset history is persisted. This includes metadata on runs, event logs, schedule/sensor ticks, and other useful data.

Refer to the following tabs for available options and sample configuration.

<Tabs>
  <TabItem value="Sqlite storage (default)" label="Sqlite storage (default)">

**SQLite storage (default)**

To use a SQLite database for storage, configure `storage.sqlite` in `dagster.yaml`:

<CodeExample path="docs_snippets/docs_snippets/deploying/dagster_instance/dagster.yaml" startAfter="start_marker_storage_sqlite" endBefore="end_marker_storage_sqlite" />

</TabItem>
<TabItem value="Postgres storage" label="Postgres storage">

**Postgres storage**

:::note

To use Postgres storage, you'll need to install the [dagster-postgres](/api/python-api/libraries/dagster-postgres) library.

:::

To use a [PostgreSQL database](/api/python-api/libraries/dagster-postgres) for storage, configure `storage.postgres` in `dagster.yaml`:


<CodeExample path="docs_snippets/docs_snippets/deploying/dagster_instance/dagster.yaml" startAfter="start_marker_storage_postgres" endBefore="end_marker_storage_postgres" />

</TabItem>
<TabItem value="MySQL storage" label="MySQL storage">

**MySQL storage**

:::note

To use MySQL storage, you'll need to install the [dagster-mysql](/api/python-api/libraries/dagster-mysql) library.

:::

To use a [MySQL database](/api/python-api/libraries/dagster-mysql) for storage, configure `storage.mysql` in `dagster.yaml`:


<CodeExample path="docs_snippets/docs_snippets/deploying/dagster_instance/dagster.yaml" startAfter="start_marker_storage_mysql" endBefore="end_marker_storage_mysql" />

</TabItem>
</Tabs>

### Run launcher

The `run_launcher` key allows you to configure the run launcher for your instance. Run launchers determine where runs are executed. You can use one of the Dagster-provided options or write your own custom run launcher. For more information, see "[Run launchers](/guides/deploy/execution/run-launchers)".

Refer to the following tabs for available options and sample configuration. Keep in mind that databases should be configured to use UTC timezone.

<Tabs>
<TabItem value="DefaultRunLauncher" label="DefaultRunLauncher (default)">

**DefaultRunLauncher**

The <PyObject section="internals" module="dagster._core.launcher" object="DefaultRunLauncher" /> spawns a new process in the same node as a job's code location.


<CodeExample path="docs_snippets/docs_snippets/deploying/dagster_instance/dagster.yaml" startAfter="start_marker_run_launcher_default" endBefore="end_marker_run_launcher_default" />

</TabItem>
<TabItem value="DockerRunLauncher" label="DockerRunLauncher">

**DockerRunLauncher**

The <PyObject section="libraries" module="dagster_docker" object="DockerRunLauncher" /> allocates a Docker container per run.


<CodeExample path="docs_snippets/docs_snippets/deploying/dagster_instance/dagster.yaml" startAfter="start_marker_run_launcher_docker" endBefore="end_marker_run_launcher_docker" />

</TabItem>
<TabItem value="K8sRunLauncher" label="K8sRunLauncher">

**K8sRunLauncher**

The <PyObject section="libraries" module="dagster_k8s" object="K8sRunLauncher" /> allocates a Kubernetes job per run.

<CodeExample path="docs_snippets/docs_snippets/deploying/dagster_instance/dagster.yaml" startAfter="start_marker_run_launcher_k8s" endBefore="end_marker_run_launcher_k8s" />

</TabItem>
</Tabs>

### Run coordinator

The `run_coordinator` key allows you to configure the run coordinator for your instance. Run coordinators determine the policy used to set the prioritization rules and concurrency limits for runs. For more information and troubleshooting help, see "[Run coordinators](/guides/deploy/execution/run-coordinators)".

Refer to the following tabs for available options and sample configuration.

<Tabs>
<TabItem value="DefaultRunCoordinator (default)" label="DefaultRunCoordinator (default)">

**DefaultRunCoordinator (default)**

The default run coordinator, the <PyObject section="internals" module="dagster._core.run_coordinator" object="DefaultRunCoordinator" /> immediately sends runs to the [run launcher](#run-launcher). There isn't a notion of `Queued` runs.


<CodeExample path="docs_snippets/docs_snippets/deploying/dagster_instance/dagster.yaml" startAfter="start_marker_run_coordinator_default" endBefore="end_marker_run_coordinator_default" />

</TabItem>
<TabItem value="QueuedRunCoordinator" label="QueuedRunCoordinator">

**QueuedRunCoordinator**

The <PyObject section="internals" module="dagster._core.run_coordinator" object="QueuedRunCoordinator" /> allows you to set limits on the number of runs that can be executed at once. **Note** This requires an active [dagster-daemon process](/guides/deploy/execution/dagster-daemon) to launch the runs.

This run coordinator supports both limiting the overall number of concurrent runs and specific limits based on run tags. For example, to avoid throttling, you can specify a concurrency limit for runs that interact with a specific cloud service.


<CodeExample path="docs_snippets/docs_snippets/deploying/dagster_instance/dagster.yaml" startAfter="start_marker_run_coordinator_queued" endBefore="end_marker_run_coordinator_queued" />

</TabItem>
</Tabs>

### Compute log storage

The `compute_logs` key allows you to configure compute log storage. Compute log storage controls the capture and persistence of raw `stdout` and `stderr` text logs.

Refer to the following tabs for available options and sample configuration.

<Tabs>
<TabItem value="LocalComputeLogManager (default)" label="LocalComputeLogManager (default)">

**LocalComputeLogManager**

Used by default, the <PyObject section="internals" module="dagster._core.storage.local_compute_log_manager" object="LocalComputeLogManager" /> writes `stdout` and `stderr` logs to disk.


<CodeExample path="docs_snippets/docs_snippets/deploying/dagster_instance/dagster.yaml" startAfter="start_marker_compute_log_storage_local" endBefore="end_marker_compute_log_storage_local" />

</TabItem>
<TabItem value="NoOpComputeLogManager" label="NoOpComputeLogManager">

**NoOpComputeLogManager**

The <PyObject section="internals" module="dagster._core.storage.noop_compute_log_manager" object="NoOpComputeLogManager" /> does not store `stdout` and `stderr` logs for any step.

<CodeExample path="docs_snippets/docs_snippets/deploying/dagster_instance/dagster.yaml" startAfter="start_marker_compute_log_storage_noop" endBefore="end_marker_compute_log_storage_noop" />

</TabItem>
<TabItem value="AzureBlobComputeLogManager" label="AzureBlobComputeLogManager">

**AzureBlobComputeLogManager**

The <PyObject section="libraries" module="dagster_azure" object="blob.AzureBlobComputeLogManager" /> writes `stdout` and `stderr` to Azure Blob Storage.

<CodeExample path="docs_snippets/docs_snippets/deploying/dagster_instance/dagster.yaml" startAfter="start_marker_compute_log_storage_blob" endBefore="end_marker_compute_log_storage_blob" />

</TabItem>
<TabItem value="GCSComputeLogManager" label="GCSComputeLogManager">

**GCSComputeLogManager**

The <PyObject section="libraries" module="dagster_gcp" object="gcs.GCSComputeLogManager" /> writes `stdout` and `stderr` to Google Cloud Storage.

<CodeExample path="docs_snippets/docs_snippets/deploying/dagster_instance/dagster.yaml" startAfter="start_marker_compute_log_storage_gcs" endBefore="end_marker_compute_log_storage_gcs" />

</TabItem>
<TabItem value="S3ComputeLogManager" label="S3ComputeLogManager">

**S3ComputeLogManager**

The <PyObject section="libraries" module="dagster_aws" object="s3.S3ComputeLogManager" /> writes `stdout` and `stderr` to an Amazon Web Services S3 bucket.

<CodeExample path="docs_snippets/docs_snippets/deploying/dagster_instance/dagster.yaml" startAfter="start_marker_compute_log_storage_s3" endBefore="end_marker_compute_log_storage_s3" />

</TabItem>
</Tabs>

### Local artifact storage

The `local_artifact_storage` key allows you to configure local artifact storage. Local artifact storage is used to:

- Configure storage for artifacts that require a local disk, or
- Store inputs and outputs when using the filesystem I/O manager (<PyObject section="io-managers" module="dagster" object="FilesystemIOManager" />). For more information on how other I/O managers store artifacts, see the [I/O managers documentation](/guides/build/io-managers/).

:::note

<PyObject section="internals" module="dagster._core.storage.root" object="LocalArtifactStorage" /> is currently the only option for local artifact storage. This option configures the directory used by the default filesystem I/O Manager, as well as any artifacts that require a local disk.

:::

<CodeExample path="docs_snippets/docs_snippets/deploying/dagster_instance/dagster.yaml" startAfter="start_marker_local_artifact_storage" endBefore="end_marker_local_artifact_storage" />

### Telemetry

The `telemetry` key allows you to opt in or out of Dagster collecting anonymized usage statistics. This is set to `true` by default.

<CodeExample path="docs_snippets/docs_snippets/deploying/dagster_instance/dagster.yaml" startAfter="start_marker_telemetry" endBefore="end_marker_telemetry" />

For more information, see the [Telemetry documentation](/about/telemetry).

### gRPC servers

The `code_servers` key allows you to configure how Dagster loads the code in a [code location](/guides/deploy/code-locations/).

When you aren't [running your own gRPC server](/guides/deploy/code-locations/workspace-yaml#grpc-server), the webserver and the Dagster daemon load your code from a gRPC server running in a subprocess. By default, if your code takes more than 180 seconds to load, Dagster assumes that it's hanging and stops waiting for it to load.

If you expect that your code will take longer than 180 seconds to load, set the `code_servers.local_startup_timeout` key. The value should be an integer that indicates the maximum timeout, in seconds.

<CodeExample path="docs_snippets/docs_snippets/deploying/dagster_instance/dagster.yaml" startAfter="start_marker_code_servers" endBefore="end_marker_code_servers" />

### Data retention

The `retention` key allows you to configure how long Dagster retains certain types of data. Specifically, data that has diminishing value over time, such as schedule/sensor tick data. Cleaning up old ticks can help minimize storage concerns and improve query performance.

By default, Dagster retains skipped sensor ticks for seven days and all other tick types indefinitely. To customize the retention policies for schedule and sensor ticks, use the `purge_after_days` key:

<CodeExample path="docs_snippets/docs_snippets/deploying/dagster_instance/dagster.yaml" startAfter="start_marker_retention" endBefore="end_marker_retention" />

The `purge_after_days` key accepts either:

- A single integer that indicates how long, in days, to retain ticks of all types. **Note**: A value of `-1` retains ticks indefinitely.
- A mapping of tick types (`skipped`, `failure`, `success`) to integers. The integers indicate how long, in days, to retain the tick type.

### Sensor evaluation

The `sensors` key allows you to configure how sensors are evaluated. To evaluate multiple sensors in parallel simultaneously, set the `use_threads` and `num_workers` keys:

<CodeExample path="docs_snippets/docs_snippets/deploying/dagster_instance/dagster.yaml" startAfter="start_marker_sensors" endBefore="end_marker_sensors" />

You can also set the optional `num_submit_workers` key to evaluate multiple run requests from the same sensor tick in parallel, which can help decrease latency when a single sensor tick returns many run requests.

### Schedule evaluation

The `schedules` key allows you to configure how schedules are evaluated. By default, Dagster evaluates schedules one at a time.

To evaluate multiple schedules in parallel simultaneously, set the `use_threads` and `num_workers` keys:

<CodeExample path="docs_snippets/docs_snippets/deploying/dagster_instance/dagster.yaml" startAfter="start_marker_schedules" endBefore="end_marker_schedules" />

You can also set the optional `num_submit_workers` key to evaluate multiple run requests from the same schedule tick in parallel, which can help decrease latency when a single schedule tick returns many run requests.
