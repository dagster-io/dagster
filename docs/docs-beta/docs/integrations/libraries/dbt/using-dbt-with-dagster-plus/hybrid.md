---
title: "Using dbt with Hybrid deployments in Dagster+"
description: Deploy your dbt & Dagster project with Hybrid deployments in Dagster+.
---

If you have a Hybrid deployment, you must make the dbt project accessible to the Dagster code executed by your agent.

- When using Amazon Elastic Container Service (ECS), Kubernetes, or Docker agent, you must include the dbt project in the Docker Image containing your Dagster code.
- When using a local agent, you must make your dbt project accessible to your Dagster code on the same machine as your agent.

For the dbt project to be used by Dagster, it must contain an up-to-date [manifest file](https://docs.getdbt.com/reference/artifacts/manifest-json) and [project dependencies](https://docs.getdbt.com/docs/collaborate/govern/project-dependencies).

In this guide, we'll demonstrate how to prepare your dbt project for use in your Hybrid deployment in Dagster+.

## Prerequisites

To follow the steps in this guide, you'll need **an existing dbt project** that contains the following files in the repository root:

- [`dbt_project.yml`](https://docs.getdbt.com/reference/dbt_project.yml)
- [`profiles.yml`](https://docs.getdbt.com/docs/core/connect-data-platform/profiles.yml)

## Using an Amazon Elastic Container Service (ECS), Kubernetes, or Docker agent

If you are using an Amazon Elastic Container Service (ECS), Kubernetes, or Docker agent for your Hybrid deployments in Dagster+, your Dagster code must be packaged in a Docker image and pushed to a registry your agent can access. In this scenario, to use a dbt project with Dagster, you'll need to include it with your code in the Docker image.

Before including the dbt project in the Docker image, you'll need to make sure it contains an up-to-date [manifest file](https://docs.getdbt.com/reference/artifacts/manifest-json) and [project dependencies](https://docs.getdbt.com/docs/collaborate/govern/project-dependencies).

This can be done by running the [`dagster-dbt project prepare-and-package`](/api/python-api/libraries/dagster-dbt#prepare-and-package) command. In the workflow building and pushing your Docker image, make sure this command runs before building your Docker image to ensure all required dbt files are included. Note that this command runs `dbt deps` and `dbt parse` to create your manifest file.

### Using CI/CD files

If you are using [CI/CD files](/dagster-plus/features/ci-cd/ci-cd-file-reference) in a Git repository to build and push your Docker image, you'll need to add a few steps to allow the dbt project to deploy successfully.

Our example updates the CI/CD files of a project from a GitHub repository, but this could be achieved in other platform like GitLab.

1. In your Dagster project, locate the `.github/workflows` directory.

2. Open the `deploy.yml` file.

3. Locate the step in which which you build and push your docker image.

4. Before this step, add the following:

   ```yaml
   - name: Prepare DBT project for deployment
     run: |
       python -m pip install pip --upgrade
       pip install . --upgrade --upgrade-strategy eager                                            ## Install the Python dependencies from the setup.py file, ex: dbt-core and dbt-duckdb
       dagster-dbt project prepare-and-package --file <DAGSTER_PROJECT_FOLDER>/project.py          ## Replace with the project.py location in the Dagster project folder
     shell: bash
   ```

   When you add this step, you'll need to:

   - **Add any [adapters](https://docs.getdbt.com/docs/connect-adapters) and libraries used by dbt to your `setup.py` file**.
   - **Add the location of your Dagster project directory** to the `dagster-dbt project prepare-and-package` command.

5. Save the changes.

6. Open the `branch_deployments.yml` file and repeat steps 3 - 5.

7. Commit the changes to the repository.

Once the new step is pushed to the remote, your workflow will be updated to prepare your dbt project before building and pushing your docker image.

## Using a local agent

When using a local agent for your Hybrid deployments in Dagster+, your Dagster code and dbt project must be in a Python environment that can be accessed on the same machine as your agent.

When updating the dbt project, it is important to refresh the [manifest file](https://docs.getdbt.com/reference/artifacts/manifest-json) and [project dependencies](https://docs.getdbt.com/docs/collaborate/govern/project-dependencies) to ensure that they are up-to-date when used with your Dagster code. This can be done by running the [`dagster-dbt project prepare-and-package`](/api/python-api/libraries/dagster-dbt#prepare-and-package) command. Note that this command runs `dbt deps` and `dbt parse` to refresh your manifest file.
