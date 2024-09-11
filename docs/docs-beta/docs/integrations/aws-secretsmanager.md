---
layout: Integration
status: published
name: AWS Secrets Manager
title: Dagster & AWS Secrets Manager
sidebar_label: AWS Secrets Manager
excerpt: This integration allows you to manage, retrieve, and rotate credentials, API keys, and other secrets using AWS Secrets Manager.
date: 2024-06-21
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-aws
docslink: 
partnerlink: https://aws.amazon.com/
logo: /integrations/aws-secretsmanager.svg
categories:
  - Other
enabledBy:
enables:
---

### About this integration

This integration allows you to manage, retrieve, and rotate credentials, API keys, and other secrets using [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/).

### Installation

```bash
pip install dagster-aws
```

### Examples

```python
from dagster import asset, Definitions
from dagster_aws.secretsmanager import (
    SecretsManagerResource,
    SecretsManagerSecretsResource,
)


@asset
def my_asset(secretsmanager: SecretsManagerResource):
    secret_value = secretsmanager.get_client().get_secret_value(
        SecretId="arn:aws:secretsmanager:region:aws_account_id:secret:appauthexample-AbCdEf"
    )
    return secret_value


@asset
def my_other_asset(secrets: SecretsManagerSecretsResource):
    secret_value = secrets.fetch_secrets().get("my-secret-name")
    return secret_value


defs = Definitions(
    assets=[my_asset, my_other_asset],
    resources={
        "secretsmanager": SecretsManagerResource(region_name="us-west-1"),
        "secrets": SecretsManagerSecretsResource(
            region_name="us-west-1",
            secrets_tag="dagster",
        ),
    },
)
```

### About AWS Secrets Manager

**AWS Secrets Manager** helps you protect access to your applications, services, and IT resources without the upfront cost and complexity of managing your own hardware security module infrastructure. With Secrets Manager, you can rotate, manage, and retrieve database credentials, API keys, and other secrets throughout their lifecycle. Users and applications retrieve secrets with a call to Secrets Manager APIs, eliminating the need to hardcode sensitive information in plain text.
