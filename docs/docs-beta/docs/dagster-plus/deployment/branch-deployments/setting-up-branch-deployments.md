---
title: "Setting up Branch Deployments"
displayed_sidebar: "dagsterPlus"
sidebar_position: 1
sidebar_label: "Setting up branch deployments"
toc_max_heading_level: 2
---

In this guide, we'll walk you through setting up Branch Deployments for a code location. Once you're finished, any time a PR is created or updated in your repository, it will automatically create or update an associated branch deployment in Dagster+.

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- **Organization Admin** permissions in Dagster+
- The ability to run a new agent in your infrastructure (only if you are using a **Hybrid deployment**)

</details>

## Step 1: Choose a method

Choose a method for setting up branch deployments:

<Tabs groupId="method">
  <TabItem value="github" label="GitHub">

You can set up GitHub to automatically create branch deployments for new PRs, using GitHub Actions.

Using this approach to branch deployments may be a good fit if:

- You use **GitHub** for version control
- You want Dagster to fully automate Branch Deployments

This approach is simplified if you use the [GitHub integration](/todo) to import your project into Dagster+.

  </TabItem>
  <TabItem value="gitlab" label="GitLab">

You can set up GitLab to automatically create branch deployments for new PRs, using GitLab's CI/CD workflow.

Using this approach to branch deployments may be a good fit if:

- You use **GitLab** for version control
- You want Dagster to fully automate Branch Deployments

This approach is simplified if you use the [GitLab integration](/todo) to import your project into Dagster+.

  </TabItem>
  <TabItem value="cli" label="dagster-cloud CLI">

You can manually execute dagster-cloud CLI commands to deploy and manage branch deployments.

Using this approach to branch deployments may be a good fit if:

- You don't use GitHub or GitLab for version control
- You use an alternative CI platform
- You want full control over Branch Deployment configuration

This is a more advanced option than the other methods.

  </TabItem>
</Tabs>

## Step 2: Generate a Dagster+ agent token

In this step, you'll generate a token for the Dagster+ agent. The Dagster+ agent will use this to authenticate to the agent API.

1. Sign in to your Dagster+ instance.
2. Click the **user menu (your icon) > Organization Settings**.
3. In the **Organization Settings** page, click the **Tokens** tab.
4. Click the **Create agent token** button.
5. After the token has been created, click **Reveal token**.

Keep the token somewhere handy - you'll need it to complete the setup.

## Step 3: Create and configure an agent

:::note
If using [Serverless deployment](/dagster-plus/deployment/serverless), this step can be skipped.
:::

While you can use your existing production agent, we recommend creating a dedicated branch deployment agent. This ensures that your production instance isn't negatively impacted by the workload associated with branch deployments.

<Tabs>
  <TabItem value="ecs" label="Amazon ECS">

  1. **Deploy an ECS agent to serve your branch deployments**. Follow the [ECS agent](/dagster-plus/deployment/hybrid/agents/amazon-ecs-new-vpc) setup guide, making sure to set the **Enable Branch Deployments** parameter if using the CloudFormation template. If you are running an existing agent, follow the [upgrade guide](/dagster-plus/deployment/hybrid/agents/amazon-ecs-existing-vpc) to ensure your template is up-to-date. Then, turn on the **Enable Branch Deployments** parameter.

  2. **Create a private [Amazon Elastic Registry (ECR) repository](https://console.aws.amazon.com/ecr/repositories).** Refer to the [AWS ECR documentation](https://docs.aws.amazon.com/AmazonECR/latest/userguide/repository-create.html) for instructions.

  After the repository has been created, navigate back to the list of [ECR repositories](https://console.aws.amazon.com/ecr/repositories).

  In the list, locate the repository and its **URI**:

  ![Show this in the UI](/img/placeholder.svg)

  Keep this around, as you'll need it in a later step.

  3. [**Create an IAM user.**](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html) This user must:

     - Have push access to the ECR repository, and
     - Have programmatic access to AWS using an [access key](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)

     After the user is created, save the **Access key ID** and **Secret access key** values shown on the confirmation page:

     ![Show this in the UI](/img/placeholder.svg)

  </TabItem>
  <TabItem value="docker" label="Docker">

  1. Set up a new Docker agent. Refer to the [Docker agent setup guide](/dagster-plus/deployment/hybrid/agents/docker) for instructions.
  2. After the agent is set up, modify the `dagster.yaml` file as follows:

     - Set the `dagster_cloud_api.branch_deployments` field to `true`
     - Remove any `deployment` field(s)

     For example:

<CodeExample filePath="dagster-plus/deployment/branch-deployments/dagster.yaml" language="yaml" />

  </TabItem>
  <TabItem value="k8s" label="Kubernetes" default>

  1. Set up a new Kubernetes agent. Refer to the [Kubernetes agent setup guide](/dagster-plus/deployment/hybrid/agents/kubernetes) for instructions.

  2. After the agent is set up, modify your Helm values file to include the following:

<CodeExample filePath="dagster-plus/deployment/branch-deployments/helm.yaml" language="yaml" />

  </TabItem>
</Tabs>

## Step 4: Set up branch  deployments

<Tabs groupId="method">
  <TabItem value="github" label="GitHub">

### Step 4.1: Add GitHub CI/CD script to your project
:::note
If you used the GitHub app to configure you're repository, this step isn't required. [Skip ahead to Step 4.5](#step-45-verify-github-action-runs)
:::

Copy the following files to your project, and **replace** all references to `quickstart-etl` with the name of your project:

- [`dagster_cloud.yaml`](https://github.com/dagster-io/dagster-cloud-hybrid-quickstart/blob/main/dagster_cloud.yaml)
- [`.github/workflows/dagster-cloud-deploy.yml`](https://github.com/dagster-io/dagster-cloud-hybrid-quickstart/blob/main/.github/workflows/dagster-cloud-deploy.yml) (for **Hybrid** deployments)
- [`.github/workflows/branch_deployments.yml`](https://github.com/dagster-io/dagster-cloud-serverless-quickstart/blob/main/.github/workflows/branch_deployments.yml) (for **Serverless** deployments)

In the next step, you'll modify these files to work with your Dagster+ setup.

### Step 4.2: Add the agent registry to dagster_cloud.yaml

:::note
If you used the GitHub app to configure you're repository, this step isn't required. [Skip ahead to Step 4.5](#step-45-verify-github-action-runs)
:::

In the `dagster_cloud.yaml` file, replace `build.registry` with the registry used by the [agent you created in Step 2](#step-2-generate-a-dagster-agent-token).

For example:

<CodeExample filePath="dagster-plus/deployment/branch-deployments/dagster_cloud.yaml" language="yaml" />

### Step 4.3: Configure GitHub Action secrets

:::note
If you used the GitHub app to configure you're repository, this step isn't required. [Skip ahead to Step 4.5](#step-45-verify-github-action-runs)
:::

1. In your GitHub repository, click the **Settings** tab.
2. In the **Security** section of the sidebar, click **Secrets > Actions**.
3. Click **New repository secret**.
4. In the **Name** field, enter the name of the secret. For example, `DAGSTER_CLOUD_API_TOKEN`
5. In the **Value** field, paste the value of the secret.
6. Click **Add secret**.

Repeat steps 3-6 for each of the secrets required for the registry used by the agent you created in Step 2. See below for more details:

<Tabs>

<TabItem value="docker" label="Docker">

- `DAGSTER_CLOUD_API_TOKEN` - The Dagster+ agent token you created in [Step 2](#step-2-generate-a-dagster-agent-token)
- `DAGSTER_CLOUD_URL` - Your Dagster+ base URL (`https://my_org.dagster.cloud`)
- `DOCKERHUB_USERNAME` - Your DockerHub username
- `DOCKERHUB_TOKEN` - A DockerHub [access token](https://docs.docker.com/docker-hub/access-tokens/#create-an-access-token)

</TabItem>

<TabItem value="ecr" label="Amazon ECR">

- `DAGSTER_CLOUD_API_TOKEN` - The Dagster+ agent token you created in [Step 2](#step-2-generate-a-dagster-agent-token)
- `DAGSTER_CLOUD_URL` - Your Dagster+ base URL (`https://my_org.dagster.cloud`)
- `AWS_ACCESS_KEY` - The **Access key ID** of the AWS IAM user you created in [Step 3](#step-3-create-and-configure-an-agent)
- `AWS_SECRET_ACCESS_KEY` - The **Secret access key** of the AWS IAM user you created in [Step 3](#step-3-create-and-configure-an-agent)
- `AWS_REGION` - The AWS region where your ECR registry is located

</TabItem>

<TabItem value="gcr" label="Google Container Registry (GCR)">

- `DAGSTER_CLOUD_API_TOKEN` - The Dagster+ agent token you created in [Step 2](#step-2-generate-a-dagster-agent-token)
- `DAGSTER_CLOUD_URL` - Your Dagster+ base URL (`https://my_org.dagster.cloud`)
- `GCR_JSON_KEY` - Your GCR JSON credentials

</TabItem>

</Tabs>

### Step 4.4: Configure GitHub Action

:::note
If you used the GitHub app to configure you're repository, this step isn't required. [Skip ahead to Step 4.5](#step-45-verify-github-action-runs)
:::

In this step, you'll update the GitHub workflow files in your repository to set up Docker registry access.

In the `.github/workflows/dagster-cloud-deploy.yml` file, un-comment the `step` associated with your registry. For example, for an Amazon ECR registry, you'd un-comment the following portion of the workflow file:

```yaml
jobs:
  dagster-cloud-deploy:
    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_REGION }}
```

Save and commit the file to your repository.

### Step 4.5: Verify GitHub action runs

The last step is to verify that the GitHub Action runs successfully.

1. In the repository, click the **Actions** tab.
2. In the list of workflows, locate the latest branch deployment run. For example:

![Show this in the UI](/img/placeholder.svg)

  </TabItem>
  <TabItem value="gitlab" label="GitLab">

### Step 4.1: add GitLab CI/CD script to your project

:::note
If you used the GitLab app to configure you're repository, this step isn't required. [Skip ahead to Step 4.5](#step-45-verify-gitlab-pipeline-runs)
:::

Copy the following files to your project, and **replace** all references to `quickstart-etl` with the name of your project:

- [`dagster_cloud.yaml`](https://github.com/dagster-io/dagster-cloud-hybrid-quickstart/blob/main/dagster_cloud.yaml)
- [`.gitlab-ci.yml`](https://github.com/dagster-io/dagster-cloud-action/blob/main/gitlab/hybrid-ci.yml) (for **Hybrid** deployments)
- [`.gitlab-ci.yml`](https://github.com/dagster-io/dagster-cloud-action/blob/main/gitlab/serverless-ci.yml) (for **Serverless** deployments)

In the next step, you'll modify these files to work with your Dagster+ setup.

### Step 4.2: add the agent registry to dagster_cloud.yaml

:::note
If you used the GitLab app to configure you're repository, this step isn't required. [Skip ahead to Step 4.5](#step-45-verify-gitlab-pipeline-runs)
:::


In the `dagster_cloud.yaml` file, replace `build.registry` with the registry used by the [agent you created in Step 2](#step-2-generate-a-dagster-agent-token).

For example:

<CodeExample filePath="dagster-plus/deployment/branch-deployments/dagster_cloud.yaml" language="yaml" />

### Step 4.3: configure GitLab CI/CD variables

:::note
If you used the GitLab app to configure you're repository, this step isn't required. [Skip ahead to Step 4.5](#step-45-verify-gitlab-pipeline-runs)
:::


1. In your project, click the **Settings** tab.
2. In the **CI/CD** section of the sidebar, expand **Variables**.
3. Click **Add variable**.
4. In the **Key** field, enter the name of the variable. For example, `DAGSTER_CLOUD_API_TOKEN`
5. In the **Value** field, paste the value of the variable.
6. Click **Add variable**.

Repeat steps 3-6 for each of the secrets required for your registry type:

<Tabs>

<TabItem value="gitlab" label="GitLab Container Registry">

- `DAGSTER_CLOUD_API_TOKEN` - The Dagster+ agent token you created in [Step 2](#step-2-generate-a-dagster-agent-token)
- `DAGSTER_CLOUD_URL` - Your Dagster+ base URL (`https://my_org.dagster.cloud`)

</TabItem>

<TabItem value="docker" label="Docker">

- `DAGSTER_CLOUD_API_TOKEN` - The Dagster+ agent token you created in [Step 2](#step-2-generate-a-dagster-agent-token)
- `DAGSTER_CLOUD_URL` - Your Dagster+ base URL (`https://my_org.dagster.cloud`)
- `DOCKERHUB_USERNAME` - Your DockerHub username
- `DOCKERHUB_TOKEN` - A DockerHub [access token](https://docs.docker.com/docker-hub/access-tokens/#create-an-access-token)

</TabItem>

<TabItem value="ecr" label="Amazon ECR">

- `DAGSTER_CLOUD_API_TOKEN` - The Dagster+ agent token you created in [Step 2](#step-2-generate-a-dagster-agent-token)
- `DAGSTER_CLOUD_URL` - Your Dagster+ base URL (`https://my_org.dagster.cloud`)
- `AWS_ACCESS_KEY` - The **Access key ID** of the AWS IAM user you created in [Step 3](#step-3-create-and-configure-an-agent)
- `AWS_SECRET_ACCESS_KEY` - The **Secret access key** of the AWS IAM user you created in [Step 3](#step-3-create-and-configure-an-agent)
- `AWS_REGION` - The AWS region where your ECR registry is located

</TabItem>

<TabItem value="gcr" label="Google Container Registry (GCR)">

- `DAGSTER_CLOUD_API_TOKEN` - The Dagster+ agent token you created in [Step 2](#step-2-generate-a-dagster-agent-token)
- `DAGSTER_CLOUD_URL` - Your Dagster+ base URL (`https://my_org.dagster.cloud`)
- `GCR_JSON_KEY` - Your GCR JSON credentials

</TabItem>

</Tabs>

### Step 4.4: configure GitLab CI/CD script

:::note
If you used the GitLab app to configure you're repository, this step isn't required. [Skip ahead to Step 4.5](#step-45-verify-gitlab-pipeline-runs)
:::

In this step, you'll update the GitLab CI/CD config to set up Docker registry access.

In the `.gitlab-ci.yml` file, un-comment the `step` associated with your registry. For example, for the GitLab container registry, you'd un-comment the following portion of the `.gitlab-ci.yml` file:

```yaml
build-image:
  ...
  before_script:
    # For GitLab Container Registry
    - echo $CI_JOB_TOKEN | docker login --username $CI_REGISTRY_USER --password-stdin $REGISTRY_URL
```

Save and commit the files to the project.

### Step 4.5: verify GitLab pipeline runs

The last step is to verify that the GitLab pipeline runs successfully.

1. On the project page, click the **CI/CD** tab.
2. In the list of pipelines, locate the latest branch deployment run. For example:

![Show this in the UI](/img/placeholder.svg)

  </TabItem>
  <TabItem value="cli" label="dagster-cloud CLI">

Whenever the state of your branch is updated, Dagster+ expects the following steps to occur:

1. A new image containing your code and requirements is built on the branch. Refer to [Managing code locations](/todo) to learn more.

2. The new image is pushed to a Docker registry accessible to your agent.

The details of how this is accomplished depend on your specific CI/CD solution.

:::note

The following examples assume the registry URL and image tag are stored in the `LOCATION_REGISTRY_URL` and `IMAGE_TAG` environment variables.

:::

### Step 4.1 Create a branch deployment associated with the branch

Execute the following command within your CI/CD process:

   ```shell
   BRANCH_DEPLOYMENT_NAME=$(
       dagster-cloud branch-deployment create-or-update \
           --organization $ORGANIZATION_NAME \
           --api-token $DAGSTER_CLOUD_API_TOKEN \ # Agent token from Step 1
           --git-repo-name $REPOSITORY_NAME \ # Git repository name
           --branch-name $BRANCH_NAME \ # Git branch name
           --commit-hash $COMMIT_SHA \ # Latest commit SHA on the branch
           --timestamp $TIMESTAMP # UTC unixtime timestamp of the latest commit
   )
   ```

One or more additional parameters can optionally be supplied to the `create-or-update` command to enhance the Branch Deployments UI in Dagster+:

```shell
BRANCH_DEPLOYMENT_NAME=$(
    dagster-cloud branch-deployment create-or-update \
        --organization $ORGANIZATION_NAME \
        --api-token $DAGSTER_CLOUD_API_TOKEN \
        --git-repo-name $REPOSITORY_NAME \
        --branch-name $BRANCH_NAME \
        --commit-hash $COMMIT_SHA \
        --timestamp $TIMESTAMP
        --code-review-url $PR_URL \ # URL to review the given changes, e.g.
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

### Step 4.2 Deploy your code to the branch deployment

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

  </TabItem>
</Tabs>

## Next steps

- Learn more about [Branch Deployments](/dagster-plus/deployment/branch-deployments)
- Learn how to [Track changes on a Branch Deployment](/dagster-plus/deployment/branch-deployments/change-tracking)
