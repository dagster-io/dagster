---
description: Configure where Dagster+ compute logs are stored and manage masking of error messages in the Dagster+ UI.
sidebar_position: 200
title: Managing compute logs and error messages
---

import ThemedImage from '@theme/ThemedImage';

:::note

This guide is applicable to Dagster+.

:::

In this guide, we'll cover how to adjust where Dagster+ compute logs are stored and manage masking of error messages in the Dagster+ UI.

By default, Dagster+ ingests [structured event logs and compute logs](/guides/monitor/logging/index.md#log-types) from runs and surfaces error messages from [code locations](/dagster-plus/deployment/code-locations/) in the UI.

Depending on your organization's needs, you may want to retain these logs in your own infrastructure or mask error message contents.

## Modifying compute log storage

Dagster's compute logs are handled by the configured [`ComputeLogManager`](/api/dagster/internals#compute-log-manager). By default, Dagster+ utilizes the `CloudComputeLogManager` which stores logs in a Dagster+-managed Amazon S3 bucket, but you can customize this behavior to store logs in a destination of your choice.

### Writing to your own S3 bucket

If using the Kubernetes agent, you can instead forward logs to your own S3 bucket by using the [`S3ComputeLogManager`](/api/libraries/dagster-aws#dagster_aws.s3.S3ComputeLogManager).

You can configure the `S3ComputeLogManager` in your [`dagster.yaml` file](/dagster-plus/deployment/management/settings/customizing-agent-settings):

```yaml
compute_logs:
  module: dagster_aws.s3.compute_log_manager
  class: S3ComputeLogManager
  config:
    show_url_only: true
    bucket: your-compute-log-storage-bucket
    region: your-bucket-region
```

If you are using Helm to deploy the Kubernetes agent, you can provide the following configuration in your `values.yaml` file:

```yaml
computeLogs:
  enabled: true
  custom:
    module: dagster_aws.s3.compute_log_manager
    class: S3ComputeLogManager
    config:
      show_url_only: true
      bucket: your-compute-log-storage-bucket
      region: your-bucket-region
```

### Disabling compute log upload

If your organization has its own logging solution which ingests `stdout` and `stderr` from your compute environment, you may want to disable compute log upload entirely. You can do this with the <PyObject section="internals" module="dagster._core.storage.noop_compute_log_manager" object="NoOpComputeLogManager" />.

You can configure the `NoOpComputeLogManager` in your [`dagster.yaml` file](/dagster-plus/deployment/management/settings/customizing-agent-settings):

```yaml
compute_logs:
  module: dagster.core.storage.noop_compute_log_manager
  class: NoOpComputeLogManager
```

If you are using Helm to deploy the Kubernetes agent, use the `enabled` flag to disable compute log upload:

```yaml
computeLogs:
  enabled: false
```

### Other compute log storage options

For a full list of available compute log storage options, see "[Dagster instance configuration](/guides/deploy/dagster-instance-configuration#compute-log-storage)".

## Masking error messages

By default, Dagster+ surfaces error messages from your code locations in the UI, including when runs fail, sensors or schedules throw an exception, or code locations fail to load. You can mask these error messages in the case that their contents are sensitive.

To mask error messages in a Dagster+ Deployment, set the environment variable `DAGSTER_REDACT_USER_CODE_ERRORS` equal to `1` using the [**Environment variables** page](/dagster-plus/deployment/management/environment-variables/) in the UI:

![Environment variable UI showing DAGSTER_REDACT_USER_CODE_ERRORS set to 1](/images/dagster-plus/management/configure-redact-env-var.png)

Once set, error messages from your code locations will be masked in the UI. A unique error ID will be generated, which you can use to look up the error message in your own logs. This error ID will appear in place of the error message in UI dialogs or in a run's event logs:

![Error message in Dagster event logs showing unique error ID](/images/dagster-plus/management/masked-err-message.png)
