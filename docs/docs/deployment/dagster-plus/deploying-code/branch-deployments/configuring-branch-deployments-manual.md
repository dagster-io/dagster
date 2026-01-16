---
title: Configuring branch deployments manually with the dagster-cloud CLI (advanced)
sidebar_label: Configuring branch deployments manually (advanced)
description: Configure branch deployments for a Dagster project in Dagster+ Serverless or Hybrid using the dagster-cloud CLI.
tags: [dagster-plus-feature]
sidebar_position: 7320
---

You can manually execute `dagster-cloud` CLI commands to deploy and manage branch deployments. This is a more advanced option than configuring branch deployments with GitHub or GitLab.

This approach may be a good fit if:

- You don't use GitHub or GitLab for version control
- You use an alternative CI platform
- You want full control over branch deployment configuration

Whenever the state of your branch is updated, Dagster+ expects the following steps to occur:

1. A new image containing your code and requirements is built on the branch.
2. The new image is pushed to a Docker registry accessible to your agent.

The details of how this is accomplished depend on your specific CI/CD solution.

:::note

The following guide assumes the registry URL and image tag are stored in the `LOCATION_REGISTRY_URL` and `IMAGE_TAG` environment variables.

:::

## Prerequisites

To complete the steps in this guide, you will need:

- [Organization Admin permissions](/deployment/dagster-plus/authentication-and-access-control/rbac/user-roles-permissions#agent-tokens) in Dagster+
- To install the [`dagster-cloud` CLI](/api/clis/dagster-cloud-cli/installing-and-configuring) wherever you will be running your CI/CD process

## Step 1: Generate a Dagster+ agent token

The first step is to generate a token for the Dagster+ agent. The Dagster+ agent will use this token to authenticate to the agent API.

1. Sign in to your Dagster+ instance.
2. Click the **user menu (your profile icon) > Organization Settings**.
3. On the **Organization Settings** page, click the **Tokens** tab.
4. Click the **Create agent token** button.
5. After the token has been created, click **Reveal token** and copy the token.

Keep the token somewhere handy, as you'll need it to complete the setup.

## Step 2: Create a branch deployment associated with the branch

Execute the following command within your CI/CD process:

```shell
BRANCH_DEPLOYMENT_NAME=$(
    dagster-cloud branch-deployment create-or-update \
        --organization $ORGANIZATION_NAME \
        --api-token $DAGSTER_CLOUD_API_TOKEN \ # Agent token from step 1
        --git-repo-name $REPOSITORY_NAME \ # Git repository name
        --branch-name $BRANCH_NAME \ # Git branch name
        --commit-hash $COMMIT_SHA \ # Latest commit SHA on the branch
        --timestamp $TIMESTAMP # UTC unixtime timestamp of the latest commit
)
```

One or more additional parameters can optionally be supplied to the `create-or-update` command to enhance the branch deployments UI in Dagster+:

```shell
BRANCH_DEPLOYMENT_NAME=$(
    dagster-cloud branch-deployment create-or-update \
        --organization $ORGANIZATION_NAME \
        --api-token $DAGSTER_CLOUD_API_TOKEN \
        --git-repo-name $REPOSITORY_NAME \
        --branch-name $BRANCH_NAME \
        --commit-hash $COMMIT_SHA \
        --timestamp $TIMESTAMP
        --code-review-url $PR_URL \ # URL to review the given changes, for example
            # Pull Request or Merge Request
        --code-review-id $INPUT_PR \ # Alphanumeric ID for the given set of changes
        --pull-request-status $PR_STATUS \ # A status, one of `OPEN`, `CLOSED`,
            # or `MERGED`, that describes the set of changes
        --commit-message $MESSAGE \ # The message associated with the latest commit
        --author-name $NAME \ # A display name for the latest commit's author
        --author-email $EMAIL \ # An email for the latest commit's author
        --author-avatar-url $AVATAR_URL # An avatar URL for the latest commit's author
        --base-deployment-name $BASE_DEPLOYMENT_NAME # The main deployment that will be compared against. Default is 'prod'
)
```

If the command is being executed from the context of the git repository, you can alternatively pull this metadata from the repository itself:

```shell
BRANCH_DEPLOYMENT_NAME=$(
    dagster-cloud branch-deployment create-or-update \
        --organization $ORGANIZATION_NAME \
        --api-token $DAGSTER_CLOUD_API_TOKEN \
        --git-repo-name $REPOSITORY_NAME \
        --branch-name $BRANCH_NAME \
        --read-git-state # Equivalent to passing --commit-hash, --timestamp
                        # --commit-message, --author-name, --author-email
)
```

## Step 3: Deploy your code to the branch deployment

Execute the following command within your CI/CD process:

```shell
dagster-cloud deployment add-location \
    --organization $ORGANIZATION_NAME \
    --deployment $BRANCH_DEPLOYMENT_NAME \
    --api-token $DAGSTER_CLOUD_API_TOKEN \
    --location-file $LOCATION_FILE \
    --location-name $LOCATION_NAME \
    --image "${LOCATION_REGISTRY_URL}:${IMAGE_TAG}" \
    --commit-hash "${COMMIT_SHA}" \
    --git-url "${GIT_URL}"
```
