---
title: 'State-backed components'
description: Learn about state-backed components and how they integrate with external tools through persistent state management.
sidebar_position: 500
canonicalUrl: "/guides/build/components/state-backed-components"
slug: "/guides/build/components/state-backed-components"
---

import Beta from '@site/docs/partials/_Beta.md';

<Beta />

:::note Prerequisites

Before working with state-backed components, you should be familiar with the basic [Components](/guides/build/components) APIs.

:::

<PyObject section="components" module="dagster" object="StateBackedComponent" pluralize={true} /> are a specialized type of Dagster component designed to handle cases where your Dagster definitions depend on information from external systems or tools, rather than purely the code and configuration files in your repository.


## What is the "state" in state-backed components?

Some integrations require doing non-trivial work to turn their configuration into actual definition objects. For example:

- The <PyObject section="libraries" integration="fivetran" module="dagster_fivetran" object="FivetranAccountComponent" /> needs to fetch information about connectors and connection tables from the Fivetran API.
- The <PyObject section="libraries" integration="dbt" module="dagster_dbt" object="DbtProjectComponent" /> needs to compile a `manifest.json` file before definitions can be built.

In these cases, the "state" is the information that is collected and used to build the definitions for the component.

State-backed components simplify the process of managing this external state by providing a structured framework for recomputing, storing, and loading the state in a consistent way, to avoid having to do expensive computations every time a dagster process starts up.

## How state-backed components work

State-backed components extend the base <PyObject section="components" module="dagster" object="Component" /> class, but break up the process of building the definitions into two steps:

1. `write_state_to_path()`: The component does whatever work is necessary to compute the state (querying an API, running a script, etc.), and stores it to a file on local disk.
2. `build_defs_from_state()`: The component uses the state that was computed in the previous step to build the definitions.

Dagster system code controls the lifecycle of the state, ensuring that the `write_state_to_path()` method is called only at specific and limited points in time and that state is persisted in an accessible location for the `build_defs_from_state()` method to use when the component is loaded in other processes. 

The specifics of this process vary depending on the [state management strategy](/guides/build/components/state-backed-components#choosing-a-state-management-strategy) you configure, but regardless of the strategy chosen, `write_state_to_path()` will be called at most once per code location load.

:::note Local development

By default, when you run `dagster dev` or use `dg` CLI commands (like `dg list defs`), state-backed components automatically refresh their state. This provides convenience during development so you always see the latest metadata from external systems. You can disable this behavior by setting `refresh_if_dev` to `False` in your component configuration.

:::

## Choosing a state management strategy

State-backed components support three different strategies for managing state, each suited to different deployment patterns:

| Strategy | Storage Location | Best For |
|----------|-----------------|----------|
| Local Filesystem | `.local_defs_state/` directory | Docker/PEX deployments where state is updated during image builds |
| Versioned State Storage | Cloud storage (S3, GCS, etc.) | Deployments where you want to update state without rebuilding images |
| Code Server Snapshots | In-memory | Legacy compatibility only (not recommended) |

### Local Filesystem

**Best for:**
- Docker-based deployments
- CI/CD pipelines that build Docker or PEX images
- Simple, predictable deployments

**How it works:**
- You run `dg utils refresh-defs-state` during your build process
- State is stored in a `.local_defs_state` directory in your project
- The directory is automatically `.gitignore`d
- State becomes part of your deployment artifact (Docker or PEX image)

**Directory structure:**

When you refresh state, the system creates this structure:

```
my_project/
└── defs/
    └── .local_defs_state/
        ├── .gitignore  (auto-created)
        └── <defs_state_key>/
            └── state
```

:::tip Why not commit state to version control?

State files can be large and change frequently based on external system metadata. Committing them would pollute your Git history and create merge conflicts. Instead, state is refreshed during your build process and included in the deployment artifact.

:::

### Versioned State Storage

**Best for:**
- Deployments where you want to update state without rebuilding Docker or PEX images
- Environments requiring state version history

**How it works:**
- State is stored in cloud storage (S3, GCS, etc.) with UUID version identifiers
- Multiple versions can exist simultaneously
- All runs and definitions point to a consistent version until the code location reloads
- Requires configuring a state storage backend in your Dagster instance (see [Configuring versioned state storage](/guides/build/components/state-backed-components/configuring-versioned-state-storage) for more information)


**Benefits:**

This strategy allows you to update state in production without rebuilding Docker images. For example, you could write a Dagster job that:
1. Executes and updates component state
2. Reloads the code location to pick up the latest state version

### Code Server Snapshots (Legacy)

:::warning Not recommended

This is the default for many existing components only for backwards compatibility. This default will be changed in the 1.13.0 release. 

:::

State is automatically refreshed every time your code location loads and stored in memory. 

**Drawbacks:**
- If an external API is unavailable, your entire code location will fail to load
- Less control over the state refresh process (no way to roll back to a previous state version)
- Larger run artifacts (since state is attached to each run)

## Defs state keys

Each state-backed component instance is identified by a **defs state key**, which is an identifier that determines where its state is stored. The key typically follows the format:

```
ComponentClassName[discriminator]
```

For example:
- `TableauComponent[https://my-company.tableau.com/]`
- `FivetranAccountComponent[account_12345]`
- `DbtProjectComponent[my_project]`

The discriminator usually comes from the component's configuration (like a site name, account ID, or project name) to ensure that different instances of the same component type don't share state.

In some cases, it is desirable for multiple components to share the same key (and therefore the same state). For example, you may have multiple instances of the <PyObject section="libraries" integration="dbt" module="dagster_dbt" object="DbtProjectComponent" /> for the same project that cover different selections of models. In these cases, the system will allow these components to share the same state object.

You can view all defs state keys for a code location by navigating to the code location overview page in the Dagster UI, which contains:
- All registered state keys for that location
- The last time each state was updated
- The current version identifier for each state

## Common state-backed components

The following Dagster integrations are implemented as state-backed components:

- <PyObject section="libraries" integration="tableau" module="dagster_tableau" object="TableauComponent" /> - Syncs Tableau workspaces, dashboards, and data sources
- <PyObject section="libraries" integration="looker" module="dagster_looker" object="LookerComponent" /> - Syncs Looker explores and dashboards
- <PyObject section="libraries" integration="sigma" module="dagster_sigma" object="SigmaComponent" /> - Syncs Sigma workbooks and datasets
- <PyObject section="libraries" integration="powerbi" module="dagster_powerbi" object="PowerBIWorkspaceComponent" /> - Syncs Power BI dashboards and reports
- <PyObject section="libraries" integration="fivetran" module="dagster_fivetran" object="FivetranAccountComponent" /> - Syncs Fivetran connectors and connection tables
- <PyObject section="libraries" integration="airbyte" module="dagster_airbyte" object="AirbyteWorkspaceComponent" /> - Syncs Airbyte connections and tables
- <PyObject section="libraries" integration="dbt" module="dagster_dbt" object="DbtProjectComponent" /> - Uses dbt manifest files for project metadata

Each of these components handles the complexity of interacting with external APIs and managing state.

## Next steps

- Learn how to [configure state-backed components](/guides/build/components/state-backed-components/configuring-state-backed-components) in your project
- Understand how to [manage state in CI/CD](/guides/build/components/state-backed-components/managing-state-in-ci-cd) deployments
