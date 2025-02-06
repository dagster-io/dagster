---
title: "Using dbt with Serverless deployments in Dagster+"
description: Deploy your dbt & Dagster project with Serverless deployments in Dagster+.
---

Importing an existing dbt project in Dagster+ allows you to automatically load your dbt models as Dagster assets. This can be be done with:

- An existing dbt project that is not already using Dagster, or
- A Dagster project in which your dbt project is included

In this guide, we'll demonstrate by using an existing dbt project that doesn't use Dagster.

## Prerequisites

To follow the steps in this guide, you'll need **Dagster+ Organization Admin**, **Admin**, or **Editor** permissions. This is required to create a code location.

**For dbt-only projects**, you'll also need **an existing dbt project** that contains the following files in the repository root:

- [`dbt_project.yml`](https://docs.getdbt.com/reference/dbt_project.yml)
- [`profiles.yml`](https://docs.getdbt.com/docs/core/connect-data-platform/profiles.yml)

**For dbt and Dagster projects**, Dagster+ requires several files to be present in your project. Refer to the [dbt & Dagster tutorial](/integrations/libraries/dbt/using-dbt-with-dagster/) to learn more about the structure and files required in a dbt and Dagster project.

## Step 1: Import your project in Dagster+

In this section, we'll demonstrate how to import an existing project to Dagster+. Our example imports the project from a GitHub repository, but Dagster+ also supports Gitlab.

1. Sign in to your Dagster+ account.

2. Navigate to **Deployment > Code locations**.

3. Click **Add code location**.

4. Depending on the type of project you imported, this step will vary:

   - **For dbt-only projects**, click **Import a dbt project**, then **Continue**.
   - **For dbt and Dagster projects,** click **Import a Dagster project**.

5. At this point, you'll be prompted to select either GitHub or Gitlab. For this guide, we'll select **GitHub**.

6. If prompted, sign into your GitHub account and complete the authorization process for the Dagster+ application. **Note**: The profile or organization you're using to authorize Dagster+ must have read and write access to the repository containing the project. After the authorization is complete, you'll be redirected back to Dagster+.

7. In Dagster+, locate and select the repository containing the project by using the dropdowns. **Note**: dbt projects must have `dbt_profiles.yml` and `profiles.yml` files in the repository root or an error will display.

8. Click **Continue** to begin the import process.

9. The last step of the import process adds a few files, which we'll discuss in the next section, to the project. Depending on the type of project you imported, this step will vary:

   - **For dbt-only projects**, Dagster+ will open a pull request to update the repository. You'll need to review and merge the pull request to complete the process.
   - **For dbt and Dagster projects,** Dagster+ will directly commit the files to the repository.

Once Dagster+ finishes importing the project, move onto the next step.

## Step 2: Review the repository changes

The file structure of the repository will change the first time a project is deployed using Dagster+. For dbt projects, a few things will happen:

- **A [`dagster_cloud.yaml` file](/dagster-plus/deployment/code-locations/dagster-cloud-yaml) will be created.** This file defines the project as a Dagster+ code location.
- **A few `.yml` files, used for CI/CD, will be created in `.github/workflows`.** [These files](/dagster-plus/features/ci-cd/ci-cd-file-reference), named `branch_deployments.yml` and `deploy.yml`, manage the deployments of the repository.
- **For dbt-only projects being deployed for the first time**, Dagster+ will create a new Dagster project in the repository using the [`dagster-dbt scaffold`](/integrations/libraries/dbt/reference#scaffolding-a-dagster-project-from-a-dbt-project) command. This will result in a Dagster project that matches the dbt project. For example, a dbt project named `my_dbt_project` will contain a Dagster project in `my_dbt_project/my_dbt_project` after the process completes.

**Use the following tabs** to see how the repository will change for a dbt-only project and a dbt and Dagster project being deployed for the first time.

<Tabs>
<TabItem value="dbt-only projects">

Before the Dagster+ changes, a typical dbt project would include files like `dbt_project.yml`, `profiles.yml`, dbt models in `.sql` format, and sbt seeds in `.csv` format. As this is a git repository, other files like `.gitignore`, `LICENSE` and `README.md` may also be included:

```shell
## dbt-only project
## before Dagster+ deployment

my_dbt_project
├── models
│   ├── my_model.sql
├── seeds
│   ├── my_seeds.csv
├── .gitignore
├── LICENSE
├── README.md
├── dbt_project.yml
└── profiles.yml
```

When the Dagster+ deployment process completes, the repository will now look like the following:

```shell
## dbt-only project
## after Dagster+ deployment

my_dbt_project
├── .github                                                ## CI/CD files
│   ├── workflows
│   │   ├── branch_deployments.yml
│   │   ├── deploy.yml
├── models
│   ├── my_model.sql
├── my_dbt_project                                         ## New Dagster project
│   ├── my_dbt_project
│   │   ├── __init__.py
│   │   ├── assets.py
│   │   ├── definitions.py
│   │   ├── project.py
│   │   ├── schedules.py
│   ├── pyproject.toml
│   ├── setup.py
├── seeds
│   ├── my_seeds.csv
├── .gitignore
├── LICENSE
├── README.md
├── dagster_cloud.yaml                                     ## Dagster+ code location file
├── dbt_project.yml
└── profiles.yml
```

</TabItem>
<TabItem value="dbt and Dagster projects">

After the Dagster+ changes, a dbt and Dagster project will include the files required for dbt and Dagster, some files related to git, and the newly-added Dagster+ files:

```shell
## dbt and Dagster project
## after Dagster+ deployment

my_dbt_and_dagster_project
├── .github                                                ## CI/CD files
│   ├── workflows
│   │   ├── branch_deployments.yml
│   │   ├── deploy.yml
├── dbt
│   ├── models
│   │   ├── my_model.sql
│   ├── seeds
│   │   ├── my_seeds.csv
│   ├── dbt_project.yml
│   ├── profiles.yml
├── my_dbt_and_dagster_project
│   ├── __init__.py
│   ├── assets.py
│   ├── definitions.py
│   ├── project.py
│   ├── schedules.py
├── .gitignore
├── LICENSE
├── README.md
├── dagster_cloud.yaml                                     ## Dagster+ code location file
├── pyproject.toml
└── setup.py
```

</TabItem>
</Tabs>

## Step 3: Update the CI/CD files

:::note

This step only applies to dbt and Dagster projects. Skip this step if you imported a dbt-only project.

:::

The last step is to update the [CI/CD files](/dagster-plus/features/ci-cd/ci-cd-file-reference) in the repository. When you import a dbt project into Dagster+ using the **Import a Dagster project** option, you'll need to add a few steps to allow the dbt project to deploy successfully.

1. In your Dagster project, locate the `.github/workflows` directory.

2. Open the `deploy.yml` file.

3. Locate the `Checkout for Python Executable Deploy` step, which should be on or near line 38.

4. After this step, add the following:

   ```yaml
   - name: Prepare DBT project for deployment
     if: steps.prerun.outputs.result == 'pex-deploy'
     run: |
       python -m pip install pip --upgrade
       cd project-repo
       pip install . --upgrade --upgrade-strategy eager                                            ## Install the Python dependencies from the setup.py file, ex: dbt-core and dbt-duckdb
       dagster-dbt project prepare-and-package --file <DAGSTER_PROJECT_FOLDER>/project.py          ## Replace with the project.py location in the Dagster project folder
     shell: bash
   ```

   When you add this step, you'll need to:

   - **Add any [adapters](https://docs.getdbt.com/docs/connect-adapters) and libraries used by dbt to your `setup.py` file**. In this example, we're using `dbt-core` and `dbt-duckdb`.
   - **Add the location of your Dagster project directory** to the `dagster-dbt project prepare-and-package` command. In this example, our project is in the `/my_dbt_and_dagster_project` directory.

5. Save the changes.

6. Open the `branch_deployments.yml` file and repeat steps 3 - 5.

7. Commit the changes to the repository.

Once the new step is pushed to the remote, GitHub will automatically try to run a new job using the updated workflow.

## What's next?

For an end-to-end example, from the project creation to the deployment to Dagster+, check out the Dagster & dbt course in [Dagster University](https://courses.dagster.io).
