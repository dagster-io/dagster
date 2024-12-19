---
title: Customizing agent settings in dagster.yaml
sidebar_position: 80
unlisted: true
---

:::note
This guide is applicable to Dagster+.
:::

The Dagster+ Agent is a special variant of the Dagster instance used in [Dagster Open Source](/deployment/dagster-instance) and is configured through the same `dagster.yaml` file. You can customize your agent with these settings.

:::note
For [Kubernetes agents](/dagster-plus/deployment/agents/kubernetes/configuring-running-kubernetes-agent) deployed with the Dagster+ Helm chart, you'll need to refer to the Helm chart's config map for customizing the agent.
:::

## Enabling user code server TTL

User code servers support a configurable time-to-live (TTL). The agent will spin down any user code servers that haven’t served requests recently and will spin them back up the next time they’re needed. Configuring TTL can save compute cost because user code servers will spend less time sitting idle.

To configure TTL:

<CodeExample filePath="./examples/docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/management/code_server_ttl.yaml" />

## Streaming compute logs

You can set up streaming compute logs by configuring the log upload interval (in seconds).

<CodeExample filePath="./examples/docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/management/streaming_compute_logs.yaml" />

## Disabling compute logs

You can disable forwarding compute logs to Dagster+ by configuring the `NoOpComputeLogManager` setting:

<CodeExample filePath="./examples/docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/management/disable_compute_logs.yaml" />

## Writing compute logs to AWS S3

You can write compute logs to an AWS S3 bucket by configuring the [dagster_aws.s3.compute_log_manager](/api/python-api/libraries/dagster-aws#dagster_aws.s3.S3ComputeLogManager) module.

You are also able to stream partial compute log files by configuring the log upload interval (in seconds) using the `upload_interval` parameter.

Note: Dagster Labs will neither have nor use your AWS credentials. The Dagster+ UI will be able to show the URLs linking to the compute log files in your S3 bucket when you set the `show_url_only` parameter to `true`.

<CodeExample filePath="./examples/docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/management/aws_compute_logs.yaml" />