---
title: Assets
description: Building your first assets
sidebar_position: 20
---

[Software-defined assets](/guides/build/assets) are the primary building blocks in Dagster. They represent the underlying entities in our pipelines, such as database tables, machine learning models, or AI processes. Together, these assets form the data platform. In this step, you will define the initial assets that represent the data you will work with throughout this tutorial.

All Dagster objects, such as assets, are added to the `Definitions` object that was created when you initialized your project.

![2048 resolution](/images/tutorial/dagster-tutorial/overviews/assets.png)

## 1. Scaffold an assets file

When building assets, the first step is to scaffold an assets file with the [`dg scaffold` command](/api/clis/dg-cli/dg-cli-reference#dg-scaffold):

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/dagster_tutorial/commands/dg-scaffold-assets.txt" />

This adds a file called `assets.py` to your Dagster project, which will contain your asset code. Using `dg` to create the file ensures it is placed where Dagster can automatically discover it:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/dagster_tutorial/tree/assets.txt" />

## 2. Define the assets

Now that you have an assets file, you can define your asset code. You define an asset using the <PyObject section="assets" module="dagster" object="asset" decorator /> decorator. Any function with this decorator will be treated as an asset and included in the Dagster asset graph.

You will create one asset for each of the three source files used in this tutorial:

- raw_customers.csv
- raw_orders.csv
- raw_payments.csv

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/dagster_tutorial/src/dagster_tutorial/defs/assets.py"
  language="python"
  startAfter="start_define_assets"
  endBefore="end_define_assets"
  title="src/dagster_tutorial/defs/assets.py"
/>

For now, these assets will simply represent the underlying files. Next, we will discuss how Dagster knows to load them.

## 3. Check definitions

In Dagster, all defined objects (such as assets) need to be associated with a top-level <PyObject section="definitions" module="dagster" object="Definitions" /> object in order to be deployed. When you first created your project with `uvx create-dagster project`, a `definitions.py` file was also created:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/dagster_tutorial/src/dagster_tutorial/definitions.py"
  language="python"
  title="src/dagster_tutorial/definitions.py"
/>

This `Definitions` object loads the module and automatically discovers all assets and other Dagster objects. There is no need to explicitly reference assets as they are created. However, it is good practice to check that the `Definitions` object can be loaded without error as new Dagster objects are added.

You can use the [`dg check defs`](/api/clis/dg-cli/dg-cli-reference#dg-check) command to ensure everything in your module loads correctly, and that your project is deployable:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/dagster_tutorial/commands/dg-check-defs.txt" />

This confirms there are no issues with any of the assets you have defined. As you develop your Dagster project, it is a good habit to run `dg check` to ensure everything works as expected.

## 4. Materialize the assets

Now that your assets are configured and you have verified that the top-level `Definitions` object is valid, you can view the asset catalog in the Dagster UI and reload the definitions:

1. In a browser, navigate to [http://127.0.0.1:3000](http://127.0.0.1:3000), or restart `dg dev` if it has been closed.
2. Navigate to **Assets**.
3. Click **Reload definitions**.

   ![2048 resolution](/images/tutorial/dagster-tutorial/asset-1.png)

You should now see three assets, one for each of the raw files (customers, orders, payments).

To materialize the assets:

1. Click **Assets**, then click **View lineage** to see all assets.
2. Click **Materialize all**.

   ![2048 resolution](/images/tutorial/dagster-tutorial/asset-2.png)

:::tip

You can also materialize assets from the command line with [`dg launch`](/api/clis/dg-cli/dg-cli-reference#dg-launch). To materialize all assets, use the `*` asset selection:

<CliInvocationExample contents='dg launch --assets "*"' />

To materialize specific assets, pass an [asset selection](/guides/build/assets/asset-selection-syntax) specifying them:

<CliInvocationExample contents="dg launch --assets customers,orders,payments" />

:::
