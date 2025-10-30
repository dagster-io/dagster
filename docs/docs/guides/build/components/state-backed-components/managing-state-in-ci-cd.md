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

## Before you begin

Ensure your project is installed in the current environment (e.g. GitHub Actions, Docker, etc.) where you'll run state refresh commands.

<Tabs groupId="package-manager">
<TabItem value="uv" label="uv">

```bash
uv pip install -e .
```

</TabItem>
<TabItem value="pip" label="pip">

```bash
pip install -e .
```

</TabItem>
</Tabs>

## Refreshing state for Local Filesystem components

If your components use the `LOCAL_FILESYSTEM` state management type, you typically refresh state during your CI/CD pipeline as part of building your Docker image.

### Basic refresh command

Run this command to refresh state for all Local Filesystem components:

```bash
dg utils refresh-defs-state --management-type LOCAL_FILESYSTEM
```

This command:
1. Discovers and loads all state-backed components in your project
2. Filters to only those using `LOCAL_FILESYSTEM` management type
3. Fetches fresh state from each external system (Tableau, Fivetran, etc.)
4. Writes the state to the `.local_defs_state` directory in your project
5. Reports success or failure for each component

### Example: Dockerfile with state refresh

Here's a Dockerfile that refreshes state during the image build process:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy project files
COPY . /app/

# Install dependencies
RUN pip install -e .

# Refresh component state during build
RUN dg utils refresh-defs-state --management-type LOCAL_FILESYSTEM
```

This approach:
1. Installs your project and its dependencies
2. Runs `dg utils refresh-defs-state` to fetch fresh state from external APIs
3. Stores the state in the `.local_defs_state` directory within the image

This causes the state to become part of your deployment artifact.

:::info .local_defs_state and version control

The `.local_defs_state` directory is automatically excluded from version control via an auto-generated `.gitignore` file. However, it **should** be included in your Docker image as part of your deployment artifact.

:::


## Refreshing state for Versioned State Storage components

If your components use the `VERSIONED_STATE_STORAGE` state management type, the refresh workflow differs between OSS and Dagster+ deployments.

### Dagster+ deployments

For Dagster+ deployments, use the specialized `dg plus deploy` command during your GitHub or GitLab build:

```bash
dg plus deploy refresh-defs-state
```

This should be executed *after* the `init` step.

:::note

This command should *not* be executed inside a Dockerfile, as it relies on having access to the configuration available within the deploy context.

:::

This command automatically:
1. Uses your Dagster+ credentials to access the cloud instance
2. Refreshes state for all `VERSIONED_STATE_STORAGE` components
3. Uploads state to Dagster+'s managed state storage
4. Updates version metadata in the Dagster+ instance

For more information on deployment commands, see [CI/CD guide](/deployment/dagster-plus/deploying-code/ci-cd).

**Example: Dagster+ Github Action step**

Here's an example of a Github Action step that refreshes state for Versioned State Storage components:

```yaml
    - name: Refresh defs state
      if: steps.prerun.outputs.result != 'skip'
      run: |
        python -m pip install uv
        cd path/to/project
        uv run dg plus deploy refresh-defs-state
      shell: bash
```

It first installs `uv`, then executes the `dg plus deploy refresh-defs-state` command (`uv run` will automatically install your project into a new virtual environment). Once this completes, new state for all of your `VERSIONED_STATE_STORAGE` components will be uploaded to Dagster+'s managed state storage, and your build metadata will be updated with pointers to the new state.

### OSS deployments

For OSS deployments, you first need to configure a state storage backend in your Dagster instance (see [Configuring versioned state storage](/guides/build/components/state-backed-components/configuring-versioned-state-storage) for more information).

#### Refreshing state

For OSS deployments with Versioned State Storage configured, run:

```bash
dg utils refresh-defs-state --management-type VERSIONED_STATE_STORAGE
```

This command:
1. Discovers all state-backed components using `VERSIONED_STATE_STORAGE`
2. Fetches fresh metadata from each external system
3. Generates a new UUID version identifier for each state
4. Uploads state to your configured state storage backend (S3, GCS, etc.)
5. Updates the instance database with the new version identifiers

The specifics of how and where you run this command will depend on your deployment strategy, but you must have access to your production `DagsterInstance` in order for state to be written to the correct spot.

In a k8s+helm deployment, this would mean mouting your instance ConfigMap into your pod. For more information, see [Customizing your Kubernetes deployment](/deployment/oss/deployment-options/kubernetes/customizing-your-deployment).

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
