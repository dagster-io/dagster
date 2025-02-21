# Dagster + AWS starter kit

This example builds a daily ETL pipeline that stores data in S3. At a high level, this project shows how to ingest data from external sources to S3, explore and transform the data, and materialize outputs that help visualize the data.

_New to Dagster? Learn what Dagster is [in Concepts](https://docs.dagster.io/concepts) or [in the hands-on Tutorials](https://docs.dagster.io/tutorial)._

This guide covers:

- [Dagster + AWS starter kit](#dagster--aws-starter-kit)
  - [Introduction](#introduction)
  - [Prerequisites](#prerequisites)
    - [Using environment variables to handle secrets](#using-environment-variables-to-handle-secrets)
  - [Getting started](#getting-started)
    - [Option 1: Deploying it on Dagster Cloud](#option-1-deploying-it-on-dagster-cloud)
    - [Option 2: Running it locally](#option-2-running-it-locally)
  - [Step 1: Materializing assets](#step-1-materializing-assets)
  - [Step 2: Viewing and monitoring assets](#step-2-viewing-and-monitoring-assets)
  - [Step 3: Scheduling a daily job](#step-3-scheduling-a-daily-job)
  - [Learning more](#learning-more)
    - [Changing the code locally](#changing-the-code-locally)
    - [Writing a custom I/O manager](#writing-a-custom-io-manager)
    - [Adding new Python dependencies](#adding-new-python-dependencies)
    - [Testing](#testing)

## Introduction

This starter kit includes:

- Basics of creating, connecting, and testing [assets](https://docs.dagster.io/concepts/assets/software-defined-assets) in Dagster.
- Convenient ways to organize and monitor assets, e.g. [grouping assets](https://docs.dagster.io/concepts/assets/software-defined-assets#grouping-assets), [recording asset metadata](https://docs.dagster.io/concepts/metadata-tags/asset-metadata), etc.
- [S3 I/O manager](https://docs.dagster.io/deployment/guides/aws#using-s3-for-io-management) to load the datasets in S3 and read from it, which [uses environment variables](https://docs.dagster.io/guides/dagster/using-environment-variables-and-secrets) to handle the AWS credentials.
- [S3 resource](https://docs.dagster.io/_apidocs/libraries/dagster-aws#dagster_aws.s3.S3Resource) to interact with S3 instance inside an asset, which also requires setting up credentials.
- A [schedule](https://docs.dagster.io/concepts/partitions-schedules-sensors/schedules) defined to run a job that generates assets daily.
- [Scaffolded project layout](https://docs.dagster.io/getting-started/create-new-project) that helps you to quickly get started with everything set up.

In this project, we're building an analytical pipeline that explores popular topics on HackerNews.

<p align="center">
    <img height="500" src="https://raw.githubusercontent.com/dagster-io/dagster/master/examples/images/quickstarts/basic/homepage.png" />
</p>

This project:

- Fetches data from [HackerNews](https://github.com/HackerNews/API) APIs and stores the data in S3.
- Transforms the collected data using [Pandas](http://pandas.pydata.org/pandas-docs/stable/).
- Creates a [word cloud](https://github.com/amueller/word_cloud) based on trending HackerNews stories to visualize popular topics on HackerNews.

## Prerequisites

To complete the steps in this guide, you'll need:

- A [AWS](https://aws.amazon.com) account.
- Set up secrets to connect to AWS.

### Using environment variables to handle secrets

To connect to AWS, you'll need to set up your credentials in Dagster.

Dagster allows using environment variables to handle sensitive information. You can define various configuration options and access environment variables through them. This also allows you to parameterize your pipeline without modifying code.

In this example, we use [`S3PickleIOManager`](https://docs.dagster.io/_apidocs/libraries/dagster-aws#dagster_aws.s3.S3PickleIOManager) to write outputs to S3 and read inputs from it and [`S3Resource`](https://docs.dagster.io/_apidocs/libraries/dagster-aws#dagster_aws.s3.S3Resource) to interact with S3 instance inside an asset.

The configurations of the S3 connection are defined in [`quickstart_aws/repository.py`](./quickstart_aws/repository.py), which requires the following environment variables:

- `AWS_ACCESS_KEY_ID`
  - _Note: `S3Resource` uses boto under the hood, so if you are accessing your private buckets, you will need to provide the `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` environment variables or follow one of the other boto authentication methods. Check out the [AWS documentation for accessing AWS using your AWS credentials](https://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html)._
- `AWS_SECRET_ACCESS_KEY`
- `S3_BUCKET`

You can declare environment variables in various ways:

- **Local development**: [Using `.env` files to load env vars into local environments](https://docs.dagster.io/guides/dagster/using-environment-variables-and-secrets#declaring-environment-variables)
- **Dagster Cloud**: [Using the Dagster Cloud UI](https://docs.dagster.io/master/dagster-cloud/developing-testing/environment-variables-and-secrets#using-the-dagster-cloud-ui) to manage environment variables
- **Dagster Open Source**: How environment variables are set for Dagster projects deployed on your infrastructure depends on where Dagster is deployed. Read about how to declare environment variables [here](https://docs.dagster.io/master/guides/dagster/using-environment-variables-and-secrets#declaring-environment-variables).

Check out [Using environment variables and secrets guide](https://docs.dagster.io/guides/dagster/using-environment-variables-and-secrets) for more info and examples.

## Getting started

### Option 1: Deploying it on Dagster Cloud

The easiest way to spin up your Dagster project is to use [Dagster Cloud Serverless](https://docs.dagster.io/dagster-cloud/deployment/serverless). It provides out-of-the-box CI/CD and native branching that make development and deployment easy.

Check out [Dagster Cloud](https://dagster.io/cloud) to get started.

### Option 2: Running it locally

First, install your Dagster repository as a Python package. By using the `--editable` flag, pip will install your repository in ["editable mode"](https://pip.pypa.io/en/latest/topics/local-project-installs/#editable-installs) so that as you develop, local code changes will automatically apply. Check out [Dagster Installation](https://docs.dagster.io/getting-started/install) for more information.

```bash
pip install -e ".[dev]"
```

Then, start the Dagster UI web server:

```bash
dagster dev
```

Open http://localhost:3000 with your browser to see the project.

## Step 1: Materializing assets

With the starter project loaded in your browser, click the icon in the top-left corner of the page to expand the navigation. You'll see both jobs and assets listed in the left nav.

<p align="center">
    <img height="500" src="https://raw.githubusercontent.com/dagster-io/dagster/master/examples/images/quickstarts/basic/step-1-1-left-nav.png" />
</p>

Click on the `hackernews` asset group to view the HackerNews assets and their relationship.

An asset is a software object that models a data asset, which can be a file in your filesystem, a table in a database, or a data report. The assets in the `hackernews` asset group ingest the current trending 500 HackerNews stories and plots a word cloud out of the collected stories to visualize the popular topics on HackerNews. You'll see three assets with different tags:

- `hackernews_topstory_ids` fetches a list of top story ids from a HackerNews endpoint.
- `hackernews_topstories` takes the list of ids and pulls the story details from HackerNews based on the ids.
- `hackernews_stories_word_cloud` visualizes the trending topics in a word cloud.

Dagster visualizes upstream and downstream dependencies vertically. Assets below other assets connected by arrows implies a dependency relationship. So we can tell from the UI that the asset `hackernews_topstories` depends on `hackernews_topstory_ids` (i.e. `hackernews_topstories` takes `hackernews_topstory_ids`'s output as an input) and `hackernews_stories_word_cloud` depends on `hackernews_topstories`.

All three assets are defined [in `quickstart_aws/assets/hackernews.py`](./quickstart_aws/assets/hackernews.py). Typically, you'll define assets by annotating ordinary Python functions with the [`@asset`](https://docs.dagster.io/concepts/assets/software-defined-assets#a-basic-software-defined-asset) decorator.

This project also comes with ways to better organize the assets:

- **Labeling/tagging.** You'll find the assets are tagged with different [labels/badges], such as `HackerNews API` and `Plot`. This is defined in code via the `compute_kind` argument to the `@asset` decorator. It can be any string value that represents the kind of computation that produces the asset and will be displayed in the UI as a badge on the asset. This can help us quickly understand the data logic from a bird's eye view.
- **Grouping assets**. We've also assigned all three assets to the group `hackernews`, which is accomplished by providing the `group_name` argument to the `@asset` decorator. Grouping assets can help keep assets organized as your project grows. Learn about asset grouping [here](https://docs.dagster.io/concepts/assets/software-defined-assets#assigning-assets-to-groups).
- **Adding descriptions.** In the asset graph, the UI also shows the description of each asset. You can specify the description of an asset in the `description` argument to `@asset`. When the argument is not provided and the decorated function has a docstring, Dagster will use the docstring as the description. In this example, the UI is using the docstrings as the descriptions.

Now that we've got a basic understanding of Dagster assets, let's materialize them.

<p align="center">
    <img height="500" src="https://raw.githubusercontent.com/dagster-io/dagster/master/examples/images/quickstarts/basic/step-1-2-materialize-all.png" />
</p>

Click **Materialize all** to kick off a Dagster run which will pull info from the external APIs and move the data through assets.

As you iterate, some assets may become outdated. To refresh them, you can select a subset of assets to run instead of re-running the entire pipeline. This allows us to avoid unnecessary re-runs of expensive computations, only re-materializing the assets that need to be updated. If assets take a long time to run or interact with APIs with restrictive rate limits, selectively re-materializing assets will come in handy.

<p align="center">
    <img height="500" src="https://raw.githubusercontent.com/dagster-io/dagster/master/examples/images/quickstarts/basic/step-1-3-view-run.png" />
</p>

You'll see an indicator pop up with the launched run ID. Click **View** to monitor the run in real-time. This will open a new tab in your browser:

<p align="center">
    <img height="500" src="https://raw.githubusercontent.com/dagster-io/dagster/master/examples/images/quickstarts/basic/step-1-4-compute-logs.png" />
</p>

The process will run for a bit. While it's running, you should see the real-time compute logs printed in the UI. _(It may take 1-2 minutes to fetch all top 500 stories from HackerNews in the `hackernews_topstories` step)._

## Step 2: Viewing and monitoring assets

When you materialize an asset, the object returned by your asset function is saved. Dagster makes it easy to save these results to disk, to blob storage, to a database, or to any other system. In this example the assets are saved to the file system. In addition to the asset materialization, your asset functions can also generate metadata that is directly visible in Dagster. To view the materialization details and metadata, click on the "ASSET_MATERIALIZATION" event. In this example, the `hackernews_stories_word_cloud` asset materializes a plot that is saved to disk, but we also add the plot as metadata to make it visible in Dagster.

<p align="center">
    <img height="500" src="https://raw.githubusercontent.com/dagster-io/dagster/master/examples/images/quickstarts/basic/step-2-5-asset-in-logs.png" />
</p>

Click **Show Markdown**. You'll see a word cloud of the top 500 HackerNews story titles generated by the `hackernews_topstories_word_cloud` asset:

<p align="center">
    <img height="500" src="https://raw.githubusercontent.com/dagster-io/dagster/master/examples/images/quickstarts/basic/step-2-6-hackernews_word_cloud.png" />
</p>

The metadata is recorded in the `hackernews_topstories_word_cloud` asset [in `quickstart_aws/assets/hackernews.py`](./quickstart_aws/assets/hackernews.py). Dagster supports attaching arbitrary [metadata](https://docs.dagster.io/_apidocs/ops#dagster.MetadataValue) to asset materializations. This metadata is also be displayed on the **Activity** tab of the **Asset Details** page in the UI or in the **Asset Lineage** view after selecting an asset. From the compute logs of a run, you can click the **View Asset** to go to the **Asset Details** page.

<p align="center">
    <img height="500" src="https://raw.githubusercontent.com/dagster-io/dagster/master/examples/images/quickstarts/basic/step-2-7-view-assets.png" />
</p>

This metadata would be useful for monitoring and maintaining the asset as you iterate. Similarly, we've also recorded some metadata in the `hackernews_topstories` asset. You can filter the compute logs by typing the asset name (e.g. `hackernews_topstories`) or the event type (e.g. `type:ASSET_MATERIALIZATION`) in the **Log Filter** input box:

<p align="center">
    <img height="500" src="https://raw.githubusercontent.com/dagster-io/dagster/master/examples/images/quickstarts/basic/step-2-8-filter.png" />
</p>

In the results, you'll see that the `hackernews_topstories` asset has two metadata entries: `num_records` and `preview`. Both are defined [in `quickstart_aws/assets/hackernews.py`](./quickstart_aws/assets/hackernews.py), in which we record the first five rows of the output Pandas DataFrame in the `preview` metadata entry using the Markdown type. This could help debug and keep your assets easily monitored. Click **Show Markdown** to view a preview of the output data frame:

<p align="center">
    <img height="500" src="https://raw.githubusercontent.com/dagster-io/dagster/master/examples/images/quickstarts/basic/step-2-9-preview.png" />
</p>

Note: You'll find a `path` metadata attached to every asset. This is because assets are, by default, materialized to pickle files on your local filesystem. In most projects, your assets will be materialized to a production system and you can fully customize the I/O using [I/O managers](https://docs.dagster.io/concepts/io-management/io-managers).

## Step 3: Scheduling a daily job

Finally, let's refresh our plots every day so we can monitor popular topics over time. To do so, we can use [schedules](https://docs.dagster.io/concepts/partitions-schedules-sensors/schedules#schedules).

We've defined a daily schedule and job in [`quickstart_aws/definitions.py`](./quickstart_aws/definitions.py) for all assets that are defined in the [`quickstart_aws/assets/`](./quickstart_aws/assets) module.

Now, let's turn on the daily schedule within Dagster.

1. In the left nav, it indicates the `all_assets_job` has a schedule associated with it but it's currently off. Clicking "all_assets_job" in the left nav will bring you to the job definition page.
2. Mouse over the schedule indicator on the top of the page to navigate to the individual schedule page for more info about the schedule.

<p align="center">
    <img height="500" src="https://raw.githubusercontent.com/dagster-io/dagster/master/examples/images/quickstarts/basic/step-3-1-schedule-off.png" />
</p>

You can now turn on the schedule switch to set up the daily job we defined in [quickstart_aws/repository.py](./quickstart_aws/repository.py).

<p align="center">
    <img height="500" src="https://raw.githubusercontent.com/dagster-io/dagster/master/examples/images/quickstarts/basic/step-3-2-schedule-on.png" />
</p>

<br />
<br />

Congratulations 🎉 You now have a daily job running in production!

---

## Learning more

### Changing the code locally

When developing pipelines locally, be sure to click the **Reload definition** button in the Dagster UI after you change the code. This ensures that Dagster picks up the latest changes you made.

You can reload the code using the **Deployment** page:

<details><summary>👈 Expand to view the screenshot</summary>

<p align="center">
    <img height="500" src="https://raw.githubusercontent.com/dagster-io/dagster/master/examples/images/quickstarts/basic/more-reload-code.png" />
</p>

</details>

Or from the left nav or on each job page:

<details><summary>👈 Expand to view the screenshot</summary>

<p align="center">
    <img height="500" src="https://raw.githubusercontent.com/dagster-io/dagster/master/examples/images/quickstarts/basic/more-reload-left-nav.png" />
</p>

</details>

### Writing a custom I/O manager

Dagster provides out-of-the-box [built-in IO managers](https://docs.dagster.io/concepts/io-management/io-managers#built-in-io-managers) for popular storage systems. This example uses the built-in [`s3_pickle_io_manager`](https://docs.dagster.io/_apidocs/libraries/dagster-aws#dagster_aws.s3.s3_pickle_io_manager) which pickles the outputs and uploads them to S3. In production, pickling is often not sufficient. You can write your own I/O managers to handle custom serialization and deserialization or for other storage systems. Here's an example for [a custom IO manager that stores Pandas DataFrames in tables](https://docs.dagster.io/concepts/io-management/io-managers#a-custom-io-manager-that-stores-pandas-dataframes-in-tables).

Check out the [I/O Manager concept page](https://docs.dagster.io/concepts/io-management/io-managers#a-custom-io-manager-that-stores-pandas-dataframes-in-tables) for more info and examples.

### Adding new Python dependencies

You can specify new Python dependencies in `setup.py`.

### Testing

Tests are in the `quickstart_aws_tests` directory and you can run tests using `pytest`:

```bash
pytest quickstart_aws_tests
```
