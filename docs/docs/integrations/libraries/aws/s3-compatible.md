---
title: Dagster & S3-compatible storage
sidebar_label: S3-compatible storage
sidebar_position: 10
description: Use Dagster's S3 resource with Amazon S3 or any S3-compatible object store by setting the endpoint URL.
tags: [dagster-supported, storage]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-aws
pypi: https://pypi.org/project/dagster-aws/
sidebar_custom_props:
  logo: images/integrations/aws-s3.svg
---

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-aws" />

## Configuration

`S3Resource` (from `dagster_aws.s3`) talks to Amazon S3 by default. Because it is built on boto3, it also works with any S3-compatible object store (for example, Backblaze B2, Cloudflare R2, or MinIO): set the `endpoint_url` field to the provider's S3 endpoint and pass the provider's credentials as `aws_access_key_id` and `aws_secret_access_key`.

Endpoint URLs, region strings, and credential formats vary by provider. Refer to your provider's S3-compatible API documentation for the correct values.

## Example

The example below mirrors the [Amazon S3 example](/integrations/libraries/aws/s3) but points `S3Resource` at an S3-compatible store by setting `endpoint_url`:

<CodeExample path="docs_snippets/docs_snippets/integrations/aws-s3-compatible.py" language="python" />

## IO managers and file managers

`S3PickleIOManager`, `S3FileManager`, and the other resources in `dagster_aws.s3` that take an `S3Resource` work against Amazon S3 or any S3-compatible store through the same `endpoint_url` configuration. You do not need a provider-specific IO manager or file manager.

## Compute logs

`S3ComputeLogManager` does not use `S3Resource`. It is configured separately in `dagster.yaml` and creates its own boto3 client. Point it at an S3-compatible store with the `endpoint_url` field:

```yaml
compute_logs:
  module: dagster_aws.s3.compute_log_manager
  class: S3ComputeLogManager
  config:
    bucket: 'my-compute-logs-bucket'
    prefix: 'dagster-compute-logs'
    endpoint_url: 'https://s3.example-provider.com'
    use_ssl: true
    verify: true
```

The compute log manager does not accept credential fields. It reads credentials and the default region from the standard boto3 sources, such as the `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_DEFAULT_REGION` environment variables or a shared AWS config file. Set these to your provider's values in the environment where the Dagster instance runs. The optional `region` field only controls the region shown in console URLs and is not passed to the boto3 client. Use `verify_cert_path` to supply a custom CA bundle when your endpoint uses a private certificate.
