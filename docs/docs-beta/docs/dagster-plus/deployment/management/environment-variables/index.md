---
title: Environment variables
sidebar_position: 60
---

Environment variables, which are key-value pairs configured outside your source code, allow you to dynamically modify application behavior depending on environment.

Using environment variables, you can define various configuration options for your Dagster application and securely set up secrets. For example, instead of hard-coding database credentials - which is bad practice and cumbersome for development - you can use environment variables to supply user details. This allows you to parameterize your pipeline without modifying code or insecurely storing sensitive data.

There are two ways to declare and manage variables in Dagster+:

* Through the [Dagster+ UI](dagster-ui)
* With [agent configuration](agent-config).

|                             | Dagster+ UI | Agent configuration |
|-----------------------------|-------------|---------------------|
| **Deployment type support** | [Serverless](/dagster-plus/deployment/deployment-types/serverless/), [Hybrid](/dagster-plus/deployment/deployment-types/hybrid/) | [Hybrid](/dagster-plus/deployment/deployment-types/hybrid/) |
| **How it works** | Environment variables are managed in the Dagster+ UI. Values are pulled from storage and decrypted when your code is executed. | Environment variables are defined in the agent's configuration. Variables set at the code location level will pass through Dagster+, while those set at the deployment level bypass Dagster+ entirely. For more information, see "[Setting environment variables using agent config](agent-config)". |
| **Requirements** | <ul><li>Dagster code must use version 1.0.17 or later</li><li>If using [Hybrid](/dagster-plus/deployment/deployment-types/hybrid/), the agent must use Dagster version 1.0.17 or later</li><li>[Editor, Admin, or Organization Admin permissions](/dagster-plus/features/authentication-and-access-control/rbac/user-roles-permissions) in Dagster+. Note: Editors and Admins can only set environment variables for deployments where they're an Editor or Admin.</li></ul> | Ability to modify your dagster.yaml and [dagster_cloud.yaml](/dagster-plus/deployment/code-locations/dagster-cloud-yaml) files |
| **Limitations** | <ul><li>Maximum of 1,000 variables per full deployment</li><li>Variables must be less than or equal to 4KB in size</li><li>Variable names:<ul><li>Must be 512 characters or less in length</li><li>Must start with a letter or underscore</li><li>Must contain only letters, numbers, and underscores</li><li>May not be the same as [built-in (system) variables](built-in)</li></ul></li></ul> | Variable names: <ul><li>Must start with a letter or underscore</li><li>Must contain only letters, numbers, and underscores</li></ul> |
| **Storage and encryption** | Uses Amazon Key Management Services (KMS) and envelope encryption. For more information, see "[Setting environment variables in the Dagster+ UI](dagster-ui#storage-and-encryption)". | Dependent on agent type. |
| **Scope** | Scoped by deployment (full and branch) and optionally, code location. | Scoped by code location. Variables can be set for a full deployment (all code locations) or on a per-code location basis.|

