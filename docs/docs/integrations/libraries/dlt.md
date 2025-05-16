---
title: Dagster & dlt
sidebar_label: dlt
description: The dltHub open-source library defines a standardized approach for creating data pipelines that load often messy data sources into well-structured data sets.
tags: [dagster-supported, etl]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-dlt
pypi: https://pypi.org/project/dagster-dlt/
sidebar_custom_props:
  logo: images/integrations/dlthub.jpeg
partnerlink: https://dlthub.com/
---

<p>{frontMatter.description}</p>

It offers many advanced features, such as:

- Handling connection secrets
- Converting data into the structure required for a destination
- Incremental updates and merges

dlt also provides a large collection of [pre-built, verified sources](https://dlthub.com/docs/dlt-ecosystem/verified-sources/) and [destinations](https://dlthub.com/docs/dlt-ecosystem/destinations/), allowing you to write less code (if any!) by leveraging the work of the dlt community.

In this guide, we'll explain how the dlt integration works, how to set up a Dagster project for dlt, and how to use a pre-defined dlt source.

## How it works

The Dagster dlt integration uses [multi-assets](/guides/build/assets/defining-assets#multi-asset), a single definition that results in multiple assets. These assets are derived from the `DltSource`.

The following is an example of a dlt source definition where a source is made up of two resources:

```python
@dlt.source
def example(api_key: str = dlt.secrets.value):
    @dlt.resource(primary_key="id", write_disposition="merge")
    def courses():
        response = requests.get(url=BASE_URL + "courses")
        response.raise_for_status()
        yield response.json().get("items")

    @dlt.resource(primary_key="id", write_disposition="merge")
    def users():
        for page in _paginate(BASE_URL + "users"):
            yield page

    return courses, users
```

Each resource queries an API endpoint and yields the data that we wish to load into our data warehouse. The two resources defined on the source will map to Dagster assets.

Next, we defined a dlt pipeline that specifies how we want the data to be loaded:

```python
pipeline = dlt.pipeline(
    pipeline_name="example_pipeline",
    destination="snowflake",
    dataset_name="example_data",
    progress="log",
)
```

A dlt source and pipeline are the two components required to load data using dlt. These will be the parameters of our multi-asset, which will integrate dlt and Dagster.

## Prerequisites

To follow the steps in this guide, you'll need:

- **To read the [dlt introduction](https://dlthub.com/docs/intro)**, if you've never worked with dlt before.
- **[To install](/getting-started/installation) the following libraries**:

  <PackageInstallInstructions packageName="dagster-dlt" />

  Installing `dagster-dlt` will also install the `dlt` package.

## Step 1: Configure your Dagster project to support dlt

The first step is to define a location for the `dlt` code used for ingesting data. We recommend creating a `dlt_sources` directory at the root of your Dagster project, but this code can reside anywhere within your Python project.

Run the following to create the `dlt_sources` directory:

```bash
cd $DAGSTER_HOME && mkdir dlt_sources
```

## Step 2: Initialize dlt ingestion code

In the `dlt_sources` directory, you can write ingestion code following the [dlt tutorial](https://dlthub.com/docs/tutorial/load-data-from-an-api) or you can use a verified source.

In this example, we'll use the [GitHub source](https://dlthub.com/docs/dlt-ecosystem/verified-sources/github) provided by dlt.

1. Run the following to create a location for the dlt source code and initialize the GitHub source:

   ```bash
   cd dlt_sources

   dlt init github snowflake
   ```

   At which point you'll see the following in the command line:

   ```bash
   Looking up the init scripts in https://github.com/dlt-hub/verified-sources.git...
   Cloning and configuring a verified source github (Source that load github issues, pull requests and reactions for a specific repository via customizable graphql query. Loads events incrementally.)
   ```

2. When prompted to proceed, enter `y`. You should see the following confirming that the GitHub source was added to the project:

   ```bash
   Verified source github was added to your project!
   * See the usage examples and code snippets to copy from github_pipeline.py
   * Add credentials for snowflake and other secrets in ./.dlt/secrets.toml
   * requirements.txt was created. Install it with:
   pip3 install -r requirements.txt
   * Read https://dlthub.com/docs/walkthroughs/create-a-pipeline for more information
   ```

This downloaded the code required to collect data from the GitHub API. It also created a `requirements.txt` and a `.dlt/` configuration directory. These files can be removed, as we will configure our pipelines through Dagster, however, you may still find it informative to reference.

```bash
$ tree -a
.
├── .dlt               # can be removed
│   ├── .sources
│   ├── config.toml
│   └── secrets.toml
├── .gitignore
├── github
│   ├── README.md
│   ├── __init__.py
│   ├── helpers.py
│   ├── queries.py
│   └── settings.py
├── github_pipeline.py
└── requirements.txt   # can be removed
```

## Step 3: Define dlt environment variables

This integration manages connections and secrets using environment variables as `dlt`. The `dlt` library can infer required environment variables used by its sources and resources. Refer to [dlt's Secrets and Configs](https://dlthub.com/docs/general-usage/credentials/configuration) documentation for more information.

In the example we've been using:

- The `github_reactions` source requires a GitHub access token
- The Snowflake destination requires database connection details

This results in the following required environment variables:

```bash
SOURCES__GITHUB__ACCESS_TOKEN=""
DESTINATION__SNOWFLAKE__CREDENTIALS__DATABASE=""
DESTINATION__SNOWFLAKE__CREDENTIALS__PASSWORD=""
DESTINATION__SNOWFLAKE__CREDENTIALS__USERNAME=""
DESTINATION__SNOWFLAKE__CREDENTIALS__HOST=""
DESTINATION__SNOWFLAKE__CREDENTIALS__WAREHOUSE=""
DESTINATION__SNOWFLAKE__CREDENTIALS__ROLE=""
```

Ensure that these variables are defined in your environment, either in your `.env` file when running locally or in the [Dagster deployment's environment variables](/guides/deploy/using-environment-variables-and-secrets).

## Step 4: Define a DagsterDltResource

Next, we'll define a <PyObject section="libraries" module="dagster_dlt" object="DagsterDltResource" />, which provides a wrapper of a dlt pipeline runner. Use the following to define the resource, which can be shared across all dlt pipelines:

```python
from dagster_dlt import DagsterDltResource

dlt_resource = DagsterDltResource()
```

We'll add the resource to our <PyObject section="definitions" module="dagster" object="Definitions" /> in a later step.

## Step 5: Create a dlt_assets definition for GitHub

The <PyObject section="libraries" object="dlt_assets" module="dagster_dlt" decorator /> decorator takes a `dlt_source` and `dlt_pipeline` parameter. In this example, we used the `github_reactions` source and created a `dlt_pipeline` to ingest data from Github to Snowflake.

In the same file containing your Dagster assets, you can create an instance of your <PyObject section="libraries" object="dlt_assets" module="dagster_dlt" decorator /> by doing something like the following:

:::

If you are using the [sql_database](https://dlthub.com/docs/api_reference/sources/sql_database/__init__#sql_database) source, consider setting `defer_table_reflect=True` to reduce database reads. By default, the Dagster daemon will refresh definitions roughly every minute, which will query the database for resource definitions.

:::

```python
from dagster import AssetExecutionContext, Definitions
from dagster_dlt import DagsterDltResource, dlt_assets
from dlt import pipeline
from dlt_sources.github import github_reactions


@dlt_assets(
    dlt_source=github_reactions(
        "dagster-io", "dagster", max_items=250
    ),
    dlt_pipeline=pipeline(
        pipeline_name="github_issues",
        dataset_name="github",
        destination="snowflake",
        progress="log",
    ),
    name="github",
    group_name="github",
)
def dagster_github_assets(context: AssetExecutionContext, dlt: DagsterDltResource):
    yield from dlt.run(context=context)
```

## Step 6: Create the Definitions object

The last step is to include the assets and resource in a <PyObject section="definitions" module="dagster" object="Definitions" /> object. This enables Dagster tools to load everything we've defined:

```python
defs = Definitions(
    assets=[
        dagster_github_assets,
    ],
    resources={
        "dlt": dlt_resource,
    },
)
```

And that's it! You should now have two assets that load data to corresponding Snowflake tables: one for issues and the other for pull requests.

## Advanced usage

### Overriding the translator to customize dlt assets

The <PyObject section="libraries" module="dagster_dlt" object="DagsterDltTranslator" /> object can be used to customize how dlt properties map to Dagster concepts.

For example, to change how the name of the asset is derived, or if you would like to change the key of the upstream source asset, you can override the <PyObject section="libraries" module="dagster_dlt" object="DagsterDltTranslator" method="get_asset_spec" /> method.

<CodeExample path="docs_snippets/docs_snippets/integrations/dlt/dlt_dagster_translator.py" />

In this example, we customized the translator to change how the dlt assets' names are defined.

### Assigning metadata to upstream external assets

A common question is how to define metadata on the external assets upstream of the dlt assets.

This can be accomplished by defining a <PyObject section="assets" module="dagster" object="AssetSpec" /> with a key that matches the one defined in the <PyObject section="libraries" module="dagster_dlt" object="DagsterDltTranslator" method="get_asset_spec" /> method.

For example, let's say we have defined a set of dlt assets named `thinkific_assets`, we can iterate over those assets and derive a <PyObject section="assets" module="dagster" object="AssetSpec" /> with attributes like `group_name`.

<CodeExample path="docs_snippets/docs_snippets/integrations/dlt/dlt_source_assets.py" />

### Customize upstream dependencies

By default, Dagster sets upstream dependencies when generating asset specs for your dlt assets. To do so, Dagster parses information about assets that are upstream of specific dlt assets from the dlt resource itself. You can customize how upstream dependencies are set on your dlt assets by passing an instance of the custom <PyObject section="libraries" module="dagster_dlt" object="DagsterDltTranslator" /> to the <PyObject section="libraries" module="dagster_dlt" object="build_dlt_asset_specs" /> function.

<CodeExample
  startAfter="start_upstream_asset"
  endBefore="end_upstream_asset"
  path="docs_snippets/docs_snippets/integrations/dlt/customize_upstream_dependencies.py"
/>

Note that `super()` is called in each of the overridden methods to generate the default asset spec. It is best practice to generate the default asset spec before customizing it.

You can also pass an instance of the custom <PyObject section="libraries" module="dagster_dlt" object="DagsterDltTranslator" /> to the <PyObject section="libraries" module="dagster_dlt" object="dlt_assets" /> decorator.

### Define downstream dependencies

Dagster allows you to define assets that are downstream of specific dlt resources using their asset keys. The asset key for a dlt resource can be retrieved using the <PyObject section="libraries" module="dagster_dlt" object="DagsterDltTranslator" />. The below example defines `example_downstream_asset` as a downstream dependency of `example_dlt_resource`:

<CodeExample
  startAfter="start_downstream_asset"
  endBefore="end_downstream_asset"
  path="docs_snippets/docs_snippets/integrations/dlt/define_downstream_dependencies.py"
/>

In the downstream asset, you may want direct access to the contents of the dlt resource. To do so, you can customize the code within your `@asset`-decorated function to load upstream data.

### Using partitions in your dlt assets

It is possible to use partitions within your dlt assets. However, it should be noted that this may result in concurrency related issues as state is managed by dlt. For this reason, it is recommended to set concurrency limits for your partitioned dlt assets. See the [Limiting concurrency in data pipelines](/guides/operate/managing-concurrency) guide for more details.

That said, here is an example of using static named partitions from a dlt source.

<CodeExample path="docs_snippets/docs_snippets/integrations/dlt/dlt_partitions.py" />

## What's next?

Want to see real-world examples of dlt in production? Check out how we use it internally at Dagster in the [Dagster Open Platform](https://github.com/dagster-io/dagster-open-platform) project.

### About dlt

[Data Load Tool (dlt)](https://dlthub.com/) is an open source library for creating efficient data pipelines. It offers features like secret management, data structure conversion, incremental updates, and pre-built sources and destinations, simplifying the process of loading messy data into well-structured datasets.
