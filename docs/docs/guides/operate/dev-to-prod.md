---
description: Transition Dagster data pipelines from local development to staging and production deployments.
sidebar_position: 60
title: Transitioning from development to production
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

To follow along with this guide, you will first need to scaffold a Dagster project with the [`create-dagster` CLI](/api/dg/create-dagster):

```bash
uvx create-dagster project my-dagster-project
```

Next, activate the project virtual environment:

```bash
cd my-dagster-project && source .venv/bin/activate
```

Finally, install the required libraries:

```bash
uv add dagster_snowflake_pandas pandas requests
```

## Part one: Local development

In this section we will:

- Scaffold our assets
- Add run configuration for the Snowflake I/O manager
- Materialize assets in the Dagster UI

### 1. Scaffold assets

Let’s start by scaffolding our three assets the [dg scaffold](/api/dg/dg-cli#dg-scaffold) command:

```bash
dg scaffold defs dagster.asset assets.py
```

Replace the boilerplate code in `assets.py` with the code below. We'll use Pandas DataFrames to interact with the data:

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dev_to_prod/assets/assets.py"
  startAfter="start_assets"
  endBefore="end_assets"
  title="src/my_dagster_project/defs/assets.py"
/>

### 2. Create a resource to hold credentials

Now we can create a `resources.py` file to hold credentials for our `SnowflakePandasIOManager`.

First, scaffold the resource:

```bash
dg scaffold defs dagster.resources resources.py
```

Next, copy the following code into `resources.py`:

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dev_to_prod/resources/resources.py"
  title="src/my_dagster_project/defs/resources.py"
/>

:::warning

Note that there are passwords in this code snippet. This is bad practice, and we will resolve it shortly.

:::

### 3. Start the webserver and materialize the assets

Start the webserver:

```bash
dg dev
```

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

#### 1. Configure resources based on environment

We want to store the assets in a production Snowflake database, so we need to update the configuration for the `SnowflakePandasIOManager`. But if we were to simply update the values we set for local development, we would run into an issue: the next time a developer wants to work on these assets, they will need to remember to change the configuration back to the local values. This means a developer could accidentally overwrite the production asset during local development.

Instead, we can determine the configuration for resources based on the environment:

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dev_to_prod/resources/resources_v2.py"
  title="src/my-dagster-project/defs/resources.py"
/>

:::warning

Note that we still have passwords in our configuration in this code snippet. This is bad practice, and we will resolve it in the next step.

:::

Now we can set the environment variable `DAGSTER_DEPLOYMENT=production` in our deployment, and the correct resources will be applied to the assets.

#### 2. Get config values from environment variables

We still have some problems with this setup:

* Developers need to remember to change `user` and `password` to their credentials and `schema` to their name when developing locally.
* Passwords are being stored in code.

We can easily solve these problems using <PyObject section="resources" module="dagster" object="EnvVar"/>, which lets us source configuration for resources from environment variables. This allows us to store Snowflake configuration values as environment variables and point the I/O manager to those environment variables:

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dev_to_prod/resources/resources_v3.py"
/>

### Staging

Depending on your organization’s Dagster setup, there are a couple of options for a staging environment.

- **For Dagster+ users**, we recommend using [branch deployments](/deployment/dagster-plus/ci-cd/branch-deployments/) as your staging step. A branch deployment is a new Dagster deployment that is automatically generated for each git branch, and can be used to verify data pipelines before deploying them to production.

- **For a self-hosted staging deployment**, we’ve already done most of the necessary work to run our assets in staging! All we need to do is add another entry to the `resources` dictionary and set `DAGSTER_DEPLOYMENT=staging` in our staging deployment.

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dev_to_prod/resources/resources_v4.py"
  startAfter="start_staging"
  endBefore="end_staging"
/>

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

#### 1. Write Hacker News API client

We'll start by writing the "real" Hacker News API Client. We'll also need to add an instance of `HNAPIClient` to `resources`:

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dev_to_prod/resources/resources_v5.py"
  title="src/my_dagster_project/defs/resources.py"
/>

#### 2. Update assets.py

Next, we'll need to update the `items` asset in `assets.py` to use the Hacker News API client as a resource:

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dev_to_prod/assets/assets_v2.py"
  title="src/my_dagster_project/defs/assets.py"
/>

:::note

For the sake of brevity, we've omitted the implementation of the property `item_field_names` in `HNAPIClient`. You can find the full implementation of this resource in the [full code example](https://github.com/dagster-io/dagster/tree/master/examples/development_to_production) on GitHub.

:::

#### 3. Write stubbed version of the Hacker News resource

Now we can write a stubbed version of the Hacker News resource. We want to make sure the stub has implementations for each method `HNAPIClient` implements.

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dev_to_prod/resources/resources_v6.py"
  title="src/my_dagster_project/defs/resources.py"
/>

:::note

Since the stub Hacker News resource and the real Hacker News resource need to implement the same methods, this would be a great time to write an interface. We’ll skip the implementation in this guide, but you can find it in the [full code example](https://github.com/dagster-io/dagster/tree/master/examples/development_to_production).

:::

#### 4. Test the `items` asset transformation

Now we can use the stub Hacker News resource to test that the `items` asset transforms the data in the way we expect:

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/dev_to_prod/test_assets.py"
  title="src/my_dagster_project/defs/test_assets.py"
/>

:::note

While we focused on assets in this article, the same concepts and APIs can be used to swap out run configuration for jobs.

:::
