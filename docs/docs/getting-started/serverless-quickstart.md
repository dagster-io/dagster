---
title: Quickstart (Dagster+ Serverless)
description: Iterate on, test, and deploy your first Dagster+ Serverless pipeline
---

TK - intro copy.

import InstallUv from '@site/docs/partials/\_InstallUv.md';

:::info Prerequisites

To follow the steps in this guide, you will need to:

- Sign up for a [Dagster+ Serverless](https://dagster.plus/signup) account.
- Choose a template repository, and clone the repository to your local machine.
- Ensure Python 3.9+ is installed on your local machine.

:::

## Step 1: Install `uv` (Recommended)

:::note

If you will be using `pip`, skip to [step 2.](#step-2-configure-your-project)

:::

If you will be using `uv` as your package manager, follow the steps below to install the Python package manager [`uv`](https://docs.astral.sh/uv/getting-started/installation):

<InstallUv />

## Step 2: Configure your project

<Tabs groupId="package-manager">
   <TabItem value="uv" label="uv">
      1. Change to the directory of your cloned project:

         ```shell
         cd <project-directory>
         ```
      4. Activate the virtual environment:

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

      5. Install any required dependencies in the virtual environment:

         ```shell
         uv add <package-name>
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

      4. Install the required dependencies:

         ```shell
         pip install pandas
         ```

      5. Install your project as an editable package:

         ```shell
         pip install --editable .
         ```

   </TabItem>
</Tabs>

## Step 3: Develop and test locally

TK - development:

- Create assets
- Automate your pipeline
- Add integrations

TK - testing:

- Run `dg check defs`
- Run `dg dev` to start the webserver and run your pipeline in the UI
- Add asset checks
- Debug with `pdb`

## Step 4: Deploy to staging with branch deployments

TK - see branch deployments docs

## Step 5: Deploy to production

TK - any config changes to make before deploying? or is this just a matter of merging branch to `main` and CI/CD takes care of it?
