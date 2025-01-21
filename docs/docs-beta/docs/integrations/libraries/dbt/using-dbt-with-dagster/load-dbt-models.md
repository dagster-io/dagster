---
title: "Load dbt models as Dagster assets"
description: Dagster can orchestrate dbt alongside other technologies.
sidebar_position: 200
---

At this point, you should have a [fully-configured dbt project](set-up-dbt-project) that's ready to work with Dagster.

In this section, you'll finally begin integrating dbt with Dagster. To do so, you'll:

- [Create a Dagster project that wraps your dbt project](#step-1-create-a-dagster-project-that-wraps-your-dbt-project)
- [Inspect your Dagster project in Dagster's UI](#step-2-inspect-your-dagster-project-in-dagsters-ui)
- [Build your dbt models in Dagster](#step-3-build-your-dbt-models-in-dagster)
- [Understand the Python code in your Dagster project](#step-4-understand-the-python-code-in-your-dagster-project)

## Step 1: Create a Dagster project that wraps your dbt project

You can create a Dagster project that wraps your dbt project by using the `dagster-dbt` command line interface. Make sure you're in the directory where your `dbt_project.yml` is. If you're continuing from the previous section, then you'll already be in this directory. Then, run:

```shell
dagster-dbt project scaffold --project-name jaffle_dagster
```

This creates a directory called `jaffle_dagster/` inside the current directory. The `jaffle_dagster/` directory contains a set of files that define a Dagster project.

In general, it's up to you where to put your Dagster project. It's most common to put your Dagster project at the root of your git repository. Therefore, in this case, because the `dbt_project.yml` was at the root of the `jaffle_shop` git repository, we created our Dagster project there.

**Note**: The `dagster-dbt project scaffold` command creates the Dagster project in whatever directory you run it from. If that's a different directory from where your `dbt_project.yml` lives, then you'll need to provide a value for the `--dbt-project-dir` option so that Dagster knows where to look for your dbt project.

## Step 2: Inspect your Dagster project in Dagster's UI

Now that you have a Dagster project, you can run Dagster's UI to take a look at it.

1. Change directories to the Dagster project directory:

   ```shell
   cd jaffle_dagster/
   ```

2. To start Dagster's UI, run the following:

   ```shell
   dagster dev
   ```

   Which will result in output similar to:

   ```shell
   Serving dagster-webserver on http://127.0.0.1:3000 in process 70635
   ```

3. In your browser, navigate to [http://127.0.0.1:3000](http://127.0.0.1:3000) The page will display the assets:

![Asset graph in Dagster's UI, containing dbt models loaded as Dagster assets](/images/integrations/dbt/using-dbt-with-dagster/load-dbt-models/asset-graph.png)

## Step 3: Build your dbt models in Dagster

You can do more than view your dbt models in Dagster – you can also run them. In Dagster, running a dbt model corresponds to _materializing_ an asset. Materializing an asset means running some computation to update its contents in persistent storage. In this tutorial, that persistent storage is our local DuckDB database.

To build your dbt project, i.e. materialize your assets, click the **Materialize all** button near the top right corner of the page. This will launch a run to materialize the assets. When finished, the **Materialized** and **Latest Run** attributes in the asset will be populated:

![Asset graph in Dagster's UI, showing materialized assets](/images/integrations/dbt/using-dbt-with-dagster/load-dbt-models/asset-graph-materialized.png)

After the run completes, you can:

- Click the **asset** to open a sidebar containing info about the asset, including its last materialization stats and a link to view the **Asset details** page
- Click the ID of the **Latest Run** in an asset to view the **Run details** page. This page contains detailed info about the run, including timing information, errors, and logs.

## Step 4: Understand the Python code in your Dagster project

You saw how you can create a Dagster project that loads a dbt project. How does this work? Understanding how Dagster loads a dbt project will give you a foundation for customizing how Dagster runs your dbt project, as well as for connecting it to other data assets outside of dbt.

The most important file is the Python file that contains the set of definitions for Dagster to load: `jaffle_shop/definitions.py`. Dagster executes the code in this file to find out what assets it should be aware of, as well as details about those assets. For example, when you ran `dagster dev` in the previous step, Dagster executed the code in this file to determine what assets to display in the UI.

In our `definitions.py` Python file, we import from `assets.py`, which contains the code to model our dbt models as Dagster assets. To return a Dagster asset for each dbt model, the code in this `assets.py` file needs to know what dbt models you have. It finds out what models you have by reading a file called a `manifest.json`, which is a file that dbt can generate for any dbt project and contains information about every model, seed, snapshot, test, etc. in the project.

To retrieve the `manifest.json`, `assets.py` imports from `project.py`, which defines an internal representation of your dbt project. Then, in `assets.py`, the path to the `manifest.json` file can be accessed with `dbt_project.manifest_path`:

<CodeExample path="docs_snippets/docs_snippets/integrations/dbt/tutorial/load_dbt_models/project.py" startAfter="start_load_project" endBefore="=end_load_project" />

Generating the `manifest.json` file for a dbt project is time-consuming, so it's best to avoid doing so every time this Python module is imported. Thus, in production deployments of Dagster, you'll typically have the CI/CD system that packages up your code generate your `manifest.json`.

However, in development, you typically want changes made to files in your dbt project to be immediately reflected in the Dagster UI without needing to regenerate the manifest.

`dbt_project.prepare_if_dev()` helps with this – it re-generates your `manifest.json` at the time Dagster imports your code, _but_ only if it's being imported by the `dagster dev` command.

Once you've got a `manifest.json` file, it's time to define your Dagster assets using it. The following code, in your project's `assets.py`, does this:

<CodeExample path="docs_snippets/docs_snippets/integrations/dbt/tutorial/load_dbt_models/assets.py" startAfter="start_dbt_assets" endBefore="=end_dbt_assets" />

This code might look a bit fancy, because it uses a decorator. Here's a breakdown of what's going on:

- It creates a variable named `jaffle_shop_dbt_assets` that holds an object that represents a set of Dagster assets.
- These Dagster assets reflect the dbt models described in the manifest file. The manifest file is passed in using the `manifest` argument.
- The decorated function defines what should happen when you materialize one of these Dagster assets, e.g. by clicking the **Materialize** button in the UI or materializing it automatically by putting it on a schedule. In this case, it will invoke the `dbt build` command on the selected assets. The `context` parameter that's provided along with `dbt build` carries the selection.

If you later want to customize how your dbt models are translated into Dagster assets, you'll do so by editing its definition in `assets.py`.

## What's next?

At this point, you've loaded your dbt models into Dagster as assets, viewed them in Dagster's asset graph UI, and materialized them. Next, you'll learn how to [add upstream Dagster assets](upstream-assets).
