---
description: Reference for the deployment configuration files used with Dagster+ Hybrid deployments, including build.yaml, container_context.yaml, and pyproject.toml.
sidebar_position: 1000
tags: [dagster-plus-feature]
title: Deployment configuration reference (Dagster+)
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';

<DagsterPlus />

Dagster+ Hybrid deployments use several configuration files to define how code locations are built, deployed, and run. These files are typically scaffolded by `dg plus deploy configure` and live in your project or workspace root.

| File                                               | Purpose                                                                 |
| -------------------------------------------------- | ----------------------------------------------------------------------- |
| [`build.yaml`](#buildyaml)                         | Docker image build settings (registry and build directory)              |
| [`container_context.yaml`](#container_contextyaml) | Infrastructure-specific runtime configuration (Kubernetes, ECS, Docker) |
| [`pyproject.toml`](#pyprojecttoml)                 | Project metadata including code location name, agent queue, and image   |

:::note

In older deployments not managed by the `dg` CLI, a single `dagster_cloud.yaml` file was used instead of these three files. For details, see [Legacy dagster_cloud.yaml format](#legacy-dagster_cloudyaml-format).

:::

## File locations

<Tabs>
<TabItem value="single_project" label="Single project">

```shell
my-project/
├── build.yaml
├── container_context.yaml   # optional
├── Dockerfile
├── pyproject.toml
├── src/
│   └── my_project/
│       ├── __init__.py
│       └── definitions.py
└── uv.lock
```

</TabItem>
<TabItem value="multiple_projects" label="Workspace (multiple projects)">

In a workspace, these files can exist at both the workspace root (shared defaults) and within individual projects (overrides). Project-level settings take precedence over workspace-level settings.

```shell
my-workspace/
├── build.yaml               # workspace-level defaults
├── container_context.yaml   # workspace-level defaults (optional)
├── dg.toml
└── projects/
    ├── data-eng/
    │   ├── build.yaml               # project-level overrides (optional)
    │   ├── container_context.yaml   # project-level overrides (optional)
    │   ├── Dockerfile
    │   ├── pyproject.toml
    │   └── src/
    └── ml-pipeline/
        ├── Dockerfile
        ├── pyproject.toml
        └── src/
```

</TabItem>
</Tabs>

## build.yaml

The `build.yaml` file defines Docker image build settings for Hybrid deployments. It contains only two fields:

```yaml
# build.yaml
registry: 764506304434.dkr.ecr.us-east-1.amazonaws.com/my-image
directory: ./
```

| Property    | Description                                         | Format                         | Default |
| ----------- | --------------------------------------------------- | ------------------------------ | ------- |
| `registry`  | The Docker registry to push the built image to      | `string` (Docker registry URL) |         |
| `directory` | The path to the directory containing the Dockerfile | `string` (path)                | `.`     |

The `registry` field specifies where Docker images are pushed during CI/CD. The `directory` field is useful when your `Dockerfile` or `pyproject.toml` is in a subdirectory rather than the project root.

### Workspace and project merging

When both workspace-level and project-level `build.yaml` files exist, settings are merged with project-level values taking precedence. A common pattern is to set `registry` at the workspace level and `directory` at the project level:

```yaml
# workspace-level build.yaml
registry: 764506304434.dkr.ecr.us-east-1.amazonaws.com/my-image
```

```yaml
# project-level build.yaml
directory: ./projects/data-eng
```

## container_context.yaml

The `container_context.yaml` file defines infrastructure-specific runtime configuration for code server and run containers. The available settings depend on which Hybrid agent platform you use.

All platforms support a shared top-level `env_vars` field:

```yaml
# container_context.yaml
env_vars:
  - DATABASE_NAME=staging
  - DATABASE_PASSWORD # pulled from agent environment
```

| Property   | Description                                                                                                                   | Format         |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------- | -------------- |
| `env_vars` | Environment variables for all containers. Use `KEY=VALUE` to set a value, or `KEY` alone to pull from the agent's environment | `list[string]` |

The platform-specific settings are nested under a key matching your agent platform. For example, a Kubernetes deployment might look like:

```yaml
# container_context.yaml
k8s:
  namespace: my-namespace
  env_secrets:
    - my-secret
```

For the full list of available settings, see the configuration reference for your agent platform:

- [Kubernetes agent configuration reference](/deployment/dagster-plus/hybrid/kubernetes/configuration)
- [Amazon ECS agent configuration reference](/deployment/dagster-plus/hybrid/amazon-ecs/configuration-reference)
- [Docker agent configuration reference](/deployment/dagster-plus/hybrid/docker/configuration)

## pyproject.toml

For projects managed with the `dg` CLI, several deployment settings are configured in `pyproject.toml` under the `[tool.dg.project]` section. These settings determine how the project is identified and routed during deployment.

```toml
# pyproject.toml
[tool.dg.project]
root_module = "my_project"
code_location_name = "my-project"
agent_queue = "special-queue"
image = "my-registry/my-image:latest"
```

| Property             | Description                                                                                                                                                              | Format                     |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------- |
| `root_module`        | **Required.** The root Python module containing Dagster definitions                                                                                                      | `string`                   |
| `code_location_name` | The name for this code location as it appears in the **Dagster UI**. Defaults to the project directory name                                                              | `string`                   |
| `agent_queue`        | Routes this code location to a specific agent queue. Useful when running [multiple agents](/deployment/dagster-plus/hybrid/multiple#routing-requests-to-specific-agents) | `string`                   |
| `image`              | A pre-built Docker image to use for this code location, skipping the build step entirely. This is an alternative to configuring a registry in `build.yaml`               | `string` (image reference) |

:::tip

If you use `dg.toml` instead of `pyproject.toml`, the same settings go under `[project]` instead of `[tool.dg.project]`.

:::

## Legacy dagster_cloud.yaml format

<details>
<summary>Expand for the legacy dagster_cloud.yaml reference</summary>

In older Dagster+ deployments not managed by the `dg` CLI, a single `dagster_cloud.yaml` file (sometimes also called `build.yaml`) was used to define all deployment configuration in one place. This format combines code location metadata, build settings, and container context into a single file.

:::warning

This format is supported for backwards compatibility. New projects should use the `dg` CLI with the separate `build.yaml`, `container_context.yaml`, and `pyproject.toml` files described above.

:::

### Structure

The file contains a single top-level `locations` key with a list of code location entries:

```yaml
# dagster_cloud.yaml
locations:
  - location_name: data-eng-pipeline
    code_source:
      package_name: example_etl
    build:
      directory: ./
      registry: localhost:5000/docker_image
    container_context:
      k8s:
        env_vars:
          - database_name
          - database_username=hooli_testing
        env_secrets:
          - database_password
    agent_queue: special-queue
  - location_name: ml-pipeline
    code_source:
      module_name: example_ml
    image: my-registry/my-image:latest
```

### Settings per location

| Property            | Description                                                                             | Required |
| ------------------- | --------------------------------------------------------------------------------------- | -------- |
| `location_name`     | The name of the code location as it appears in the **Dagster UI**                       | Yes      |
| `code_source`       | How to find Dagster definitions (see below)                                             | Yes      |
| `build`             | Docker build settings: `directory` and `registry`                                       | No       |
| `working_directory` | Directory to load code from, if different from the project root                         | No       |
| `executable_path`   | Path to the Python executable to use                                                    | No       |
| `image`             | Pre-built Docker image (alternative to `build`)                                         | No       |
| `container_context` | Infrastructure-specific runtime configuration (same schema as `container_context.yaml`) | No       |
| `agent_queue`       | Routes to a specific agent queue                                                        | No       |

### Code source

The `code_source` must contain exactly one of:

| Property                   | Description                                          |
| -------------------------- | ---------------------------------------------------- |
| `code_source.package_name` | Python package name containing Dagster definitions   |
| `code_source.module_name`  | Python module path containing Dagster definitions    |
| `code_source.python_file`  | Path to a Python file containing Dagster definitions |

### Defaults

You can set default values that apply to all locations using the `defaults` key:

```yaml
# dagster_cloud.yaml
defaults:
  build:
    registry: my-registry/my-image
  container_context:
    k8s:
      namespace: dagster
locations:
  - location_name: data-eng
    code_source:
      package_name: example_etl
  - location_name: ml-pipeline
    code_source:
      module_name: example_ml
```

</details>
