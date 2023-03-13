# Dagster + Modern Data Stack starter kit

This starter kit shows how to build the Dagster's [Software-Defined Assets](https://docs.dagster.io/concepts/assets/software-defined-assets) alongside Modern Data Stack tools (specifically, [Airbyte](https://github.com/airbytehq/airbyte) and [dbt](https://github.com/dbt-labs/dbt-core)).

<p align="center">
<img width="500" alt="Screen Shot 2022-11-17 at 11 50 20 PM" src="https://user-images.githubusercontent.com/4531914/202649416-b727405a-f96c-4531-95ff-29b9f9bf53d2.png">
</p>

## Prerequisites

To complete the steps in this guide, you'll need:

- A Postgres database
- An [Airbyte](https://airbyte.com/) connection that's set up from Postgres to Postgres

You can follow the [Set up data and connections](#set-up-data-and-connections) section below to manually seed the source data and set up the connection.

### Using environment variables to handle secrets

Dagster allows using environment variables to handle sensitive information. You can define various configuration options and access environment variables through them. This also allows you to parameterize your pipeline without modifying code.

In this example, we ingest data from Airbyte by reading info from an [Airbyte connection](https://airbytehq.github.io/understanding-airbyte/connections/) where it syncs data from Postgres to Postgres. This example uses the default username, passwords, hosts, and ports for Airbyte and Dagster. These default configuration values can be changed pointing at environment variables, see `assets_modern_data_stack.assets.airbyte_iaac`.

You can declare environment variables in various ways:
- **Local development**: [Using `.env` files to load env vars into local environments](https://docs.dagster.io/guides/dagster/using-environment-variables-and-secrets#declaring-environment-variables)
- **Dagster Cloud**: [Using the Dagster Cloud UI](https://docs.dagster.io/master/dagster-cloud/developing-testing/environment-variables-and-secrets#using-the-dagster-cloud-ui) to manage environment variables
- **Dagster Open Source**: How environment variables are set for Dagster projects deployed on your infrastructure depends on where Dagster is deployed. Read about how to declare environment variables [here](https://docs.dagster.io/master/guides/dagster/using-environment-variables-and-secrets#declaring-environment-variables).

Check out [Using environment variables and secrets guide](https://docs.dagster.io/guides/dagster/using-environment-variables-and-secrets) for more info and examples.

## Getting started

### Option 1: Deploying it on Dagster Cloud

The easiest way to spin up your Dagster project is to use [Dagster Serverless](https://docs.dagster.io/dagster-cloud/deployment/serverless). It provides out-of-the-box CI/CD and native branching that make development and deployment easy.

Check out the [Dagster Cloud](https://dagster.io/cloud) to get started.

> Note: To use Dagster Cloud with this example you will need Airbyte and Postgres running separately.

### Option 2: Running it locally

To install this example and its Python dependencies, run:

```bash
pip install -e ".[dev]"
```

Then, start the Dagster UI web server:

```
dagster dev
```

Open http://localhost:3000 with your browser to see the project.

If you try to kick off a run immediately, it will fail, as there is no source data to ingest/transform, nor is there an active Airbyte connection. To get everything set up properly, read on.

### Setting up services locally

#### Postgres

To keep things running on a single machine, we'll use a local postgres instance as both the source and the destination for our data. You can imagine the "source" database as some online transactional database, and the "destination" as a data warehouse (something like Snowflake).

To get a postgres instance with the required source and destination databases running on your machine, you can run:

```
$ docker pull postgres
$ docker run --name mds-demo -p 5432:5432 -e POSTGRES_PASSWORD=password -d postgres
$ PGPASSWORD=password psql -h localhost -p 5432 -U postgres -d postgres -c "CREATE DATABASE postgres_replica;"
```

#### Airbyte

Now, you'll want to get Airbyte running locally. The full instructions can be found [here](https://docs.airbyte.com/deploying-airbyte/local-deployment), but if you just want to run some commands (in a separate terminal):

```
$ git clone https://github.com/airbytehq/airbyte.git
$ cd airbyte
$ docker-compose up
```

Once you've done this, you should be able to go to http://localhost:8000, and see Airbyte's UI, the default username is `airbyte` and the default password is `password`.

#### Set up data

Now, you'll want to seed some data into the empty database you just created.

There's a script provided that should handle this all for you, which you can run with:

```bash
$ python -m assets_modern_data_stack.utils.setup_postgres
```

#### Set up Airbyte connections

This example uses Dagster to [manage Airbyte ingestion as code](https://docs.dagster.io/guides/dagster/airbyte-ingestion-as-code).

To setup the Airbyte connections between the Postgres source and sink run:

```shell
dagster-airbyte apply --module assets_modern_data_stack.assets.airbyte_iaac:airbyte_reconciler
```

## Learning more

### Changing the code locally

When developing pipelines locally, be sure to click the **Reload definition** button in the Dagster UI after you change the code. This ensures that Dagster picks up the latest changes you made.

You can reload the code using the **Deployment** page:
<details><summary>👈 Expand to view the screenshot</summary>

<p align="center">
    <img height="500" src="https://raw.githubusercontent.com/dagster-io/dagster/master/docs/next/public/images/quickstarts/basic/more-reload-code.png" />
</p>

</details>

Or from the left nav or on each job page:
<details><summary>👈 Expand to view the screenshot</summary>

<p align="center">
    <img height="500" src="https://raw.githubusercontent.com/dagster-io/dagster/master/docs/next/public/images/quickstarts/basic/more-reload-left-nav.png" />
</p>

</details>

### Adding new Python dependencies

You can specify new Python dependencies in `setup.py`.

### Testing

Tests are in the `assets_modern_data_stack_tests` directory and you can run tests using `pytest`:

```bash
pytest assets_modern_data_stack_tests
```
