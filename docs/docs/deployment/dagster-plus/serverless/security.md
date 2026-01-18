---
description: Dagster+ Serverless secures data and secrets with container sandboxing and per-customer registries. Adjust I/O managers for PII, PHI, or GDPR compliance.
sidebar_label: Security & data protection
sidebar_position: 4000
title: Serverless security & data protection
tags: [dagster-plus-feature]
---

Unlike [Hybrid deployments](/deployment/dagster-plus/hybrid), Dagster+ Serverless deployments require direct access to your data, secrets, and source code.

Secrets and source code are built into the image directly. Images are stored in a per-customer container registry with restricted access.
User code is securely sandboxed using modern container sandboxing techniques.

All production access is governed by industry-standard best practices which are regularly audited.

## I/O management in Serverless

:::warning
The default I/O manager cannot be used if you are a Serverless user who:

- Works with personally identifiable information (PII)
- Works with private health information (PHI)
- Has signed a business association agreement (BAA), or
- Are otherwise working with data subject to GDPR or other such regulations
  :::

In Serverless, code that uses the default [I/O manager](/guides/build/io-managers) is automatically adjusted to save data in Dagster+ managed storage. This automatic change is useful because the Serverless filesystem is ephemeral, which means the default I/O manager wouldn't work as expected.

However, this automatic change also means potentially sensitive data could be **stored** and not just processed or orchestrated by Dagster+.

To prevent this, you can use [another I/O manager](/guides/build/io-managers#built-in) that stores data in your infrastructure or [adapt your code to avoid using an I/O manager](/guides/build/io-managers#before-you-begin).

:::note
You must have [boto3](https://pypi.org/project/boto3) or `dagster-cloud[serverless]` installed as a project dependency otherwise the Dagster+ managed storage can fail and silently fall back to using the default I/O manager.
:::

## Adding environment variables and secrets

Often you'll need to securely access secrets from your jobs. Dagster+ supports several methods for adding secrets—refer to the [Dagster+ environment variables documentation](/deployment/dagster-plus/management/environment-variables) for more information.
