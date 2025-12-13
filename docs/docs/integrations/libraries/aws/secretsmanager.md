---
title: Dagster & AWS Secrets Manager
sidebar_label: Secrets Manager
sidebar_position: 10
description: This integration allows you to manage, retrieve, and rotate credentials, API keys, and other secrets using AWS Secrets Manager.
tags: [dagster-supported]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-aws
pypi: https://pypi.org/project/dagster-aws/
sidebar_custom_props:
  logo: images/integrations/aws-secretsmanager.svg
partnerlink: https://aws.amazon.com/
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-aws" />

## Examples

<CodeExample path="docs_snippets/docs_snippets/integrations/aws-secretsmanager.py" language="python" />

## About AWS Secrets Manager

**AWS Secrets Manager** helps you protect access to your applications, services, and IT resources without the upfront cost and complexity of managing your own hardware security module infrastructure. With Secrets Manager, you can rotate, manage, and retrieve database credentials, API keys, and other secrets throughout their lifecycle. Users and applications retrieve secrets with a call to Secrets Manager APIs, eliminating the need to hardcode sensitive information in plain text.
