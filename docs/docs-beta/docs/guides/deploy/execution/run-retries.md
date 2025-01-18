---
title: "Configuring run retries"
sidebar_position: 600
---

If you configure run retries, a new run will be kicked off whenever a run fails for any reason. Compared to [op retries](/todo), the maximum retry limit for run retries applies to the whole run instead of each individual op. Run retries also handle the case where the run process crashes or is unexpectedly terminated.

## Configuration

How to configure run retries depends on whether you're using Dagster+ or Dagster Open Source:

- **Dagster+**: Use the [Dagster+ UI or the dagster-cloud CLI](/dagster-plus/deployment/management/settings/deployment-settings) to set a default maximum number of retries. Run retries do not need to be explicitly enabled.
- **Dagster Open Source**: Use your instance's `dagster.yaml` to enable run retries.

For example, the following will set a default maximum number of retries of `3` for all runs:

```yaml
run_retries:
  enabled: true # Omit this key if using Dagster+, since run retries are enabled by default
  max_retries: 3
```

In both Dagster+ and Dagster Open Source, you can also configure retries using tags either on Job definitions or in the Dagster UI [Launchpad](/guides/deploy/execution/webserver).

{/* TODO convert to <CodeExample> */}
```python file=/deploying/job_retries.py
from dagster import job


@job(tags={"dagster/max_retries": 3})
def sample_job():
    pass


@job(tags={"dagster/max_retries": 3, "dagster/retry_strategy": "ALL_STEPS"})
def other_sample_sample_job():
    pass
```

### Retry Strategy

The `dagster/retry_strategy` tag controls which ops the retry will run.

By default, retries will re-execute from failure (tag value `FROM_FAILURE`). This means that any successful ops will be skipped, but their output will be used for downstream ops. If the `dagster/retry_strategy` tag is set to `ALL_STEPS`, all the ops will run again.

:::note

`FROM_FAILURE` requires an I/O manager that can access outputs from other runs. For example, on Kubernetes the <PyObject section="libraries" object="s3.s3_pickle_io_manager" module="dagster_aws" /> would work but the <PyObject section="io-managers" object="FilesystemIOManager" module="dagster" /> would not, since the new run is in a new Kubernetes job with a separate filesystem.

:::

### Combining op and run retries

By default, if a run fails due to an op failure and both op and run retries are enabled, the overlapping retries might cause the op to be retried more times than desired. This is because the op retry count will reset for each retried run.

To prevent this, you can configure run retries to only retry when the failure is for a reason other than an op failure, like a crash or an unexpected termination of the run worker. This behavior is controlled by the `run_retries.retry_on_asset_or_op_failure` setting, which defaults to `true` but can be overridden to `false`.

For example, the following configures run retries so that they ignore runs that failed due to a step failure:

```yaml
run_retries:
  enabled: true # Omit this key if using Dagster+, since run retries are enabled by default
  max_retries: 3
  retry_on_asset_or_op_failure: false
```

You can also apply the `dagster/retry_on_asset_or_op_failure` tag on specific jobs using tags to override the default value for runs of that job:

```python
from dagster import job


@job(tags={"dagster/max_retries": 3, "dagster/retry_on_asset_or_op_failure": False})
def sample_job():
    pass
```

:::note

Setting `retry_on_asset_or_op_failure` to `false` will only change retry behavior for runs on Dagster version 1.6.7 or greater.

:::
