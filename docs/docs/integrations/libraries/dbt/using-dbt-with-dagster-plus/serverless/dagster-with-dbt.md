---
title: Importing a Dagster project that includes a dbt project
description: Deploy your dbt & Dagster project with Serverless deployments in Dagster+.
sidebar_position: 200
---

Importing an existing dbt project in Dagster+ allows you to automatically load your dbt models as Dagster assets. In this guide, we'll demonstrate by using an existing Dagster project that includes a dbt project.

## Prerequisites

To follow the steps in this guide, you'll need **Dagster+ Organization Admin**, **Admin**, or **Editor** permissions in order to create a code location.

Additionally, Dagster+ requires several files to be present in your project. To learn more about the structure and files required in a dbt and Dagster project, see "[Creating a dbt project in a Dagster project](/integrations/libraries/dbt/using-dbt-with-dagster-plus)".

## Step 1: Import your project in Dagster+

In this section, we'll demonstrate how to import an existing project to Dagster+. Our example imports the project from a GitHub repository, but Dagster+ also supports Gitlab.

1. Sign in to your Dagster+ account.

2. Navigate to **Deployment > Code locations**.

3. Click **Add code location**.

4. Click **Import a Dagster project**.

5. At this point, you'll be prompted to select either GitHub or Gitlab. For this guide, we'll select **GitHub**.

6. If prompted, sign into your GitHub account and complete the authorization process for the Dagster+ application. **Note**: The profile or organization you're using to authorize Dagster+ must have read and write access to the repository containing the project. After the authorization is complete, you'll be redirected back to Dagster+.

7. In Dagster+, locate and select the repository containing the project by using the dropdowns. **Note**: dbt projects must have `dbt_profiles.yml` and `profiles.yml` files in the repository root or an error will display.

8. Click **Continue** to begin the import process. Dagster+ will directly commit the files to the repository.

## Step 2: Review the repository changes

The file structure of the repository will change the first time a project is deployed using Dagster+. For dbt projects, a few things will happen:

- **A [`dagster_cloud.yaml` file](/deployment/code-locations/dagster-cloud-yaml) will be created.** This file defines the project as a Dagster+ code location.
- **A few `.yml` files, used for CI/CD, will be created in `.github/workflows`.** [These files](/deployment/dagster-plus/ci-cd/ci-cd-file-reference), named `branch_deployments.yml` and `deploy.yml`, manage the deployments of the repository.

### How the repository will change after the project is deployed for the first time

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

## Step 3: Update the CI/CD files

The last step is to update the [CI/CD files](/deployment/dagster-plus/ci-cd/ci-cd-file-reference) in the repository. When you import a dbt project into Dagster+ using the **Import a Dagster project** option, you'll need to add a few steps to allow the dbt project to deploy successfully.

### Update `deploy.yml` and `branch_deployments.yml`

1. In your Dagster project, locate the `.github/workflows` directory.

2. Open the `deploy.yml` file.

3. Locate the `Initialize build session` step.

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
   - **Add the location of your file defining your DbtProject** to the `dagster-dbt project prepare-and-package` command. In this example, our project is in the `/my_dbt_and_dagster_project/project.py` directory. If you are using [Components](/guides/build/components), you can use the `--components` flag with a path to your project root.

5. Save the changes.

6. Open the `branch_deployments.yml` file and repeat steps 3 - 5.

7. Commit the changes to the repository.

Once the new step is pushed to the remote, GitHub will automatically try to run a new job using the updated workflow.

### Update `profiles.yml`

To ensure your project parses correctly with `dbt parse`, you need to include credentials in your `profiles.yml` file. You can use dummy credentials, since `dbt parse` doesn't connect to your data warehouse.

1. In your Dagster project, locate the `dbt` directory.
2. Open the `profiles.yml` file and add the following:
   ```yaml
   my_profile:
     target: dev
     outputs:
       dev:
         type: snowflake
         account: "{{ env_var('SNOWFLAKE_ACCOUNT', 'dummy-account') }}"
         user: "{{ env_var('SNOWFLAKE_USER', 'dummy-user') }}"
         password: "{{ env_var('SNOWFLAKE_PASSWORD', 'dummy-password') }}"
   ```
3. Save the changes.
4. Commit the changes to the repository.
