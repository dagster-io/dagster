# Dagster starter kit

This example is a starter kit for building a daily ETL pipeline. At a high level, this project shows how to ingest data from external sources, explore and transform the data, and materialize outputs that help visualize the data.

_New to Dagster? Learn what Dagster is [in Concepts](https://docs.dagster.io/concepts) or [in the hands-on Tutorials](https://docs.dagster.io/tutorial)._

This guide covers:

- [Dagster starter kit](#dagster-starter-kit)
  - [Introduction](#introduction)
  - [Getting started](#getting-started)
    - [Option 1: Deploying it on Dagster Cloud](#option-1-deploying-it-on-dagster-cloud)
    - [Option 2: Running it locally](#option-2-running-it-locally)
  - [Step 1: Materializing assets](#step-1-materializing-assets)
  - [Step 2: Viewing and monitoring assets](#step-2-viewing-and-monitoring-assets)
  - [Step 3: Scheduling a daily job](#step-3-scheduling-a-daily-job)
  - [Learning more](#learning-more)
    - [Changing the code locally](#changing-the-code-locally)
    - [Using environment variables and secrets](#using-environment-variables-and-secrets)
    - [Adding new Python dependencies](#adding-new-python-dependencies)
    - [Testing](#testing)

## Introduction

This starter kit includes:

- Basics of creating, connecting, and testing [assets](https://docs.dagster.io/concepts/assets/software-defined-assets) in Dagster.
- Convenient ways to organize and monitor assets, e.g. [grouping assets](https://docs.dagster.io/concepts/assets/software-defined-assets#grouping-assets), [recording asset metadata](https://docs.dagster.io/concepts/assets/software-defined-assets#recording-materialization-metadata), etc.
- A [schedule](https://docs.dagster.io/concepts/partitions-schedules-sensors/schedules) defined to run a job that generates assets daily.
- [Scaffolded project layout](https://docs.dagster.io/getting-started/create-new-project) that helps you to quickly get started with everything set up.

In this project, we're building an analytical pipeline that explores popular topics on HackerNews.

<p align="center">
    <img height="500" src="../../docs/next/public/images/quickstarts/basic/homepage.png" />
</p>

This project:

- Fetches data from [HackerNews](https://github.com/HackerNews/API) APIs.
- Transforms the collected data using [Pandas](http://pandas.pydata.org/pandas-docs/stable/).
- Creates a [word cloud](https://github.com/amueller/word_cloud) based on trending HackerNews stories to visualize popular topics on HackerNews.

## Getting started

### Option 1: Deploying it on Dagster Cloud

The easiest way to spin up your Dagster project is to use [Dagster Cloud Serverless](https://docs.dagster.io/dagster-cloud/deployment/serverless). It provides out-of-the-box CI/CD and native branching that make development and deployment easy.

Check out [Dagster Cloud](https://dagster.io/cloud) to get started.

### Option 2: Running it locally

Bootstrap your own Dagster project with this example:

```bash
dagster project from-example --name my-dagster-project --example quickstart_etl
```

First, install your Dagster code as a Python package. By using the `--editable` flag, pip will install in ["editable mode"](https://pip.pypa.io/en/latest/topics/local-project-installs/#editable-installs) so that as you develop, local code changes will automatically apply. Check out [Dagster Installation](https://docs.dagster.io/getting-started/install) for more information.

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
    <img height="500" src="../../docs/next/public/images/quickstarts/basic/step-1-1-left-nav.png" />
</p>

Click on the `hackernews` asset group to view the HackerNews assets and their relationship.

An asset is a software object that models a data asset, which can be a file in your filesystem, a table in a database, or a data report. The assets in the `hackernews` asset group ingest the current trending 500 HackerNews stories and plots a word cloud out of the collected stories to visualize the popular topics on HackerNews. You'll see three assets with different tags:

- `hackernews_topstory_ids` fetches a list of top story ids from a HackerNews endpoint.
- `hackernews_topstories` takes the list of ids and pulls the story details from HackerNews based on the ids.
- `hackernews_stories_word_cloud` visualizes the trending topics in a word cloud.

Dagster visualizes upstream and downstream dependencies vertically. Assets below other assets connected by arrows implies a dependency relationship. So we can tell from the UI that the asset `hackernews_topstories` depends on `hackernews_topstory_ids` (i.e. `hackernews_topstories` takes `hackernews_topstory_ids`'s output as an input) and `hackernews_stories_word_cloud` depends on `hackernews_topstories`.

All three assets are defined [in `quickstart_etl/assets/hackernews.py`](./quickstart_etl/assets/hackernews.py). Typically, you'll define assets by annotating ordinary Python functions with the [`@asset`](https://docs.dagster.io/concepts/assets/software-defined-assets#a-basic-software-defined-asset) decorator.

This project also comes with ways to better organize the assets:

- **Labeling/tagging.** You'll find the assets are tagged with different [labels/badges], such as `HackerNews API` and `Plot`. This is defined in code via the `compute_kind` argument to the `@asset` decorator. It can be any string value that represents the kind of computation that produces the asset and will be displayed in the UI as a badge on the asset. This can help us quickly understand the data logic from a bird's eye view.
- **Grouping assets**. We've also assigned all three assets to the group `hackernews`, which is accomplished by providing the `group_name` argument to the `@asset` decorator. Grouping assets can help keep assets organized as your project grows. Learn about asset grouping [here](https://docs.dagster.io/concepts/assets/software-defined-assets#assigning-assets-to-groups).
- **Adding descriptions.** In the asset graph, the UI also shows the description of each asset. You can specify the description of an asset in the `description` argument to `@asset`. When the argument is not provided and the decorated function has a docstring, Dagster will use the docstring as the description. In this example, the UI is using the docstrings as the descriptions.

Now that we've got a basic understanding of Dagster assets, let's materialize them.

<p align="center">
    <img height="500" src="../../docs/next/public/images/quickstarts/basic/step-1-2-materialize-all.png" />
</p>

Click **Materialize all** to kick off a Dagster run which will pull info from the external APIs and move the data through assets.

As you iterate, some assets may become outdated. To refresh them, you can select a subset of assets to run instead of re-running the entire pipeline. This allows us to avoid unnecessary re-runs of expensive computations, only re-materializing the assets that need to be updated. If assets take a long time to run or interact with APIs with restrictive rate limits, selectively re-materializing assets will come in handy.

<p align="center">
    <img height="500" src="../../docs/next/public/images/quickstarts/basic/step-1-3-view-run.png" />
</p>

You'll see an indicator pop up with the launched run ID. Click **View** to monitor the run in real-time. This will open a new tab in your browser:

<p align="center">
    <img height="500" src="../../docs/next/public/images/quickstarts/basic/step-1-4-compute-logs.png" />
</p>

The process will run for a bit. While it's running, you should see the real-time compute logs printed in the UI. _(It may take 1-2 minutes to fetch all top 500 stories from HackerNews in the `hackernews_topstories` step)._

## Step 2: Viewing and monitoring assets

When you materialize an asset, the object returned by your asset function is saved. Dagster makes it easy to save these results to disk, to blob storage, to a database, or to any other system. In this example the assets are saved to the file system. In addition to the asset materialization, your asset functions can also generate metadata that is directly visible in Dagster. To view the materialization details and metadata, click on the "ASSET_MATERIALIZATION" event. In this example, the `hackernews_stories_word_cloud` asset materializes a plot that is saved to disk, but we also add the plot as metadata to make it visible in Dagster.

<p align="center">
    <img height="500" src="../../docs/next/public/images/quickstarts/basic/step-2-5-asset-in-logs.png" />
</p>

Click **Show Markdown**. You'll see a word cloud of the top 500 HackerNews story titles generated by the `hackernews_topstories_word_cloud` asset:

<p align="center">
    <img height="500" src="../../docs/next/public/images/quickstarts/basic/step-2-6-hackernews_word_cloud.png" />
</p>

The metadata is recorded in the `hackernews_topstories_word_cloud` asset [in `quickstart_etl/assets/hackernews.py`](./quickstart_etl/assets/hackernews.py). Dagster supports attaching arbitrary [metadata](https://docs.dagster.io/_apidocs/ops#dagster.MetadataValue) to asset materializations. This metadata is also be displayed on the **Activity** tab of the **Asset Details** page in the UI or in the **Asset Lineage** view after selecting an asset. From the compute logs of a run, you can click the **View Asset** to go to the **Asset Details** page.

<p align="center">
    <img height="500" src="../../docs/next/public/images/quickstarts/basic/step-2-7-view-assets.png" />
</p>

This metadata would be useful for monitoring and maintaining the asset as you iterate. Similarly, we've also recorded some metadata in the `hackernews_topstories` asset. You can filter the compute logs by typing the asset name (e.g. `hackernews_topstories`) or the event type (e.g. `type:ASSET_MATERIALIZATION`) in the **Log Filter** input box:

<p align="center">
    <img height="500" src="../../docs/next/public/images/quickstarts/basic/step-2-8-filter.png" />
</p>

In the results, you'll see that the `hackernews_topstories` asset has two metadata entries: `num_records` and `preview`. Both are defined [in `quickstart_etl/assets/hackernews.py`](./quickstart_etl/assets/hackernews.py), in which we record the first five rows of the output Pandas DataFrame in the `preview` metadata entry using the Markdown type. This could help debug and keep your assets easily monitored. Click **Show Markdown** to view a preview of the output data frame:

<p align="center">
    <img height="500" src="../../docs/next/public/images/quickstarts/basic/step-2-9-preview.png" />
</p>

Note: You'll find a `path` metadata attached to every asset. This is because assets are, by default, materialized to pickle files on your local filesystem. In most projects, your assets will be materialized to a production system and you can fully customize the I/O using [I/O managers](https://docs.dagster.io/concepts/io-management/io-managers).

## Step 3: Scheduling a daily job

Finally, let's refresh our plots every day so we can monitor popular topics over time. To do so, we can use [schedules](https://docs.dagster.io/concepts/partitions-schedules-sensors/schedules#schedules).

We've defined a daily schedule and job in [`quickstart_etl/__init__.py`](./quickstart_etl/__init__.py) for all assets that are defined in the [`quickstart_etl/assets/`](./quickstart_etl/assets) module.

Now, let's turn on the daily schedule within Dagster.

1. In the left nav, it indicates the `all_assets_job` has a schedule associated with it but it's currently off. Clicking "all_assets_job" in the left nav will bring you to the job definition page.
2. Mouse over the schedule indicator on the top of the page to navigate to the individual schedule page for more info about the schedule.

<p align="center">
    <img height="500" src="../../docs/next/public/images/quickstarts/basic/step-3-1-schedule-off.png" />
</p>

You can now turn on the schedule switch to set up the daily job we defined in [quickstart_etl/**init**.py](./quickstart_etl/__init__.py).

<p align="center">
    <img height="500" src="../../docs/next/public/images/quickstarts/basic/step-3-2-schedule-on.png" />
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
    <img height="500" src="../../docs/next/public/images/quickstarts/basic/more-reload-code.png" />
</p>

</details>

Or from the left nav or on each job page:

<details><summary>👈 Expand to view the screenshot</summary>

<p align="center">
    <img height="500" src="../../docs/next/public/images/quickstarts/basic/more-reload-left-nav.png" />
</p>

</details>

### Using environment variables and secrets

Environment variables, which are key-value pairs configured outside your source code, allow you to dynamically modify application behavior depending on environment.

Using environment variables, you can define various configuration options for your Dagster application and securely set up secrets. For example, instead of hard-coding database credentials - which is bad practice and cumbersome for development - you can use environment variables to supply user details. This allows you to parameterize your pipeline without modifying code or insecurely storing sensitive data.

Check out [Using environment variables and secrets](https://docs.dagster.io/guides/dagster/using-environment-variables-and-secrets) for more info and examples.

### Adding new Python dependencies

You can specify new Python dependencies in `setup.py`.

### Testing

Tests are in the `quickstart_etl_tests` directory and you can run tests using `pytest`:

```bash
pytest quickstart_etl_tests
```
