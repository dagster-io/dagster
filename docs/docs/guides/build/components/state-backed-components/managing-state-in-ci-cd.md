---
title: 'Managing state in CI/CD'
description: Learn how to refresh and manage component state in production deployments using the dg CLI.
sidebar_position: 200
---

import Beta from '@site/docs/partials/_Beta.md';
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

<Beta />

This guide explains how to refresh state for both Local Filesystem and Versioned State Storage strategies while deploying your Dagster project.

:::tip Dagster+ users
If you're using Dagster+, the `dg scaffold github-actions` command will generate a GitHub Actions workflow that automatically refreshes state for all `StateBackedComponents` in your project.
:::

## Understanding state storage

Before configuring state refresh in your CI/CD pipeline, it's important to understand where component state is stored:

### Versioned State Storage

State is written to your Dagster instance:
- **Dagster+**: State is written to Dagster+ managed state storage
- **OSS**: State is written to a configured backend (S3, GCS, etc.) that you set up

### Local Filesystem

State is written to a `.local_defs_state` directory within your Python project, then copied into your Docker image or PEX build as part of your deployment artifact.

### Dagster+ vs OSS

In **Dagster+**, connecting to the instance and copying project files into your deployment artifact is handled automatically by the deployment process.

In **OSS**, you need to ensure these steps are followed accurately in your deployment configuration.

## OSS deployments

For OSS deployments, you'll run state refresh commands in your CI/CD pipeline before building your deployment artifacts.

### Refreshing state in CI/CD

Run state refresh commands in your CI/CD pipeline (GitHub Actions, GitLab CI, etc.) before building your deployment artifacts.

#### Basic steps

1. **Install uv**: `python -m pip install uv`
2. **Navigate to your project**: `cd path/to/your/project`
3. **Run refresh command**: `uv run dg utils refresh-defs-state`

#### Example: GitHub Actions workflow

```yaml
- name: Install uv
  run: python -m pip install uv
  
- name: Refresh component state
  run: |
    cd path/to/your/project
    uv run dg utils refresh-defs-state
  shell: bash
  
- name: Build Docker image
  run: docker build -t my-dagster-image .
```

### Making the instance available (Versioned State Storage)

If you're using Versioned State Storage, your refresh command needs access to your Dagster instance configuration.

#### Requirements

- Set the `DAGSTER_HOME` environment variable to point to a valid `dagster.yaml` file
- The `dagster.yaml` must be configured with your `defs_state_storage` backend
- Your environment must have credentials to access the storage backend (S3, GCS, etc.)

For more information on configuring state storage, see [Configuring versioned state storage](/guides/build/components/state-backed-components/configuring-versioned-state-storage).

#### Example: GitHub Actions with DAGSTER_HOME

```yaml
- name: Set up Dagster instance config
  run: |
    mkdir -p $HOME/dagster_home
    echo "$DAGSTER_YAML_CONTENT" > $HOME/dagster_home/dagster.yaml
  env:
    DAGSTER_YAML_CONTENT: ${{ secrets.DAGSTER_YAML }}
    
- name: Refresh defs state
  run: |
    cd path/to/your/project
    uv run dg utils refresh-defs-state
  env:
    DAGSTER_HOME: $HOME/dagster_home
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
  shell: bash
```

#### Kubernetes deployments

For Kubernetes deployments using Helm, you'll need to mount your instance ConfigMap into your pods to make the `dagster.yaml` configuration available using the `includeInstance` flag.

For more information, see [Customizing your Kubernetes deployment](/deployment/oss/deployment-options/kubernetes/customizing-your-deployment).

### Copying files into your Docker image (Local Filesystem)

When using Local Filesystem state storage, the `.local_defs_state` directory must be included in your Docker image.

#### How it works

1. After running the refresh command in CI/CD, the `.local_defs_state` directory exists in your project
2. When you copy your project files into the Docker image, this directory is automatically included
3. Your deployed code will have access to the refreshed state

#### Example: Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy project files (includes .local_defs_state directory)
COPY . /app/

# Install dependencies
RUN pip install -e .

# Your application will now have access to refreshed state
```

:::info .local_defs_state and version control

The `.local_defs_state` directory is automatically excluded from version control via an auto-generated `.gitignore` file. However, it **should** be included in your Docker image as part of your deployment artifact.

:::

## Dagster+ deployments

For Dagster+ deployments, most of the configuration is handled automatically by the builtin `dg plus deploy` commands.

### Scaffolded GitHub Actions

If you use `dg scaffold github-actions` to generate your deployment workflow, state refresh is included by default. You don't need to configure anything additional.

### Manual configuration

If you're manually configuring your deployment workflow, add a state refresh step after the `ci-init` step.

#### Basic steps

1. **Install uv**: `python -m pip install uv`
2. **Navigate to your project**: `cd path/to/your/project`
3. **Run refresh command**: `uv run dg plus deploy refresh-defs-state`

This command automatically handles both storage types:
- **Local Filesystem**: State is written to `.local_defs_state`, which is later copied into your deployment artifact
- **Versioned State Storage**: The deployment environment has credentials to write state to Dagster+ managed state storage

#### Example: GitHub Actions workflow

```yaml
  - name: Initialize build session
    id: ci-init
    uses: dagster-io/dagster-cloud-action/actions/utils/dg-deploy-init@vX.Y.Z
  # ... ci-init configuration ...
  
- name: Refresh defs state
  run: |
    python -m pip install uv
    cd path/to/your/project
    uv run dg plus deploy refresh-defs-state
  shell: bash

# ... other deployment steps ...
  
```

For more information on Dagster+ deployment commands, see the [CI/CD deployment guide](/deployment/dagster-plus/deploying-code/ci-cd/).

## Checking state status

After refreshing state, you can verify the update in the Dagster UI:

1. Navigate to the **Deployment** tab
2. Select your code location
3. View the **Defs state** section

You'll see:
- All registered defs state keys
- The last updated timestamp for each key
- The current version identifier for each key

## Handling state refresh failures

If your state refresh command fails (for example, due to API errors or network issues), the CLI exits with a non-zero status code. This typically causes your build process to fail, preventing deployment with stale or missing state.

:::tip Handling refresh failures

Common causes and solutions:
- **Invalid credentials**: Verify API keys and secrets are correct and not expired
- **Network connectivity**: Ensure your CI/CD environment can reach external APIs
- **Rate limiting**: Space out refreshes or request higher rate limits from providers
- **Service outages**: Monitor external service status pages
- **Transient errors**: Add retry logic with exponential backoff to your deployment scripts

:::

## Next steps

- Review how to [configure state-backed components](/guides/build/components/state-backed-components/configuring-state-backed-components)
- Learn about the [Components system](/guides/build/components) in general
