---
title: 'State-backed components'
description: Learn about state-backed components and how they integrate with external tools through persistent state management.
sidebar_position: 500
---

State-backed components are a specialized type of Dagster component designed to handle cases where your Dagster definitions depend on information from external systems accessed through web APIs.

:::note Prerequisites

Before working with state-backed components, you should be familiar with the basic [Components](/guides/build/components) concept.

:::

## What are state-backed components?

Most Dagster components produce definitions based solely on the code and configuration files (like `defs.yaml`) in your repository. However, some integrations need to fetch metadata from external systems to build their definitions.

For example:
- **Fivetran** components need to query the Fivetran API to discover which connectors exist and what tables they sync
- **Tableau** components need to fetch information about workspaces, dashboards, and data sources
- **Looker** components need to retrieve explore and dashboard definitions
- **dbt** components need to read the generated manifest file to understand the project structure

State-backed components simplify the process of managing, tracking, and updating this external state by providing a structured framework for fetching, storing, and versioning state data.

## How state-backed components work

State-backed components extend the base <PyObject section="components" module="dagster" object="Component" /> class with additional capabilities:

1. **Fetching state**: Each component knows how to query its external system and retrieve the necessary metadata
2. **Storing state**: The fetched state is persisted using one of several storage strategies
3. **Building definitions**: Components use the stored state to generate Dagster assets, jobs, and other definitions
4. **Versioning**: State changes are tracked with version identifiers, ensuring consistency across runs

When you use a state-backed component, the component handles all the complexity of fetching and managing state, so you can focus on building your data pipelines.

## State management strategies

State-backed components support three different strategies for managing state, each suited to different deployment patterns:

### Local Filesystem (Recommended)

State is stored in a `.local_defs_state` directory within your project. This approach is ideal for:
- Docker-based deployments where state is updated during image builds
- Simple deployment workflows
- Local development

With this strategy, you run `dg utils refresh-defs-state` during your CI/CD pipeline to update state, and the updated state becomes part of your deployment artifact.

### Versioned State Storage

State is stored in cloud storage (S3, GCS, etc.) with unique version identifiers. This approach is ideal for:
- Deployments where you want to update state without rebuilding Docker images
- Dynamic workflows that update state and reload code locations
- Dagster+ deployments

This strategy requires configuring a state storage backend in your Dagster instance, but provides more flexibility for updating state in production.

### Code Server Snapshots (Legacy)

State is automatically refreshed every time your code location loads and stored in memory. This approach is:
- The default for many existing components (for backwards compatibility)
- **Not recommended for new deployments** due to reliability concerns
- Problematic if external APIs are unavailable, as your entire code location may fail to load

For new projects, we recommend using **Local Filesystem** for its simplicity and reliability.

## Common state-backed components

The following Dagster integrations are implemented as state-backed components:

- <PyObject section="libraries" module="dagster_tableau" object="TableauComponent" /> - Syncs Tableau workspaces, dashboards, and data sources
- <PyObject section="libraries" module="dagster_looker" object="LookerComponent" /> - Syncs Looker explores and dashboards
- <PyObject section="libraries" module="dagster_sigma" object="SigmaComponent" /> - Syncs Sigma workbooks and datasets
- <PyObject section="libraries" module="dagster_powerbi" object="PowerBIWorkspaceComponent" /> - Syncs Power BI dashboards and reports
- <PyObject section="libraries" module="dagster_fivetran" object="FivetranAccountComponent" /> - Syncs Fivetran connectors and connection tables
- <PyObject section="libraries" module="dagster_airbyte" object="AirbyteWorkspaceComponent" /> - Syncs Airbyte connections and tables
- <PyObject section="libraries" module="dagster_dbt" object="DbtProjectComponent" /> - Uses dbt manifest files for project metadata
- <PyObject section="libraries" module="dagster_airlift" object="AirflowInstanceComponent" /> - Syncs Airflow DAGs and tasks

Each of these components handles the complexity of interacting with external APIs and managing state, so you can focus on building your data pipelines.

## Understanding defs state keys

Each state-backed component instance is identified by a **defs state key** - a unique identifier that determines where its state is stored. The key typically follows the format:

```
ComponentClassName[discriminator]
```

For example:
- `TableauComponent[my_site_name]`
- `FivetranAccountComponent[account_12345]`
- `DbtProjectComponent[my_project]`

The discriminator is usually derived from the component's configuration (like a site name, account ID, or project name) to ensure that different instances of the same component type don't share state.

You can view all defs state keys for a code location by navigating to the code location overview page in the Dagster UI, where you'll see:
- All registered state keys
- The last time each state was updated
- The current version identifier for each state

## Next steps

- Learn how to [configure state-backed components](/guides/build/components/state-backed-components/configuring-state-backed-components) in your project
- Understand how to [manage state in production](/guides/build/components/state-backed-components/managing-state-in-production) deployments
