---
title: Importing an existing dbt project
description: Deploy your dbt project with Serverless deployments in Dagster+.
sidebar_position: 100
---

Importing an existing dbt project in Dagster+ allows you to automatically load your dbt models as Dagster assets.

In this guide, we'll demonstrate by using an existing dbt project that doesn't use Dagster.

## Prerequisites

To follow the steps in this guide, you'll need **Dagster+ Organization Admin**, **Admin**, or **Editor** permissions in order to create a code location.

You will also need **an existing dbt project** that contains the following files in the repository root:

- [`dbt_project.yml`](https://docs.getdbt.com/reference/dbt_project.yml)
- [`profiles.yml`](https://docs.getdbt.com/docs/core/connect-data-platform/profiles.yml)

## Step 1: Import your project in Dagster+

In this section, we'll demonstrate how to import an existing project to Dagster+. Our example imports the project from a GitHub repository, but Dagster+ also supports Gitlab.

1. Sign in to your Dagster+ account.

2. Navigate to **Deployment > Code locations**.

3. Click **Add code location**.

4. Click **Import a dbt project**, then **Continue**.

5. At this point, you'll be prompted to select either GitHub or Gitlab. For this guide, we'll select **GitHub**.

6. If prompted, sign into your GitHub account and complete the authorization process for the Dagster+ application. **Note**: The profile or organization you're using to authorize Dagster+ must have read and write access to the repository containing the project. After the authorization is complete, you'll be redirected back to Dagster+.

7. In Dagster+, locate and select the repository containing the project by using the dropdowns. **Note**: dbt projects must have `dbt_project.yml` and `profiles.yml` files in the repository root or an error will display.

8. Click **Continue** to begin the import process.

9. Dagster+ will open a pull request to add a few files to the repository (discussed in the next section), which you will need to review and merge to complete the process.

## Step 2: Review the repository changes

The file structure of the repository will change the first time a project is deployed using Dagster+. For dbt projects, a few things will happen:

- **A [`dagster_cloud.yaml` file](/deployment/code-locations/dagster-cloud-yaml) will be created.** This file defines the project as a Dagster+ code location.
- **A `dagster-plus-deploy.yml` workflow file, used for [CI/CD](/deployment/dagster-plus/deploying-code/ci-cd), will be created in `.github/workflows`.** This file manages the deployments of the repository.
- Dagster+ will create a new Dagster project in the repository using the [`dagster-dbt scaffold`](/integrations/libraries/dbt/reference#scaffolding-a-dagster-project-from-a-dbt-project) command. This will result in a Dagster project that matches the dbt project. For example, a dbt project named `my_dbt_project` will contain a Dagster project in `my_dbt_project/my_dbt_project` after the process completes.

### How the repository will change after the project is deployed for the first time

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
│   │   ├── dagster-plus-deploy.yml
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

## Step 3: Update `profiles.yml`

To ensure your project parses correctly with `dbt parse`, you need to include credentials in your `profiles.yml` file. You can use dummy credentials, since `dbt parse` doesn't connect to your data warehouse.

1. In your dbt project root directory, open the `profiles.yml` file and add the following:
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
2. Save the changes.
3. Commit the changes to the repository.
