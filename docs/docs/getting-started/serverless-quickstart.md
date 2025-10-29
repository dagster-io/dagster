---
title: Quickstart (Dagster+ Serverless)
description: Iterate on, test, and deploy your first Dagster+ Serverless pipeline
---

import InstallUv from '@site/docs/partials/\_InstallUv.md';

Welcome to Dagster! In this guide, we'll cover developing and testing your Dagster project locally, using branch deployments to test against a production environment, and finally, pushing your changes to production.

:::info Dagster OSS and Dagster+ Hybrid users

To get started with Dagster+ Hybrid or Dagster OSS, see the [Dagster+ Hybrid and OSS quickstart guide](/getting-started/quickstart) instead.

:::

## Prerequisites

To follow the steps in this guide, you will need to:

- Sign up for a [Dagster+ Serverless](https://dagster.plus/signup) account and create a Dagster project
- Clone your Dagster project to your local machine
- Ensure you have Python 3.9+ installed

## Step 1: Install `uv` (Recommended)

:::note

If you will be using `pip`, skip to [step 2.](#step-2-configure-your-project)

:::

If you will be using `uv` as your package manager, follow the steps below to install the [Python package manager `uv`](https://docs.astral.sh/uv/getting-started/installation):

<InstallUv />

## Step 2: Install project dependencies

<Tabs groupId="package-manager">
   <TabItem value="uv" label="uv">
      1. Change to the directory of your cloned project:

         ```shell
         cd <project-directory>
         ```
      2. Activate the virtual environment:

         <Tabs>
            <TabItem value="macos" label="MacOS/Unix">
               ```shell
               source .venv/bin/activate
               ```
            </TabItem>
            <TabItem value="windows" label="Windows">
               ```shell
               .venv\Scripts\activate
               ```
            </TabItem>
         </Tabs>

      3. Install any required dependencies in the virtual environment:

         ```shell
         uv sync
         ```

   </TabItem>

   <TabItem value="pip" label="pip">
      1. Change to the directory of your cloned project:

         ```shell
         cd <project-directory>
         ```
      2. Create and activate a virtual environment:

         <Tabs>
            <TabItem value="macos" label="MacOS/Unix">
               ```shell
               python -m venv .venv
               ```
               ```shell
               source .venv/bin/activate
               ```
            </TabItem>
            <TabItem value="windows" label="Windows">
               ```shell
               python -m venv .venv
               ```
               ```shell
               .venv\Scripts\activate
               ```
            </TabItem>
         </Tabs>

      3. Install your project as an editable package:

         ```shell
         pip install --editable .
         ```

   </TabItem>
</Tabs>

## Step 3: Start the webserver and run your pipeline

1. In the terminal, navigate to your project's root directory and run:

   ```bash
   dg dev
   ```

2. Open your web browser and navigate to [http://localhost:3000](http://localhost:3000), where you should see the Dagster UI:

   TK - add screenshot

3. In the top navigation, click **Assets > View lineage**.

4. Click **Materialize** to run the pipeline.

5. In the popup, click **View**. This will open the **Run details** page, allowing you to view the run as it executes.

   TK - add screenshot

   Use the **view buttons** in the top left corner of the page to change how the run is displayed. You can also click on the asset to view logs and metadata.

:::tip

You can also run the pipeline by using the [`dg launch --assets`](/api/clis/dg-cli/dg-cli-reference#dg-launch) command and passing an [asset selection](/guides/build/assets/asset-selection-syntax):

```
dg launch --assets "*"
```

:::

## Step 4: Develop and test your pipeline

To develop your pipeline, you can:

- Update and create [assets](/guides/build/assets)
- [Automate](/guides/automate) your pipeline
- Add [integrations](/integrations/libraries)

To test your pipeline, you can:

- Run `dg check defs` to check Dagster definitions
- Run `dg dev` to start the local webserver and run your pipeline in the UI
- Add [asset checks](/guides/test/asset-checks)
- [Debug assets during execution with `pdb`](/guides/log-debug/debugging/debugging-pdb)

## Step 5: Deploy to staging with branch deployments

To see how your changes will look in production without altering production data, you can use branch deployments. If you add your changes to a branch and create a pull request, the changes will appear in your Serverless deployment. For more information, see the [branch deployments docs](/deployment/dagster-plus/deploying-code/branch-deployments).

## Step 6: Deploy to production

Once you are satisfied with your changes, you can merge your branch into `main`, and the changes will be deployed to your production Serverless deployment.

## Next steps

Congratulations! You've just built and run your first pipeline with Dagster. Next, you can:

- Follow the [Tutorial](/dagster-basics-tutorial) to learn how to build a more complex ETL pipeline
- [Create your own Dagster project](/guides/build/projects/creating-a-new-project) and [add assets](/guides/build/assets/defining-assets) to it
- Check out our [Python primer series](https://dagster.io/blog/python-packages-primer-1) for an in-depth tour of Python modules, packages and imports