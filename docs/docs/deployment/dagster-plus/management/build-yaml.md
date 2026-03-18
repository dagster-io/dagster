---
description: Configuration files for Dagster+ deployments - build.yaml, container_context.yaml, and pyproject.toml.
sidebar_position: 1000
tags: [dagster-plus-feature]
title: Deployment configuration reference (Dagster+)
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';

<DagsterPlus />

Dagster+ uses several configuration files to manage deployments. This page describes each file and what configuration belongs in each.

## Overview

Modern Dagster+ projects use three separate configuration files, each with a specific purpose:

| File                                               | Purpose                                                 | Required    |
| -------------------------------------------------- | ------------------------------------------------------- | ----------- |
| [`build.yaml`](#buildyaml)                         | Docker build settings (directory, registry)             | Hybrid only |
| [`container_context.yaml`](#container_contextyaml) | Agent-specific runtime configuration (K8s, ECS, Docker) | Optional    |
| [`pyproject.toml`](#pyprojecttoml)                 | Project settings (code location name, root module)      | Yes         |

:::note

In older deployments, you may have a `dagster_cloud.yaml` file that combines all of these settings. This format is deprecated but still supported. See [Legacy format](#legacy-format-dagster_cloudyaml) for migration guidance.

:::

## File locations

<Tabs>
<TabItem value="single_project" label="Single project">

```shell
my-project
├── build.yaml              # Build configuration (hybrid only)
├── container_context.yaml  # Runtime configuration (optional)
├── Dockerfile
├── pyproject.toml          # Project configuration
├── README.md
├── src
│   └── my_project
│       ├── __init__.py
│       ├── definitions.py
│       └── defs
│           └── __init__.py
├── tests
│   └── __init__.py
└── uv.lock
```

</TabItem>
<TabItem value="multiple_projects" label="Workspace (multiple projects)">

In a workspace, configuration files can exist at both the workspace and project levels:

```shell
my-workspace
├── build.yaml              # Workspace-level build config (shared registry)
├── container_context.yaml  # Workspace-level runtime config
├── dg.toml                 # Workspace configuration
└── projects
    ├── project-a
    │   ├── build.yaml              # Project-specific build config (optional)
    │   ├── container_context.yaml  # Project-specific runtime config (optional)
    │   ├── Dockerfile
    │   └── pyproject.toml
    └── project-b
        ├── build.yaml
        ├── container_context.yaml
        ├── Dockerfile
        └── pyproject.toml
```

</TabItem>
</Tabs>

## build.yaml

The `build.yaml` file configures Docker image building for **Hybrid deployments only**. Serverless deployments do not require this file.

### Basic structure

```yaml
# build.yaml

# Container registry URL for pushing Docker images.
# Examples:
#   ECR:       123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo
#   GCR:       gcr.io/my-project/my-image
#   Azure:     myregistry.azurecr.io/my-image
#   DockerHub: docker.io/myuser/my-image
#   GHCR:      ghcr.io/myorg/my-image
registry: '123456789012.dkr.ecr.us-east-1.amazonaws.com/my-dagster-image'

# Path to the directory containing the Dockerfile (defaults to current directory)
directory: .
```

### Settings

| Property    | Description                                     | Format                  | Default |
| ----------- | ----------------------------------------------- | ----------------------- | ------- |
| `registry`  | The Docker registry URL to push images to       | `string` (registry URL) | -       |
| `directory` | Path to the directory containing the Dockerfile | `string` (path)         | `.`     |

### Workspace vs project configuration

In a workspace with multiple projects:

- **Workspace-level `build.yaml`**: Define a shared `registry` that applies to all projects
- **Project-level `build.yaml`**: Override with project-specific settings if needed

```yaml
# Workspace build.yaml
registry: '123456789012.dkr.ecr.us-east-1.amazonaws.com/shared-registry'
```

```yaml
# Project build.yaml (inherits registry from workspace)
directory: .
# registry: '...'  # Uncomment to override workspace registry
```

## container_context.yaml

The `container_context.yaml` file configures agent-specific runtime settings for Hybrid deployments. This includes environment variables, secrets, resource limits, and other platform-specific configuration.

### Kubernetes agent

```yaml
# container_context.yaml (Kubernetes)

k8s:
  server_k8s_config: # Config for code servers launched by the agent
    pod_spec_config:
      node_selector:
        disktype: standard
    pod_template_spec_metadata:
      annotations:
        mykey: myvalue
    container_config:
      resources:
        limits:
          cpu: 100m
          memory: 128Mi
  run_k8s_config: # Config for runs launched by the agent
    pod_spec_config:
      node_selector:
        disktype: ssd
    container_config:
      resources:
        limits:
          cpu: 500m
          memory: 1024Mi
    pod_template_spec_metadata:
      annotations:
        mykey: myvalue
    job_spec_config:
      ttl_seconds_after_finished: 7200
```

For complete Kubernetes configuration options, see the [Kubernetes agent configuration reference](/deployment/dagster-plus/hybrid/kubernetes/configuration).

### Amazon ECS agent

```yaml
# container_context.yaml (ECS)

ecs:
  env_vars:
    - DATABASE_NAME=staging
    - DATABASE_PASSWORD
  secrets:
    - name: 'MY_API_TOKEN'
      valueFrom: 'arn:aws:secretsmanager:us-east-1:123456789012:secret:FOO-AbCdEf:token::'
  server_resources:
    cpu: '256'
    memory: '512'
  run_resources:
    cpu: '4096'
    memory: '16384'
  execution_role_arn: arn:aws:iam::123456789012:role/MyECSExecutionRole
  task_role_arn: arn:aws:iam::123456789012:role/MyECSTaskRole
```

For complete ECS configuration options, see the [Amazon ECS agent configuration reference](/deployment/dagster-plus/hybrid/amazon-ecs/configuration-reference).

### Docker agent

```yaml
# container_context.yaml (Docker)

docker:
  env_vars:
    - DATABASE_NAME=staging
    - DATABASE_PASSWORD
```

For complete Docker configuration options, see the [Docker agent configuration reference](/deployment/dagster-plus/hybrid/docker/configuration).

## pyproject.toml

Project settings are configured in `pyproject.toml` under the `[tool.dg]` section. This includes the code location name, root module, and other project-level settings.

### Basic structure

```toml
# pyproject.toml

[tool.dg]
directory_type = "project"

[tool.dg.project]
# The root Python module for this project (required)
root_module = "my_project"

# Custom name for the code location (optional)
# Defaults to the project name (hyphenated variant of root_module)
code_location_name = "my-custom-location-name"

# Module containing the top-level Definitions object (optional)
# Defaults to <root_module>.definitions
code_location_target_module = "my_project.definitions"

# Module where new components are scaffolded (optional)
# Defaults to <root_module>.defs
defs_module = "my_project.defs"
```

### Settings

| Property                      | Description                                             | Default                     |
| ----------------------------- | ------------------------------------------------------- | --------------------------- |
| `root_module`                 | The root Python module for the project                  | Required                    |
| `code_location_name`          | Custom name shown in the Dagster UI Code Locations page | Project name (hyphenated)   |
| `code_location_target_module` | Module containing the `Definitions` object              | `<root_module>.definitions` |
| `defs_module`                 | Module where new components are scaffolded              | `<root_module>.defs`        |

For complete `pyproject.toml` configuration options, see [Installing and configuring the dg CLI](/api/clis/dg-cli/dg-cli-configuration).

## Legacy format (dagster_cloud.yaml) {#legacy-format-dagster_cloudyaml}

Older Dagster+ deployments may use a single `dagster_cloud.yaml` (or `build.yaml` with the legacy format) that combines all configuration. This format is deprecated but still supported for backwards compatibility.

<details>
<summary>Legacy format reference</summary>

The legacy format uses a `locations` key containing a list of code location configurations:

```yaml
# dagster_cloud.yaml (legacy format)
locations:
  - location_name: data-eng-pipeline
    code_source:
      package_name: example_etl
    build:
      directory: ./example_etl
      registry: localhost:5000/docker_image
    working_directory: ./project_directory
    executable_path: venvs/path/to/python
    container_context:
      k8s:
        env_vars:
          - database_name
          - database_username=hooli_testing
        env_secrets:
          - database_password
```

### Legacy settings reference

#### Location name

| Property        | Description                                                                              | Format   |
| --------------- | ---------------------------------------------------------------------------------------- | -------- |
| `location_name` | The name of your Dagster project that will appear in the Dagster UI Code locations page. | `string` |

#### Code source

| Property                   | Description                                         | Format                   |
| -------------------------- | --------------------------------------------------- | ------------------------ |
| `code_source.package_name` | The name of a package containing Dagster code       | `string` (folder name)   |
| `code_source.python_file`  | The name of a Python file containing Dagster code   | `string` (.py file name) |
| `code_source.module_name`  | The name of a Python module containing Dagster code | `string` (module name)   |

#### Build

| Property          | Description                                         | Format                     | Default |
| ----------------- | --------------------------------------------------- | -------------------------- | ------- |
| `build.directory` | The path to the directory containing the Dockerfile | `string` (path)            | `.`     |
| `build.registry`  | The Docker registry to push images to (Hybrid only) | `string` (docker registry) |         |

#### Working directory

| Property            | Description                                                             | Format          |
| ------------------- | ----------------------------------------------------------------------- | --------------- |
| `working_directory` | The path of the directory that Dagster should load the code source from | `string` (path) |

#### Python executable

| Property          | Description                                   | Format          |
| ----------------- | --------------------------------------------- | --------------- |
| `executable_path` | The file path of the Python executable to use | `string` (path) |

#### Container context

The `container_context` key accepts agent-specific configuration. Refer to the agent configuration references:

- [Docker agent configuration reference](/deployment/dagster-plus/hybrid/docker/configuration)
- [Amazon ECS agent configuration reference](/deployment/dagster-plus/hybrid/amazon-ecs/configuration-reference)
- [Kubernetes agent configuration reference](/deployment/dagster-plus/hybrid/kubernetes/configuration)

### Migrating from legacy format

To migrate from the legacy format:

1. **Move build settings to `build.yaml`**:

   ```yaml
   # build.yaml
   directory: ./example_etl
   registry: localhost:5000/docker_image
   ```

2. **Move container context to `container_context.yaml`**:

   ```yaml
   # container_context.yaml
   k8s:
     env_vars:
       - database_name
       - database_username=hooli_testing
     env_secrets:
       - database_password
   ```

3. **Move project settings to `pyproject.toml`**:

   ```toml
   # pyproject.toml
   [tool.dg]
   directory_type = "project"

   [tool.dg.project]
   root_module = "example_etl"
   code_location_name = "data-eng-pipeline"
   ```

4. **Delete the `dagster_cloud.yaml` file** once migration is complete.

</details>
