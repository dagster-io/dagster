---
description: Customize Dagster+ agent settings in dagster.yaml
sidebar_position: 1000
title: Customizing agent settings
tags: [dagster-plus-feature]
---

The Dagster+ Agent is a special variant of the Dagster instance used in Dagster Open Source and is configured through the same `dagster.yaml` file. You can customize your agent with these settings.

:::note

For [Kubernetes agents](/deployment/dagster-plus/hybrid/kubernetes) deployed with the Dagster+ Helm chart, refer to the Helm chart's config map for customizing the agent.

:::

## Enabling user code server TTL

User code servers support a configurable time-to-live (TTL). The agent will spin down any user code servers that haven't served requests recently and will spin them back up the next time they're needed. Configuring TTL can save compute cost because user code servers will spend less time sitting idle.

TTL is disabled by default for full deployments, and can be configured separately for full and [branch deployments](/deployment/dagster-plus/deploying-code/branch-deployments/configuring-branch-deployments). TTL defaults to 24 hours for both full and branch deployments.

To configure TTL:

```yaml
# dagster.yaml
instance_class:
  module: dagster_cloud.instance
  class: DagsterCloudAgentInstance

dagster_cloud_api:
  agent_token:
    env: DAGSTER_CLOUD_AGENT_TOKEN
  deployment: prod

user_code_launcher:
  module: dagster_cloud.workspace.docker
  class: DockerUserCodeLauncher
  config:
    server_ttl:
      full_deployments:
        enabled: true # Disabled by default for full deployments
        ttl_seconds: 7200 # 2 hours
      branch_deployments:
        ttl_seconds: 3600 # 1 hour
```

## Retrying code locations that fail to start

By default, if a code location's code server fails to start (for example, an image pull failure or a startup timeout), the agent reports the failure and leaves the location as it is until you redeploy it. You can instead have the agent retry the start automatically.

Retries are off by default. Setting `max_attempts` above `0` enables them:

```yaml
# dagster.yaml
instance_class:
  module: dagster_cloud.instance
  class: DagsterCloudAgentInstance

dagster_cloud_api:
  agent_token:
    env: DAGSTER_CLOUD_AGENT_TOKEN
  deployment: prod

user_code_launcher:
  module: dagster_cloud.workspace.docker
  class: DockerUserCodeLauncher
  config:
    code_location_start_retry:
      max_attempts: 3 # Retries are disabled when this is 0 (the default)
      backoff_seconds: 300 # Delay before the first retry (default 300), doubled after each attempt
```

- Only start failures are retried. Errors in your code, such as an import error, are never retried.
- Image errors that a retry can't fix are not retried, such as a missing tag or manifest, an invalid image name, an unsupported architecture, or an image setting the agent can't use. Transient failures such as registry timeouts, rate limits, expired pull credentials, and startup timeouts are retried. The agent logs a warning when it skips a retry for this reason.
- The retry count resets each time a new version of the location is deployed.
- Each retry redeploys the location and reports the result to Dagster+, so the location's status updates if a retry succeeds.

For [Kubernetes agents](/deployment/dagster-plus/hybrid/kubernetes) deployed with the Helm chart, use the `workspace.codeLocationStartRetry` value:

```yaml
# values.yaml
workspace:
  codeLocationStartRetry:
    maxAttempts: 3
    backoffSeconds: 300
```

## Streaming compute logs

You can set up streaming compute logs by configuring the log upload interval (in seconds).

```yaml
# dagster.yaml
instance_class:
  module: dagster_cloud.instance
  class: DagsterCloudAgentInstance

dagster_cloud_api:
  agent_token:
    env: DAGSTER_CLOUD_AGENT_TOKEN
  deployment: prod

user_code_launcher:
  module: dagster_cloud.workspace.docker
  class: DockerUserCodeLauncher

compute_logs:
  module: dagster_cloud
  class: CloudComputeLogManager
  config:
    upload_interval: 60
```

## Disabling compute logs

You can disable forwarding compute logs to Dagster+ by configuring the `NoOpComputeLogManager` setting:

```yaml
# dagster.yaml
instance_class:
  module: dagster_cloud.instance
  class: DagsterCloudAgentInstance

dagster_cloud_api:
  agent_token:
    env: DAGSTER_CLOUD_AGENT_TOKEN
  deployment: prod

user_code_launcher:
  module: dagster_cloud.workspace.docker
  class: DockerUserCodeLauncher

compute_logs:
  module: dagster.core.storage.noop_compute_log_manager
  class: NoOpComputeLogManager
```

## Writing compute logs to AWS S3

You can write compute logs to an AWS S3 bucket by configuring the <PyObject section="libraries" integration="aws" module="dagster_aws" object="s3.S3ComputeLogManager" /> module.

You are also able to stream partial compute log files by configuring the log upload interval (in seconds) using the `upload_interval` parameter.

Note: Dagster Labs will neither have nor use your AWS credentials. The Dagster+ UI will be able to show the URLs linking to the compute log files in your S3 bucket when you set the `show_url_only` parameter to `true`.

```yaml
# dagster.yaml
instance_class:
  module: dagster_cloud.instance
  class: DagsterCloudAgentInstance

dagster_cloud_api:
  agent_token:
    env: DAGSTER_CLOUD_AGENT_TOKEN
  deployment: prod

user_code_launcher:
  module: dagster_cloud.workspace.docker
  class: DockerUserCodeLauncher

compute_logs:
  module: dagster_aws.s3.compute_log_manager
  class: S3ComputeLogManager
  config:
    bucket: 'mycorp-dagster-compute-logs'
    local_dir: '/tmp/cool'
    prefix: 'dagster-test-'
    use_ssl: true
    verify: true
    verify_cert_path: '/path/to/cert/bundle.pem'
    endpoint_url: 'http://alternate-s3-host.io'
    skip_empty_files: true
    upload_interval: 30
    upload_extra_args:
      ServerSideEncryption: 'AES256'
    show_url_only: true
    region: 'us-west-1'
```
