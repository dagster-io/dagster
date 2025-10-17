---
title: 'Configuring state-backed components'
description: Learn how to configure state management strategies for state-backed components in your Dagster project.
sidebar_position: 100
---

import Beta from '@site/docs/partials/_Beta.md';

<Beta />

State-backed components provide flexible configuration options to control how state is fetched, stored, and updated. This guide explains the available configuration options and how to choose the right strategy for your deployment.

## The defs_state configuration field

Most state-backed components include a `defs_state:` configuration field in their YAML definition. This field allows you to customize how the component manages its state.

### Basic configuration

Here's an example of a Tableau component with default state management:

```yaml
# defs.yaml
components:
  tableau_workspace:
    type: dagster_tableau.TableauComponent
    attributes:
      workspace:
        site_name: my_tableau_site
        connected_app_client_id:
          env: TABLEAU_CLIENT_ID
        connected_app_secret_id:
          env: TABLEAU_SECRET_ID
        connected_app_secret_value:
          env: TABLEAU_SECRET_VALUE
        server_name: https://my-company.tableau.com
```

By default, most components use the legacy code server snapshots strategy. To use a different strategy, add the `defs_state` field:

```yaml
# defs.yaml
components:
  tableau_workspace:
    type: dagster_tableau.TableauComponent
    attributes:
      workspace:
        site_name: my_tableau_site
        connected_app_client_id:
          env: TABLEAU_CLIENT_ID
        connected_app_secret_id:
          env: TABLEAU_SECRET_ID
        connected_app_secret_value:
          env: TABLEAU_SECRET_VALUE
        server_name: https://my-company.tableau.com
      defs_state:
        type: LOCAL_FILESYSTEM
```

## Configuration options

The `defs_state` field supports three configuration options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `key` | `str` | Auto-generated | Override the state key identifier |
| `type` | `LOCAL_FILESYSTEM` \| `VERSIONED_STATE_STORAGE` \| `LEGACY_CODE_SERVER_SNAPSHOTS` | Component-specific | State management strategy |
| `refresh_if_dev` | `bool` | `true` | Auto-refresh state in `dagster dev` mode |

### key

Override the default defs state key for this component instance. By default, components generate keys based on their class name and configuration (e.g., `TableauComponent[my_tableau_site]`).

```yaml
defs_state:
  key: custom_tableau_key
  type: LOCAL_FILESYSTEM
```

You typically don't need to override the key unless you have specific naming requirements.

### type

Specify which state management strategy to use. Available options:

- `LOCAL_FILESYSTEM` - Stores state in `.local_defs_state` directory (recommended)
- `VERSIONED_STATE_STORAGE` - Stores state in cloud storage with version tracking
- `LEGACY_CODE_SERVER_SNAPSHOTS` - Auto-refreshes state on code server load (not recommended)

```yaml
defs_state:
  type: LOCAL_FILESYSTEM
```

### refresh_if_dev

Control whether state is automatically refreshed when running `dagster dev` or using `dg` CLI commands locally. Defaults to `true`.

```yaml
defs_state:
  type: VERSIONED_STATE_STORAGE
  refresh_if_dev: true
```

Setting this to `false` can speed up local development if:
- Fetching state takes a long time
- You don't need the latest state for local development
- You want to avoid rate limits on external APIs

## Choosing a state management strategy

### Local Filesystem (Recommended)

**Best for:**
- Docker-based deployments
- CI/CD pipelines that build Docker images
- Simple, predictable deployments

**How it works:**
- State is stored in a `.local_defs_state` directory in your project
- You run `dg utils refresh-defs-state` during your build process
- The directory is automatically `.gitignore`d (don't commit state to version control)
- State becomes part of your deployment artifact (Docker image)

**Example configuration:**

```yaml
# defs.yaml
components:
  fivetran_workspace:
    type: dagster_fivetran.FivetranAccountComponent
    attributes:
      workspace:
        account_id:
          env: FIVETRAN_ACCOUNT_ID
        api_key:
          env: FIVETRAN_API_KEY
        api_secret:
          env: FIVETRAN_API_SECRET
      defs_state:
        type: LOCAL_FILESYSTEM
```

**Directory structure:**

When you refresh state, the component creates this structure:

```
my_project/
├── defs.yaml
└── my_defs/
    └── .local_defs_state/
        ├── .gitignore  (auto-created)
        └── FivetranAccountComponent[account_12345]/
            └── state
```

The `.gitignore` file ensures state files aren't committed to version control.

:::tip Why not commit state to version control?

State files can be large and change frequently based on external system metadata. Committing them would pollute your Git history and create merge conflicts. Instead, state is refreshed during your build process and included in the deployment artifact.

:::

### Versioned State Storage

**Best for:**
- Deployments where you want to update state without rebuilding Docker images
- Dagster+ deployments
- Dynamic workflows that update state and reload code locations

**How it works:**
- State is stored in cloud storage (S3, GCS, etc.) with UUID version identifiers
- Multiple versions can exist simultaneously
- All runs and definitions point to a consistent version until the code location reloads
- Requires configuring a state storage backend in your Dagster instance

**Example configuration:**

```yaml
# defs.yaml
components:
  tableau_workspace:
    type: dagster_tableau.TableauComponent
    attributes:
      workspace:
        site_name: my_tableau_site
        connected_app_client_id:
          env: TABLEAU_CLIENT_ID
        connected_app_secret_id:
          env: TABLEAU_SECRET_ID
        connected_app_secret_value:
          env: TABLEAU_SECRET_VALUE
        server_name: https://my-company.tableau.com
      defs_state:
        type: VERSIONED_STATE_STORAGE
```

**Instance configuration (OSS deployments):**

For OSS deployments, you need to configure a state storage backend in your `dagster.yaml`:

```yaml
# dagster.yaml
defs_state_storage:
  module: dagster._core.storage.defs_state
  class: S3DefsStateStorage
  config:
    base_dir: s3://my-bucket/dagster/defs-state
```

The `base_dir` should be a UPath-compatible URI pointing to your cloud storage:
- S3: `s3://bucket-name/path`
- GCS: `gs://bucket-name/path`
- Azure: `az://container-name/path`

Ensure your Dagster instance has appropriate credentials to access this storage location.

:::info Cloud storage authentication

Your Dagster instance uses standard cloud provider authentication:
- **S3**: AWS credentials via IAM roles, environment variables, or ~/.aws/credentials
- **GCS**: Google Cloud credentials via service accounts or Application Default Credentials
- **Azure**: Azure credentials via managed identities or connection strings

The instance must have read and write permissions to the specified `base_dir` location.

:::

**Benefits of versioned storage:**

This strategy allows you to update state in production without rebuilding Docker images. For example, you could write a Dagster job that:
1. Executes and updates component state
2. Reloads the code location to pick up the latest state version
3. Continues with new definitions, much faster than rebuilding a Docker image

### Code Server Snapshots (Legacy)

**Not recommended for new deployments.** This strategy automatically refreshes state every time your code location loads, storing it in memory.

**Drawbacks:**
- If the external API is unavailable, your entire code location fails to load
- No version consistency during code location lifetime
- Slower code location startup times
- Can hit API rate limits during development

:::warning Not recommended

This is the default for many existing components only for backwards compatibility. New projects should use Local Filesystem or Versioned State Storage instead.

:::

## Local development behavior

When you run `dagster dev` or use `dg` CLI commands (like `dg list defs`), state-backed components automatically refresh their state by default. This provides convenience during development so you always see the latest metadata from external systems.

To disable automatic refresh in development:

```yaml
defs_state:
  type: VERSIONED_STATE_STORAGE
  refresh_if_dev: false
```

This can be useful if:
- State fetching takes a long time (30+ seconds)
- You're working offline or have intermittent network connectivity
- You want to avoid hitting API rate limits
- You don't need the absolute latest state for your current development task

## Multiple components with the same type

If you have multiple instances of the same component type, each will have its own state key and state storage:

```yaml
# defs.yaml
components:
  tableau_workspace_prod:
    type: dagster_tableau.TableauComponent
    attributes:
      workspace:
        site_name: production_site
        # ... other config ...
      defs_state:
        type: LOCAL_FILESYSTEM

  tableau_workspace_staging:
    type: dagster_tableau.TableauComponent
    attributes:
      workspace:
        site_name: staging_site
        # ... other config ...
      defs_state:
        type: LOCAL_FILESYSTEM
```

This creates two separate state keys:
- `TableauComponent[production_site]`
- `TableauComponent[staging_site]`

Each maintains its own state independently.

## Viewing state in the Dagster UI

You can view state metadata for your code location in the Dagster UI:

1. Navigate to the **Deployment** tab
2. Select your code location
3. View the **Defs state** section

This shows:
- All registered defs state keys
- The last time each state was updated
- The current version identifier for each state key

Note: The UI shows metadata only. You cannot view or download the actual state contents from the UI.

## Next steps

- Learn how to [manage state in production](/guides/build/components/state-backed-components/managing-state-in-production) deployments
- Review the [Components guide](/guides/build/components) for general component usage
