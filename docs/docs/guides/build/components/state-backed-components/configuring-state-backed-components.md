---
title: 'Configuring state-backed components'
description: Learn how to configure state management strategies for state-backed components in your Dagster project.
sidebar_position: 100
---

import Beta from '@site/docs/partials/_Beta.md';

<Beta />

State-backed components provide flexible configuration options to control how state is fetched, stored, and updated. This guide explains the available configuration options and how to use them in your project.

## The defs_state configuration field

Most state-backed components include a `defs_state:` configuration field in their YAML definition. This field allows you to customize how the component manages its state.

### Basic configuration

Here's an example of a component with default state management:

```yaml
# defs.yaml
type: dagster_fivetran.FivetranAccountComponent
attributes:
  ...
```

By default, many components currently use the legacy code server snapshots strategy for backwards compatibility. This default will be changed in the 1.13.0 release. To use a different strategy, add the `defs_state` field:

```yaml
# defs.yaml
type: dagster_fivetran.FivetranAccountComponent
attributes:
  ...
  defs_state:
    management_type: LOCAL_FILESYSTEM
```

## Configuration options

The `defs_state` field supports three configuration options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `key` | `str` | Auto-generated | Override the state key identifier |
| `management_type` | `LOCAL_FILESYSTEM` \| `VERSIONED_STATE_STORAGE` \| `LEGACY_CODE_SERVER_SNAPSHOTS` | Component-specific | State management strategy (see [Choosing a state management strategy](/guides/build/components/state-backed-components#choosing-a-state-management-strategy)) |
| `refresh_if_dev` | `bool` | `true` | Auto-refresh state during local development |

### key

Override the default defs state key for this component instance. By default, components generate keys based on their class name and configuration (e.g., `TableauComponent[my_tableau_site]`).

#### Example

```yaml
defs_state:
  key: custom_tableau_key
  management_type: LOCAL_FILESYSTEM
```

You typically don't need to override the key unless you have specific naming requirements.

### management_type

Specify which state management strategy to use. See [Choosing a state management strategy](/guides/build/components/state-backed-components#choosing-a-state-management-strategy) for detailed guidance on which strategy to choose for your deployment.

Available options:

- `LOCAL_FILESYSTEM` - Stores state in a `.local_defs_state` directory inside your project
- `VERSIONED_STATE_STORAGE` - Stores state in remote storage with version tracking
- `LEGACY_CODE_SERVER_SNAPSHOTS` - Auto-refreshes state on code server load (not recommended)

#### Example

```yaml
defs_state:
  management_type: LOCAL_FILESYSTEM
```

### refresh_if_dev

Control whether state is automatically refreshed when running `dagster dev` or using `dg` CLI commands locally. Defaults to `true`.

#### Example

```yaml
defs_state:
  management_type: VERSIONED_STATE_STORAGE
  refresh_if_dev: false
```

Setting this to `false` can speed up local development if:
- Fetching state takes a long time
- You don't need the latest state for local development
- You want to avoid rate limits on external APIs


## Multiple components with the same type

If you have multiple instances of the same component type, each will typically have a different defs state key, and so will manage their own state independently.


## Viewing state in the Dagster UI

You can view state metadata for your code location in the Dagster UI:

1. Navigate to the **Deployment** tab
2. Select your code location
3. View the **Defs state** section

This shows:
- All registered defs state keys
- The last time each state was updated
- The current version identifier for each state key

## Next steps

- Learn how to [manage state in CI/CD](/guides/build/components/state-backed-components/managing-state-in-ci-cd) deployments
- Review the [Components guide](/guides/build/components) for general component usage
