---
title: "Transitioning from development to production"
sidebar_position: 500
---

In this article, we'll walk through how to transition your data pipelines from local development to staging and production deployments.

Let's say we’ve been tasked with fetching the N most recent entries from Hacker News and splitting the data into two datasets: one containing all of the data about stories and one containing all of the data about comments. In order to make the pipeline maintainable and testable, we have two additional requirements:

- We must be able to run our data pipeline in local, staging, and production environments.
- We need to be confident that data won't be accidentally overwritten (for example, because a user forgot to change a configuration value).

Using a few Dagster concepts, we can easily tackle this task! Here’s an overview of the main concepts we’ll be using in this guide:

- [Assets](/guides/build/assets/) - An asset is a software object that models a data asset. The prototypical example is a table in a database or a file in cloud storage.
- [Resources](/guides/build/external-resources) - A resource is an object that models a connection to a (typically) external service. Resources can be shared between assets, and different implementations of resources can be used depending on the environment. For example, a resource may provide methods to send messages in Slack.
- [I/O managers](/guides/build/io-managers/) - An I/O manager is a special kind of resource that handles storing and loading assets. For example, if we wanted to store assets in S3, we could use Dagster’s built-in S3 I/O manager.
- [Run config](/guides/operate/configuration/run-configuration) - Assets and resources sometimes require configuration to set certain values, like the password to a database. Run config allows you to set these values at run time. In this guide, we will also use an API to set some default run configuration.

Using these Dagster concepts we will:

- Write three assets: the full Hacker News dataset, data about comments, and data about stories.
- Use Dagster's Snowflake I/O manager to store the datasets in [Snowflake](https://www.snowflake.com/).
- Set up our Dagster code so that the configuration for the Snowflake I/O manager is automatically supplied based on the environment where the code is running.

## Setup

<CodeReferenceLink filePath="examples/development_to_production" />

To follow along with this guide, you can copy the full code example and install a few additional pip libraries:

```bash
dagster project from-example --name my-dagster-project --example development_to_production
cd my-dagster-project
pip install -e .
```

## Part one: Local development

In this section we will:

- Write our assets
- Add run configuration for the Snowflake I/O manager
- Materialize assets in the Dagster UI

Let’s start by writing our three assets. We'll use Pandas DataFrames to interact with the data.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/development_to_production/assets.py" startAfter="start_assets" endBefore="end_assets" />

Now we can add these assets to our <PyObject section="definitions" module="dagster" object="Definitions" /> object and materialize them via the UI as part of our local development workflow. We can pass in credentials to our `SnowflakePandasIOManager`.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/development_to_production/repository/repository_v1.py" startAfter="start" endBefore="end" />

Note that we have passwords in our configuration in this code snippet. This is bad practice, and we will resolve it shortly.

This results in an asset graph that looks like this:

![Hacker News asset graph](/images/guides/deploy/hacker_news_asset_graph.png)

We can materialize the assets in the UI and ensure that the data appears in Snowflake as we expect:

![Snowflake data](/images/guides/deploy/snowflake_data.png)

While we define our assets as Pandas DataFrames, the Snowflake I/O manager automatically translates the data to and from Snowflake tables. The Python asset name determines the Snowflake table name. In this case three tables will be created: `ITEMS`, `COMMENTS` and `STORIES`.

## Part two: Deployment

In this section we will:

- Modify the configuration for the Snowflake I/O manager to handle staging and production environments
- Discuss different options for managing a staging environment

Now that our assets work locally, we can start the deployment process! We'll first set up our assets for production, and then discuss the options for our staging deployment.

### Production

We want to store the assets in a production Snowflake database, so we need to update the configuration for the `SnowflakePandasIOManager`. But if we were to simply update the values we set for local development, we would run into an issue: the next time a developer wants to work on these assets, they will need to remember to change the configuration back to the local values. This leaves room for a developer to accidentally overwrite the production asset during local development.

Instead, we can determine the configuration for resources based on the environment:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/development_to_production/repository/repository_v2.py" startAfter="start" endBefore="end" />

Note that we still have passwords in our configuration in this code snippet. This is bad practice, and we will resolve it next.

Now, we can set the environment variable `DAGSTER_DEPLOYMENT=production` in our deployment and the correct resources will be applied to the assets.

We still have some problems with this setup:

1. Developers need to remember to change `user` and `password` to their credentials and `schema` to their name when developing locally.
2. Passwords are being stored in code.

We can easily solve these problems using <PyObject section="resources" module="dagster" object="EnvVar"/>, which lets us source configuration for resources from environment variables. This allows us to store Snowflake configuration values as environment variables and point the I/O manager to those environment variables:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/development_to_production/repository/repository_v3.py" startAfter="start" endBefore="end" />

### Staging

Depending on your organization’s Dagster setup, there are a couple of options for a staging environment.

- **For Dagster+ users**, we recommend using [branch deployments](/dagster-plus/features/ci-cd/branch-deployments/) as your staging step. A branch deployment is a new Dagster deployment that is automatically generated for each git branch, and can be used to verify data pipelines before deploying them to production.

- **For a self-hosted staging deployment**, we’ve already done most of the necessary work to run our assets in staging! All we need to do is add another entry to the `resources` dictionary and set `DAGSTER_DEPLOYMENT=staging` in our staging deployment.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/development_to_production/repository/repository_v3.py" startAfter="start_staging" endBefore="end_staging" />

## Advanced: Unit tests with stubs and mocks

You may have noticed a missing step in the development workflow presented in this guide — unit tests! While the main purpose of the guide is to help you transition your code from local development to a production deployment, unit testing is still an important part of the development cycle. In this section, we'll explore a pattern you may find useful when writing your own unit tests.

When we write unit tests for the `items` asset, we could make more precise assertions if we knew exactly what data we'd receive from Hacker News. If we refactor our interactions with the Hacker News API as a resource, we can leverage Dagster's resource system to provide a stub resource in our unit tests.

Before we get into implementation, let's go over some best practices:

### When to use resources

In many cases, interacting with an external service directly in assets or ops is more convenient than refactoring the interactions with the service as a resource. We recommend refactoring code to use resources in the following cases:

- Multiple assets or ops need to interact with the service in a consistent way
- Different implementations of a service need to be used in certain scenarios (ie. a staging environment, or unit tests)

### When to use stub resources

Determining when it makes sense to stub a resource for a unit test can be a topic of much debate. There are certainly some resources where it would be too complicated to write and maintain a stub. For example, it would be difficult to mock a database like Snowflake with a lightweight database since the SQL syntax and runtime behavior may vary. In general, if a resource is relatively simple, writing a stub can be helpful for unit testing the assets and ops that use the resource.

We'll start by writing the "real" Hacker News API Client:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/development_to_production/resources/resources_v1.py" startAfter="start_resource" endBefore="end_resource" />

We'll also need to update the `items` asset to use this client as a resource:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/development_to_production/assets_v2.py" startAfter="start_items" endBefore="end_items" />

:::note

For the sake of brevity, we've omitted the implementation of the property `item_field_names` in `HNAPIClient`. You can find the full implementation of this resource in the [full code example](https://github.com/dagster-io/dagster/tree/master/examples/development_to_production) on GitHub.

:::

We'll also need to add an instance of `HNAPIClient` to `resources` in our `Definitions` object.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/development_to_production/repository/repository_v3.py" startAfter="start_hn_resource" endBefore="end_hn_resource" />

Now we can write a stubbed version of the Hacker News resource. We want to make sure the stub has implementations for each method `HNAPIClient` implements.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/development_to_production/resources/resources_v2.py" startAfter="start_mock" endBefore="end_mock" />

:::note

Since the stub Hacker News resource and the real Hacker News resource need to implement the same methods, this would be a great time to write an interface. We’ll skip the implementation in this guide, but you can find it in the [full code example](https://github.com/dagster-io/dagster/tree/master/examples/development_to_production).

:::

Now we can use the stub Hacker News resource to test that the `items` asset transforms the data in the way we expect:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/development_to_production/test_assets.py" startAfter="start" endBefore="end" />

:::note

While we focused on assets in this article, the same concepts and APIs can be used to swap out run configuration for jobs.

:::
