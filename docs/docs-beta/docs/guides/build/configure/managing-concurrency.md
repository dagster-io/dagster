---
title: Managing concurrency of Dagster assets and jobs
sidebar_label: Managing concurrency
description: How to limit the number of concurrent executions on a Dagster instance.
sidebar_position: 900
---

You often want to control the number of concurrent runs for a Dagster job, a specific asset, or for a type of asset or job. Limiting concurrency in your data pipelines can help prevent performance problems and downtime.


<details>
<summary>Prerequisites</summary>

- Familiarity with [Assets](/guides/build/assets-concepts/index.mdx
- Familiarity with [Jobs and Ops](/guides/build/ops-jobs)
</details>



## Limit the number of total runs that can be in progress at the same time

* Dagster Core, add the following to your [dagster.yaml](/todo)
* In Dagster+, add the following to your [deployment settings](/dagster-plus/deployment/deployment-settings)

```yaml
concurrency:
  max_runs: 15
```

## Limit the number of runs that can be in progress for a set of assets

You can assign assets and ops to concurrency groups which allow you to limit the number of in progress runs containing those assets or ops.  You first assign your asset to a concurrency group using the `concurrency_group` keyword argument.

<CodeExample filePath="guides/tbd/concurrency-global.py" language="python" title="Global concurrency limits" />

Once you have assigned a concurrency group, you can configure a limit for that group in your deployment by using the Dagster UI or by using the Dagster CLI.

To specify a limit for the concurrency group "database" using the UI, navigate to the `Deployments` &rarr; `Concurrency limits` settings page and click the `Add concurrency limit` button:

Need screenshot here

To specify a limit for the concurrency group "database" using the CLI, use:

```
dagster instance concurrency set database 1
```

### Setting a default limit for concurrency groups

Instead of adding a limit for every individual concurrency group, you can specify a default limit for concurrency groups in your deployment settings.

* Dagster Core, add the following to your [dagster.yaml](/todo)
* In Dagster+, add the following to your [deployment settings](/dagster-plus/deployment/deployment-settings)

```yaml
concurrency:
  concurrency_group:
    default_limit: 1
```


## Limit the number of runs by run tag

You can also limit the number of in progress runs by run tag.  This is useful for limiting sets of runs independent of which assets or ops it is executing. For example, you might want to limit the number of in-progress runs for a particular schedule. Or, you might want to limit the number of in-progress runs for all backfills.

```yaml
concurrency:
  run_tag_limits:
    - key: "dagster/sensor_name"
      value: "my_cool_sensor"
      limit: 5
    - key: "dagster/backfill"
      limit: 10
```

### Limiting runs by unique tag value

To apply separate limits to each unique value of a run tag, set a limit for each unique value using applyLimitPerUniqueValue. For example, instead of limiting the number of backfill runs across all backfills, you may want to limit the number of runs for each backfill in progress:

```yaml
concurrency:
  run_tag_limits:
    - key: "dagster/backfill"
      value:
        applyLimitPerUniqueValue: true
      limit: 10
```

## [Advanced] Limit the number of assets/ops actively in execution across a large set of runs

For deployments with complex jobs containing many ops, blocking entire runs for a small number of concurrency-limited ops may be too coarse-grained for your requirements.  Instead of enforcing concurrency limits at the run level, Dagster will ensure that the concurrency limit will be applied at the individual op/asset execution level.  This means that if one run completes its materialization of a concurrency group asset, a materialization of another concurrency group asset in a different run may begin even if the first run is still in progress.

```yaml
concurrency:
  concurrency_group:
    enforcement_level: op
```