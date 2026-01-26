---
title: AWS Components
sidebar_label: Components
sidebar_position: 1
description: Configuration-driven AWS resources using Dagster Components.
tags: [dagster-supported, aws, components]
---

<p>{frontMatter.description}</p>

The `dagster-aws` library provides a set of components that allow you to configure AWS resources directly in YAML. These components wrap existing `dagster-aws` resources, enabling faster setup and better reusability.

## Installation

<PackageInstallInstructions packageName="dagster-aws" />

## Credentials configuration

All AWS components use a unified credential resolution pattern. You can provide credentials **inline** or **reference** a standalone component.

### Shared Credential Components

- **`Boto3CredentialsComponent`**: Standard AWS SDK (Boto3) configuration.
- **`S3CredentialsComponent`**: Specialized for S3, including unsigned session support.
- **`AthenaCredentialsComponent`**: Athena-specific settings (workgroups, polling).
- **`RedshiftCredentialsComponent`**: Redshift connection settings (host, port, sslmode).

## Service Components

### Amazon S3

Components for interacting with S3 buckets and managing files.

- **`S3ResourceComponent`**: Provides a standard `S3Resource`.
- **`S3FileManagerComponent`**: Provides an `S3FileManager` for artifact storage.

### AWS Systems Manager (SSM)

Manage configurations and parameters.

- **`SSMResourceComponent`**: Standard client for SSM operations.
- **`ParameterStoreResourceComponent`**: Fetches parameters and supports nested `ParameterStoreTag` objects.

### AWS Secrets Manager

Manage and fetch secrets securely.

- **`SecretsManagerResourceComponent`**: General client for Secrets Manager.
- **`SecretsManagerSecretsResourceComponent`**: Efficiently fetches specific secret ARNs.

### Database and Query Services

- **`AthenaClientResourceComponent`**: Executes SQL queries through Amazon Athena.
- **`RedshiftClientResourceComponent`**: Connects to and queries Amazon Redshift.
- **`RDSResourceComponent`**: Interacts with Amazon RDS instances.

### Container Registry

- **`ECRPublicResourceComponent`**: Retrieves login passwords for AWS Public ECR.

## Examples

### Inline Credentials

Perfect for simple setups where credentials are used by a single service.

```yaml
type: dagster_aws.ParameterStoreResourceComponent
attributes:
  credentials:
    region_name: us-west-2
  parameters:
    - /myapp/db/password
  resource_key: parameter_store
```

### Component Referencing

Best for production environments where credentials are shared across multiple services.

```yaml
type: dagster_aws.S3ResourceComponent
attributes:
  credentials: "{{ context.load_component('shared/aws_credentials') }}"
  resource_key: s3
```
