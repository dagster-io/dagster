---
title: Managing concurrency of Dagster assets, jobs, and Dagster instances
sidebar_label: Managing concurrency
description: How to limit the number of runs a job, or assets for an instance of Dagster.
---

You often want to control the number of concurrent runs for a Dagster job, a specific asset, or for a type of asset or job. Limiting concurrency in your data pipelines can help prevent performance problems and downtime.

This guide shows the most common ways to limit concurrency within Dagster:

* Within a specific run
* Across all runs
* For a specific tag across all runs
* Limiting the number of active runs for a specific job


<details>
<summary>Prerequisites</summary>

- Familiarity with [Assets](/concepts/assets)
- Familiarity with [Jobs and Ops](/concepts/ops-jobs)
</details>



## Limit how many jobs can be running at the same time


* Dagster Core, add the following to your [dagster.yaml](/todo)
* In Dagster+, add the following to your [deployment settings](/dagster-plus/settings)

```yaml
run_queue:
  max_concurrent_runs: 15
```


<CodeExample filePath="guides/tbd/concurrency-global.py" language="python" title="Global concurrency limits" />

## Limit how many ops or assets can be running at the same time

You can control the number of assets or ops that are running concurrently within a job using the `config` argument of `dg.define_asset_job` or `dg.@job()` for ops.

<Tabs>
  <TabItem value="Assets" label="Asset job">
    <CodeExample filePath="guides/tbd/concurrency-job-asset.py" language="python" title="Asset concurrency limits in a job" />
  
  </TabItem>

  <TabItem value="Ops" label="Op job">
    <CodeExample filePath="guides/tbd/concurrency-job-op.py" language="python" title="Op concurrency limits in a job" />
  
  </TabItem>
</Tabs>


## Limit how many of a certain type of op or asset can run across all runs

You can a limit for all ops or assets with a specific tag key or key-value pair. Ops or assets above that limit will be qeued. Use `tag_concurrency_limits` in the job’s config, either in Python or using the Launchpad in the Dagster UI.

For example, if you want to limit the number of ops or assets that are running with a key of `database`

:::warning
This feature is experimental and is only supported with Postgres/MySQL storages.
:::


```yaml
# dagster.yaml for Dagster Core; Deployment Settings for Dagster+
run_coordinator:
  module: dagster.core.run_coordinator
  class: QueuedRunCoordinator
  config:
    tag_concurrency_limits:
      - key: "dagster/concurrency_key"
        value: "database"
        limit: 1
```

To specify a global concurrency limit using the CLI, use:

```
dagster instance concurrency set database 1
```

A default concurrency limit can be configured for the instance, for any concurrency keys that do not have an explicit limit set:

* Dagster+: Use the Dagster+ UI or the dagster-cloud CLI
* Dagster Open Source: Use your instance's dagster.yaml

To enable this default value, use `concurrency.default_op_concurrency_limit`. For example, the following would set the default concurrency value for the deployment to 1:
```yaml
concurrency:
  default_op_concurrency_limit: 1
```

<Tabs>
  <TabItem value="Asset Tag" label="Asset tag concurrency limits">
    <CodeExample filePath="guides/tbd/concurrency-tag-key-asset.py" language="python" title="No more than 1 asset running with a tag of 'database'" />
  
  </TabItem>
  <TabItem value="Op Tag" label="Asset tag concurrency limits">
  <CodeExample filePath="guides/tbd/concurrency-tag-key-op.py" language="python" title="No more than 1 op running with a tag of 'database'" />
  
  </TabItem>
</Tabs>

Or you can configure it in the job definition:

<Tabs>
  <TabItem value="Asset Tag with Job" label="Asset tag concurrency limits in a job">
    <CodeExample filePath="guides/tbd/concurrency-tag-key-job-asset.py" language="python" title="No more than 1 asset running with a tag of 'database' job example" />
  
  </TabItem>
  <TabItem value="Op Tag with Job" label="Op tag concurrency limits in a job">
  <CodeExample filePath="guides/tbd/concurrency-tag-key-job-op.py" language="python" title="No more than 1 op running with a tag of 'database' job example" />
  </TabItem>
</Tabs>


## Override job level concurrency in the Launchpad

You can override the default job-level settings, such as the value of the `max_concurrent` key for a job, by launching a job via the Launchpad in the Dagster UI.

Need screenshot here

## Prevent runs from starting if another run is already occurring (advanced)

You can use Dagster's rich metadata to use a schedule or a sensor to only start a run when there are no currently running jobs.

<CodeExample filePath="guides/tbd/concurrency-no-more-than-1-job.py" language="python" title="No more than 1 running job from a schedule" />



## Questions for PR comments:

* Should we keep the following sections or move them to a "concepts" page? 
  * glossary
  * Setting priority for ops/assets
  * Freeing concurrency slots
  * Throttling concurrency-limited runs
  * Troubleshooting
* tag_concurrency_limits could use a major look -- is bug noted [here](https://github.com/dagster-io/dagster/issues/23508) accurate, or does this still work with Postgres / MySQL?
* question: include Dagster insance settings (`dagster.yaml / Dagster+ Deployment settings) examples as inline YAML, keep the folder with the dagster.yaml?
To repro, need to `export DAGSTER_HOME=$(pwd)/global_concurrency` (and for tag_concurrency, need an OSS version using Postgres / MYSQL)
* (from Linear) How can I set concurrency limits on a resource? -- I don't think this is possible, other than via using the concurrency tags.
