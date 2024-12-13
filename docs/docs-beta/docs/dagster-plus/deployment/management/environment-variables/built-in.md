---
title: 'Built-in environment variables'
sidebar_position: 100
sidebar_label: 'Built-in variables'
---

[Dagster+](/todo) provides a set of built-in, automatically populated environment variables, such as the name of a deployment or details about a branch deployment commit, that can be used to modify behavior based on environment.

### All deployment variables

The following variables are available in every deployment of your Dagster+ instance.

| Key                                  | Value                                                                |
| ------------------------------------ | -------------------------------------------------------------------- |
| `DAGSTER_CLOUD_DEPLOYMENT_NAME`      | The name of the Dagster+ deployment. <br/><br/> **Example:** `prod`. |
| `DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT` | `1` if the deployment is a branch deployment.                        |

### Branch deployment variables

The following environment variables are available only in a [branch deployment](/todo).

For every commit made to a branch, the following environment variables are available:

| Key                                 | Value                                                                                                                     |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `DAGSTER_CLOUD_GIT_SHA`             | The SHA of the commit.                                                                                                    |
| `DAGSTER_CLOUD_GIT_TIMESTAMP`       | The Unix timestamp in seconds when the commit occurred. <br/><br/> **Example:** `1724871941`                              |
| `DAGSTER_CLOUD_GIT_AUTHOR_EMAIL`    | The email of the git user who authored the commit.                                                                        |
| `DAGSTER_CLOUD_GIT_AUTHOR_NAME`     | The name of the git user who authored the commit.                                                                         |
| `DAGSTER_CLOUD_GIT_MESSAGE`         | The message associated with the commit.                                                                                   |
| `DAGSTER_CLOUD_GIT_BRANCH`          | The name of the branch associated with the commit.                                                                        |
| `DAGSTER_CLOUD_GIT_REPO`            | The name of the repository associated with the commit.                                                                    |
| `DAGSTER_CLOUD_PULL_REQUEST_ID`     | The ID of the pull request associated with the commit.                                                                    |
| `DAGSTER_CLOUD_PULL_REQUEST_STATUS` | The status of the pull request at the time of the commit. <br/><br/> **Possible values:** `OPEN`, `CLOSED`, and `MERGED`. |
