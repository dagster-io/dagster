---
title: 'Op jobs'
sidebar_position: 200
---

:::note

Looking to materialize [asset definitions](/guides/build/assets/) instead of ops? Check out the [asset jobs](/guides/build/jobs/asset-jobs) documentation.

:::

[Jobs](/guides/build/jobs/) are the main unit of execution and monitoring in Dagster. An op job executes a [graph](/guides/build/ops/graphs) of [ops](/guides/build/ops/).

Op jobs can be launched in a few different ways:

- Manually from the Dagster UI
- At fixed intervals, by [schedules](/guides/automate/schedules/)
- When external changes occur, using [sensors](/guides/automate/sensors/)

## Relevant APIs

| Name                                | Description                                                                                                                                                     |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| <PyObject section="jobs" module="dagster" object="job" decorator /> | The decorator used to define a job.                                                                                                                             |
| <PyObject section="jobs" module="dagster" object="JobDefinition" /> | A job definition. Jobs are the main unit of execution and monitoring in Dagster. Typically constructed using the <PyObject section="jobs" module="dagster" object="job" decorator /> decorator. |

## Creating op jobs

Op jobs can be created:

- [Using the `@job` decorator](#using-the-job-decorator)
- [From a graph](#from-a-graph)

### Using the @job decorator

The simplest way to create an op job is to use the <PyObject section="jobs" module="dagster" object="job" decorator />decorator.

Within the decorated function body, you can use function calls to indicate the dependency structure between the ops/graphs. This allows you to explicitly define dependencies between ops when you define the job.

In this example, the `add_one` op depends on the `return_five` op's output. Because this data dependency exists, the `add_one` op executes after `return_five` runs successfully and emits the required output:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/simple_job.py" />

When defining an op job, you can provide any of the following:

- [Resources](/guides/build/external-resources/)
- [Configuration](/guides/operate/configuration/)
- [Hooks](/guides/build/ops/op-hooks)
- [Tags](/guides/build/assets/metadata-and-tags/tags) and other metadata
- An [executor](/guides/operate/run-executors)

### From a graph

Creating op jobs from a graph can be useful when you want to define inter-op dependencies before binding them to resources, configuration, executors, and other environment-specific features. This approach to op job creation allows you to customize graphs for each environment by plugging in configuration and services specific to that environment.

You can model this by building multiple op jobs that use the same underlying graph of ops. The graph represents the logical core of data transformation, and the configuration and resources on each op job customize the behavior of that job for its environment.

To do this, define a graph using the <PyObject section="graphs" module="dagster" object="graph" decorator /> decorator:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/jobs_from_graphs.py" startAfter="start_define_graph" endBefore="end_define_graph" />

Then build op jobs from it using the <PyObject section="graphs" module="dagster" object="GraphDefinition" method="to_job" /> method:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/jobs_from_graphs.py" startAfter="start_define_jobs" endBefore="end_define_jobs" />

`to_job` accepts the same arguments as the <PyObject section="jobs" module="dagster" object="job" decorator />decorator, such as providing resources, configuration, etc.

## Configuring op jobs

Ops and resources can accept [configuration](/guides/operate/configuration/run-configuration) that determines how they behave. By default, configuration is supplied at the time an op job is launched.

When constructing an op job, you can customize how that configuration will be satisfied by passing a value to the `config` parameter of the <PyObject section="graphs" module="dagster" object="GraphDefinition.to_job" /> method or the <PyObject section="jobs" module="dagster" object="job" decorator />decorator.

The options are discussed below:

- [Hardcoded configuration](#hardcoded-configuration)
- [Partitioned configuration](#partitioned-configuration)
- [Config mapping](#config-mapping)

### Hardcoded configuration

You can supply a <PyObject section="config" module="dagster" object="RunConfig"/> object or raw config dictionary. The supplied config will be used to configure the op job whenever it's launched. It will show up in the Dagster UI Launchpad and can be overridden.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/jobs_with_default_config.py" />

### Partitioned configuration

Supplying a <PyObject section="partitions" module="dagster" object="PartitionedConfig" /> will create a partitioned op job. This defines a discrete set of partitions along with a function for generating config for a partition. Op job runs can be configured by selecting a partition.

Refer to the [Partitioning ops documentation](/guides/build/partitions-and-backfills/partitioning-ops) for more info and examples.

### Config mapping

Supplying a <PyObject section="config" module="dagster" object="ConfigMapping" /> allows you to expose a narrower config interface to the op job.

Instead of needing to configure every op and resource individually when launching the op job, you can supply a smaller number of values to the outer config. The <PyObject section="config" module="dagster" object="ConfigMapping" /> will then translate it into config for all the job's ops and resources.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/jobs_with_config_mapping.py" />

## Making op jobs available to Dagster tools

You make jobs available to the UI, GraphQL, and command line by including them in a <PyObject section="definitions" module="dagster" object="Definitions"/> object at the top level of Python module or file. The tool loads that module as a [code location](/guides/deploy/code-locations/). If you include schedules or sensors, the code location will automatically include jobs that those schedules or sensors target.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/repo_with_job.py" />

## Testing op jobs

Dagster has built-in support for testing, including separating business logic from environments and setting explicit expectations on uncontrollable inputs. Refer to the [testing documentation](/guides/test/) for more info and examples.

## Executing op jobs

You can run an op job in a variety of ways:

- In the Python process where it's defined
- Via the command line
- Via the GraphQL API
- In [the UI](/guides/operate/webserver#dagster-ui-reference). The UI centers on jobs, making it a one-stop shop - you can manually kick off runs for an op job and view all historical runs.

Refer to the [Job execution guide](/guides/build/jobs/job-execution) for more info and examples.