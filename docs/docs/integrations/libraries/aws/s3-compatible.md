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

## Drop-in compatibility with `dagster-aws`

`S3Resource` is the same resource consumed by every `dagster-aws` IO manager, file manager, and compute log manager. That means `S3PickleIOManager`, `S3ComputeLogManager`, `S3FileManager`, and the other resources in `dagster_aws.s3` work against Amazon S3 or any S3-compatible store through the same `endpoint_url` configuration. You do not need a provider-specific IO manager or file manager.
