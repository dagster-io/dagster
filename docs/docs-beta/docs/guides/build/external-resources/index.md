---
title: External resources
sidebar_position: 20
---

Dagster resources are objects that provide access to external systems, databases, or services. Resources are used to manage connections to external systems, and are used by Dagster assets and ops. For example, a simple ETL (Extract Transform Load) pipeline fetches data from an API, ingests it into a database, and updates a dashboard. External tools and services this pipeline uses could be:

- The API the data is fetched from
- The AWS S3 bucket where the API's response is stored
- The Snowflake/Databricks/BigQuery account the data is ingested into
- The BI tool the dashboard was made in

Using Dagster resources, you can standardize connections and integrations to these tools across Dagster definitions like [asset definitions](/guides/build/assets), [schedules](/guides/automate/schedules), [sensors](/guides/automate/sensors), and [jobs](/guides/build/assets/asset-jobs).

Resources allow you to:

- **Plug in different implementations in different environments** - If you have a heavy external dependency that you want to use in production but avoid using in testing, you can accomplish this by providing different resources in each environment. Refer to the [Separating business logic from environments](/todo) section of the Testing documentation for more info about this capability.
- **Surface configuration in the Dagster UI** - Resources and their configuration are surfaced in the UI, making it easy to see where resources are used and how they're configured.
- **Share configuration across multiple assets or ops** - Resources are configurable and shared, so configuration can be supplied in one place instead of individually.
- **Share implementations across multiple assets or ops** - When multiple assets access the same external services, resources provide a standard way to structure your code to share the implementations.

## Relevant APIs

{/* TODO replace `ResourceParam` with <PyObject section="resources" module="dagster" object="ResourceParam"/> in table below  */}

| Name                                             | Description                                                                                                                                                                                                                             |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| <PyObject section="resources" module="dagster" object="ConfigurableResource"/>        | The base class extended to define resources. Under the hood, implements <PyObject section="resources" object="ResourceDefinition" />.                                                                                                                       |
| `ResourceParam`               | An annotation used to specify that a plain Python object parameter for an asset or op is a resource.                                                                                                                                    |
| <PyObject section="resources" module="dagster" object="ResourceDefinition" />         | Class for resource definitions. You almost never want to use initialize this class directly. Instead, you should extend the <PyObject section="resources" object="ConfigurableResource" /> class which implements <PyObject section="resources" object="ResourceDefinition" />. |
| <PyObject section="resources" module="dagster" object="InitResourceContext"/>         | The context object provided to a resource during initialization. This object contains required resources, config, and other run information.                                                                                            |
| <PyObject section="resources" module="dagster" object="build_init_resource_context"/> | Function for building an <PyObject section="resources" object="InitResourceContext"/> outside of execution, intended to be used when testing a resource.                                                                                                    |
| <PyObject section="resources" module="dagster" object="build_resources"/>             | Function for initializing a set of resources outside of the context of a job's execution.                                                                                                                                               |
| <PyObject section="resources" module="dagster" object="with_resources"/>              | Advanced API for providing resources to a specific set of asset definitions, overriding those provided to <PyObject section="definitions" object="Definitions"/>.
