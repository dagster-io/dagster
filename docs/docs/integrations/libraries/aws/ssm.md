---
title: Dagster & AWS Systems Parameter Store
sidebar_label: Systems Parameter Store
sidebar_position: 11
description: The Dagster AWS Systems Manager (SSM) Parameter Store integration allows you to manage and retrieve parameters stored in AWS SSM Parameter Store directly within your Dagster pipelines. This integration provides resources to fetch parameters by name, tags, or paths, and optionally set them as environment variables for your operations.
tags: [dagster-supported]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-aws
pypi: https://pypi.org/project/dagster-aws/
sidebar_custom_props:
  logo: images/integrations/aws-ssm.svg
partnerlink: https://aws.amazon.com/
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-aws" />

## Examples

<CodeExample path="docs_snippets/docs_snippets/integrations/aws-ssm.py" language="python" />

## About AWS Systems Parameter Store

**AWS Systems Manager Parameter Store** is a secure storage service for configuration data management and secrets management. It allows you to store data such as passwords, database strings, and license codes as parameter values. You can then reference these parameters in your applications or scripts, ensuring that sensitive information isn't hard-coded or exposed in your codebase.

AWS Systems Manager Parameter Store integrates with AWS Identity and Access Management (IAM) to control access to parameters, and it supports encryption using AWS Key Management Service (KMS) to protect sensitive data. This service is essential for maintaining secure and manageable configurations across your AWS environment.
