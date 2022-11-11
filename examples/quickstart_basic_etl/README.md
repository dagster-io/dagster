# Dagster starter kit

This example is a starter kit for building a daily ETL pipeline. It showcases Dagster's basic features such as **[Assets](https://docs.dagster.io/concepts/assets/software-defined-assets)** and **[Schedules](https://docs.dagster.io/concepts/partitions-schedules-sensors/schedules)**. It also follows Dagster's recommendations on [using environment variables and secrets](https://docs.dagster.io/guides/dagster/using-environment-variables-and-secrets) to ensure the project is production-ready.

This project is scaffolded with [`dagster project scaffold`](https://docs.dagster.io/getting-started/create-new-project).


## Introduction

<p align="center">
    <img height="500" src="https://user-images.githubusercontent.com/4531914/200668814-2c0be35e-25eb-4555-a3a5-f7e52ff792f4.png">
</p>


In this project, we're building an analytical pipeline that:
* Fetches data from [HackerNews](https://github.com/HackerNews/API) and [GitHub](https://pygithub.readthedocs.io) APIs.
* Transforms and aggregates the collected data using [Pandas](http://pandas.pydata.org/pandas-docs/stable/).
* Creates visualizations for exploratory analysis (e.g. [word cloud](https://github.com/amueller/word_cloud) based on trending HackerNews stories).
* Generates a daily metrics report.


## Getting started

### Option 1: Deploying it on Dagster Cloud

The easiest way to spin up your Dagster project is to use Dagster Cloud.

Check out the [Dagster Cloud Documentation](https://docs.dagster.io/dagster-cloud) to learn more.

<TODO: add a button to link to NUX template flow?>


### Option 2: Running it locally

Bootstrap your own Dagster project with this example:

```bash
dagster project from-example --name my-dagster-project --example quickstart_etl
```

First, install your Dagster repository as a Python package. By using the --editable flag, pip will install your repository in ["editable mode"](https://pip.pypa.io/en/latest/topics/local-project-installs/#editable-installs) so that as you develop, local code changes will automatically apply.

```bash
pip install -e ".[dev]"
```

Then, start the Dagit web server:

```bash
dagit
```

Open http://localhost:3000 with your browser to see the project.

You can start writing assets in `quickstart_basic_etl/assets/`. The assets are automatically loaded into the Dagster repository as you define them.

<!-- ### Option 3: Running it in Gitpod
Open source friendly
<TODO: set up gitpod> -->

## Step 1: Materializing assets

An asset is a software object that models a data asset, which can be a file in your filesystem, a table in a database, or a data report.

Navigate to `hackernews` asset group. You will find four assets with different tags in the group:
* `hackernews_topstory_ids` fetches a list of top story ids from a HackerNews endpoint
* `hackernews_topstories` takes the list of ids and pulls the story details from HackerNews based on the ids.
* `hackernews_stories_by_date` aggregates stories by date, which later will be used to generate a metrics report.
* `hackernews_stories_word_cloud` explores the dataset by visualizing the word cloud of trending story titles.

<p align="center">
    <img height="500" src="https://user-images.githubusercontent.com/4531914/200672470-fe8c7880-6fb7-4ec7-b5a6-c167416cbf1c.png">
</p>

Click `Materialize all`. Now you've launched a Dagster run and it will materialize all the assets in this group. *(It may take 1-2 minutes to fetch all top 500 stories from HackerNews).*

## Step 2: Viewing assets

Once the run finishes, go to <TODO: relative url?>. You can now find a preview of the asset you just materialized.

<TODO: point out dataframe preview. explain asset metadata>

<p align="center">
    <img height="500" src="https://user-images.githubusercontent.com/4531914/201304011-0c62ad06-36d8-4984-9278-b3b670254da3.png">
</p>


<TODO: explain word cloud plot 👇 . need to find a cloud friendly way to view the plot>

<p align="center">
    <img height="500" src="https://user-images.githubusercontent.com/4531914/201312310-44fb053c-9352-498d-9c23-ab4d7be6afec.png">
</p>

## Step 3: Configuring data pipelines

You've got your first couple of assets generated. Let's add one more data source to the pipeline: GitHub.

Navigate to the `github` asset group and click `Materialize all`. When you try to materialize assets in this group, you may encounter the following error:
<p align="center">
    <img height="500" src="https://user-images.githubusercontent.com/4531914/200670846-625d1196-c421-4906-82fc-1d045c51e158.png">
</p>

<TODO: explain config and env vars>

### Step 3.1: Setting up GitHub Token

#### 1) Generating GitHub Personal Access Token

<TODO: how to generate github PAT>

<p align="center">
    <img height="500" src="https://user-images.githubusercontent.com/4531914/201305411-76f0c39f-887b-4162-a15e-e41fba001320.png">
</p>

#### 2) Adding the token as an environment variable

1. Add the token to your environment: `export MY_GITHUB_TOKEN="blahblahblah-todo-put-something-looks-like-a-token-here" inside either your `.bash_profile`, `.bashrc`, or `.zshrc`. *Important: You will need to `source` your bash profile (or restart the terminal) afterwards.
2. Verify you see your token: Open a new terminal and run `echo $MY_GITHUB_TOKEN`.
3. All set! Start `dagit` again and now you should be able to materialize all the `github` assets using your own GitHub token.

#### 3) (Dagster Cloud) Environment Variable page

<TODO: add env var to dagster cloud>

### Step 3.2: (Optional) Sampling data fetching

<details><summary>Expand to view</summary>

<p align="center">
    <img height="500" src="https://user-images.githubusercontent.com/4531914/200671284-c716efa5-1a0f-4a54-a79b-5247f1589374.png">
</p>

```yaml
ops:
  hackernews_topstories:
    config:
      sample_size: 100
```

</details>


### Step 3.3: (Optional) Filtering stories by keyword


<details><summary>Expand to view</summary>

<p align="center">
    <img height="500" src="https://user-images.githubusercontent.com/4531914/200671547-11073c00-fe35-4296-9457-b41a8e8ab395.png">
</p>

```yaml
ops:
  hackernews_stories_by_date:
    config:
      keyword: twitter
```

</details>


## Step 4: Turning on the daily schedule

Go to <TODO: schedule page>. Turn on the schedule.
<p align="center">
    <img height="500" src="https://user-images.githubusercontent.com/4531914/200672130-dd2f0cdc-e767-448b-9ed0-b05eaa4a9c69.png">
</p>

Congratulations 🎉 You now have a daily metrics report running in production!

## Learn more

<TODO: links to other post NUX guides>

### Adding new Python dependencies

You can specify new Python dependencies in `setup.py`.

### (Optional) Unit testing

<details><summary>Expand to view</summary>

Tests are in the `quickstart_basic_etl_tests` directory and you can run tests using `pytest`:

```bash
pytest quickstart_basic_etl_tests
```

</details>


### (Optional) Schedules and sensors


<details><summary>Expand to view</summary>

If you want to enable Dagster [Schedules](https://docs.dagster.io/concepts/partitions-schedules-sensors/schedules) or [Sensors](https://docs.dagster.io/concepts/partitions-schedules-sensors/sensors) for your jobs, start the [Dagster Daemon](https://docs.dagster.io/deployment/dagster-daemon) process in the same folder as your `workspace.yaml` file, but in a different shell or terminal.

The `$DAGSTER_HOME` environment variable must be set to a directory for the daemon to work. Note: using directories within /tmp may cause issues. See [Dagster Instance default local behavior](https://docs.dagster.io/deployment/dagster-instance#default-local-behavior) for more details.

```bash
dagster-daemon run
```

Once your Dagster Daemon is running, you can start turning on schedules and sensors for your jobs. -->


</details>
