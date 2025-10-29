---
title: Develop and deploy your first Dagster pipeline
sidebar_label: Quickstart (Dagster+ Serverless)
description: Iterate on, test, and deploy your first Dagster+ Serverless pipeline
---

import InstallUv from '@site/docs/partials/\_InstallUv.md';

Welcome to Dagster+ Serverless! In this guide, we'll cover developing and testing your Dagster project locally, using branch deployments to safely test against production data, and finally, pushing your changes to production.

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

      3. Install required dependencies in the virtual environment:

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

## Step 3: Run your pipeline

1. In the terminal, navigate to your project's root directory and run:

   ```bash
   dg dev
   ```

2. Open your web browser and navigate to [http://localhost:3000](http://localhost:3000), where you should see the Dagster UI:

   ![Dagster UI overview](/images/getting-started/quickstart-serverless/oss-ui-overview.png)

3. In the top navigation, click the **Assets** tab, then click **View lineage**:

   ![Dagster UI asset lineage page](/images/getting-started/quickstart-serverless/oss-ui-assets-view-lineage.png)

4. To run the pipeline, click **Materialize all**:

   ![Dagster asset lineage page with materialize all button](/images/getting-started/quickstart-serverless/oss-ui-materialize-all.png)

5. To view the run as it executes, click the **Runs** tab, then on the right side of the page, click **View**:

   ![Dagster run view](/images/getting-started/quickstart-serverless/oss-ui-run-view.png)

   To change how the run is displayed, you can use the **view buttons** in the top left corner of the page:

   <img src="/images/getting-started/quickstart-serverless/oss-ui-run-view-options.png" height="100" />

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

To see how your changes will look in production without altering production data, you can use [branch deployments](/deployment/dagster-plus/deploying-code/branch-deployments). To get started, make your changes in a Git branch and create a pull request, then select your branch from the deployment dropdown in the Dagster+ Serverless UI:

<img src="/images/getting-started/quickstart-serverless/branch-deployment-switcher.png" height="400" />

## Step 6: Deploy to production

Once you are satisfied with your changes, you can merge your branch into `main` and the changes will be deployed to your production Serverless deployment.

## Next steps

Congratulations! You've just built and run your first pipeline with Dagster. Next, you can:

- Follow the [Dagster Basics Tutorial](/dagster-basics-tutorial) to learn how to build a more complex ETL pipeline.
- [Create your own Dagster project](/guides/build/projects/creating-a-new-project) and [add assets](/guides/build/assets/defining-assets) to it.
- Check out our [Python primer series](https://dagster.io/blog/python-packages-primer-1) for an in-depth tour of Python modules, packages and imports.