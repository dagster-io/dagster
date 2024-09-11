---
layout: Integration
status: published
name: AWS Systems Parameter Store
title: Dagster & AWS Systems Parameter Store
sidebar_label: AWS Systems Parameter Store
excerpt: The Dagster AWS Systems Manager (SSM) Parameter Store integration allows you to manage and retrieve parameters stored in AWS SSM Parameter Store directly within your Dagster pipelines.
date: 2024-06-21
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-aws
docslink: 
partnerlink: https://aws.amazon.com/
logo: /integrations/aws-ssm.svg
categories:
  - Other
enabledBy:
enables:
---

### About this integration

The Dagster AWS Systems Manager (SSM) Parameter Store integration allows you to manage and retrieve parameters stored in AWS SSM Parameter Store directly within your Dagster pipelines. This integration provides resources to fetch parameters by name, tags, or paths, and optionally set them as environment variables for your operations.

### Installation

```bash
pip install dagster-aws
```

### Examples

```python
from dagster import asset, Definitions
from dagster_aws.ssm import ParameterStoreResource, ParameterStoreTag


@asset
def example_parameter_store_asset(parameter_store: ParameterStoreResource):
    parameter_value = parameter_store.fetch_parameters(
        parameters=["my-parameter-name"]
    ).get("my-parameter-name")
    return parameter_value


@asset
def example_parameter_store_asset_with_env(parameter_store: ParameterStoreResource):
    import os

    with parameter_store.parameters_in_environment():
        return os.getenv("my-other-parameter-name")


defs = Definitions(
    assets=[example_parameter_store_asset, example_parameter_store_asset_with_env],
    resources={
        "parameter_store": ParameterStoreResource(
            region_name="us-west-1",
            parameter_tags=[
                ParameterStoreTag(key="my-tag-key", values=["my-tag-value"])
            ],
            with_decryption=True,
        )
    },
)
```

### About AWS Systems Parameter Store

**AWS Systems Manager Parameter Store** is a secure storage service for configuration data management and secrets management. It allows you to store data such as passwords, database strings, and license codes as parameter values. You can then reference these parameters in your applications or scripts, ensuring that sensitive information isn't hard-coded or exposed in your codebase.

AWS Systems Manager Parameter Store integrates with AWS Identity and Access Management (IAM) to control access to parameters, and it supports encryption using AWS Key Management Service (KMS) to protect sensitive data. This service is essential for maintaining secure and manageable configurations across your AWS environment.
