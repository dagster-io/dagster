---
description: Configure branch deployments for a code location in Dagster+ using GitHub, GitLab, or the dagster-cloud CLI.
sidebar_position: 7310
title: Setting up branch deployments
tags: [dagster-plus-feature]
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';
import BranchDeploymentCli from '@site/docs/partials/\_BranchDeploymentCli.md';
import UpdateBuildYaml from '@site/docs/partials/\_UpdateBuildYaml.md';

<DagsterPlus />

This guide covers setting up branch deployments for a [code location](/guides/build/projects) using GitHub, GitLab, or an alternative CI platform using the dagster-cloud CLI. Once you've set up branch deployments, any time you create or update a pull request (or merge request) in the repository for your code location, it will automatically create or update an associated branch deployment in Dagster+.

:::info

Output created from a branch deployment -- such as a database, table, etc. -- won't be automatically removed from storage once a branch is merged or closed. For more information on handling this output, see the [best practices section](#best-practices).

:::

## Prerequisites

To follow the steps in this guide, you'll need:

- [**Organization Admin** permissions](/deployment/dagster-plus/authentication-and-access-control/rbac/user-roles-permissions) in Dagster+.
- **If using a Hybrid deployment:** The ability to run a new agent in your infrastructure.

## Step 1: Generate a Dagster+ agent token

The first step is to generate a token for the Dagster+ agent. The Dagster+ agent will use this token to authenticate to the agent API.

1. Sign in to your Dagster+ instance.
2. Click the **user menu (your profile icon) > Organization Settings**.
3. On the **Organization Settings** page, click the **Tokens** tab.
4. Click the **Create agent token** button.
5. After the token has been created, click **Reveal token** and copy the token.

Keep the token somewhere handy, as you'll need it to complete the setup.

## Step 2: Create and configure a branch deployment agent (Hybrid only)

:::info

If you are using [Dagster+ Serverless](/deployment/dagster-plus/serverless), you can skip this step.

:::

While you can use your existing production agent for branch deployment on Dagster+ Hybrid, we recommend creating a dedicated branch deployment agent. This ensures that your production instance isn't negatively impacted by the workload associated with branch deployments.

<Tabs>
  <TabItem value="ecs" label="Amazon ECS">

1. **Deploy an ECS agent to serve your branch deployments**. Follow the [ECS agent](/deployment/dagster-plus/hybrid/amazon-ecs/new-vpc) setup guide, making sure to set the **Enable branch deployments** parameter if using the CloudFormation template. If you are running an existing agent, follow the [upgrade guide](/deployment/dagster-plus/hybrid/amazon-ecs/existing-vpc) to ensure your template is up-to-date. Then, turn on the **Enable branch deployments** parameter.

2. **Create a private [Amazon Elastic Registry (ECR) repository](https://console.aws.amazon.com/ecr/repositories).** Refer to the [AWS ECR documentation](https://docs.aws.amazon.com/AmazonECR/latest/userguide/repository-create.html) for instructions.

After the repository has been created, navigate back to the list of [ECR repositories](https://console.aws.amazon.com/ecr/repositories).

In the list, locate the repository and its **URI**:

![Show this in the UI](/images/dagster-plus/features/branch-deployments/aws-ecr-uri.png)

Keep this around, as you'll need it in a later step.

3. [**Create an IAM user.**](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html) This user must:

   - Have push access to the ECR repository, and
   - Have programmatic access to AWS using an [access key](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)

   After the user is created, save the **Access key ID** and **Secret access key** values shown on the confirmation page:

   ![Show this in the UI](/images/dagster-plus/features/branch-deployments/aws-iam-user-keys.png)

  </TabItem>
  <TabItem value="docker" label="Docker">

1. Set up a new Docker agent. For instructions, see the [Docker agent setup guide](/deployment/dagster-plus/hybrid/docker).
2. After the agent is set up, modify the `dagster.yaml` file as follows:

   - Set the `dagster_cloud_api.branch_deployments` field to `true`
   - Remove any `deployment` field(s)

   For example:

<CodeExample
  path="docs_snippets/docs_snippets/dagster-plus/deployment/branch-deployments/dagster.yaml"
  language="yaml"
  title="dagster.yaml"
/>

  </TabItem>
  <TabItem value="k8s" label="Kubernetes" default>

1. Set up a new Kubernetes agent. For instructions, see the [Kubernetes agent setup guide](/deployment/dagster-plus/hybrid/kubernetes).

2. After the agent is set up, modify your Helm values file to include the following:

<CodeExample path="docs_snippets/docs_snippets/dagster-plus/deployment/branch-deployments/helm.yaml" language="yaml" />

  </TabItem>
</Tabs>

## Step 3: Automate branch deployment creation

### Dagster+ Serverless

<Tabs groupId="method">
  <TabItem value="github" label="GitHub">

If you use the GitHub app to import your repo to Dagster+, the app will create the GitHub Actions workflow file needed to automatically create branch deployments for new pull requests.

After using the GitHub app to import your repo to Dagster+ Serverless, we recommend verifying that the GitHub Action runs successfully.

1. In the GitHub repository, click the **Actions** tab.
2. In the list of workflows, locate the latest branch deployment run. For example:

![Show this in the UI](/images/dagster-plus/features/branch-deployments/github-verify-run.png)

  </TabItem>
  <TabItem value="gitlab" label="GitLab">

If you use the GitLab app to import your repo to Dagster+, the app will create the GitLab CI/CD configuration file needed to automatically create branch deployments for new pull requests.

After using the GitLab app to import your repo to Dagster+ Serverless, we recommend verifying that the GitLab pipeline runs successfully.

1. On the project page, click the **CI/CD** tab.
2. In the list of pipelines, locate the latest branch deployment run. For example:

![Show this in the UI](/images/dagster-plus/features/branch-deployments/gitlab-verify-run.png)

  </TabItem>
  <TabItem value="cli" label="dagster-cloud CLI">

  <BranchDeploymentCli />

  </TabItem>
</Tabs>

### Dagster+ Hybrid

<Tabs groupId="method">
  <TabItem value="github" label="GitHub">

You can set up GitHub to automatically create branch deployments for new pull requests, using GitHub Actions.

This approach may be a good fit if:

- You use **GitHub** for version control
- You want Dagster to fully automate branch deployments

**Step 3.1: Add GitHub CI/CD script to your project**

To set up continuous integration using GitHub Actions, you can use the [`dg plus deploy configure CLI command`](/api/clis/dg-cli/dg-plus#deploy) to generate the GitHub workflow YAML file:

```shell
dg plus deploy configure --git-provider github
```

**Step 3.2: Add the agent registry to build.yaml**

<UpdateBuildYaml />

**Step 3.3: Configure GitHub Action secrets**

1. In your GitHub repository, click the **Settings** tab.
2. In the **Security** section of the sidebar, click **Secrets > Actions**.
3. Click **New repository secret**.
4. In the **Name** field, enter the name of the secret. For example, `DAGSTER_CLOUD_API_TOKEN`
5. In the **Value** field, paste the value of the secret.
6. Click **Add secret**.

Repeat steps 3-6 for each of the secrets required for the registry used by the agent you created in step 1. See below for more details:

<Tabs>

<TabItem value="docker" label="Docker">

- `DAGSTER_CLOUD_API_TOKEN` - The Dagster+ agent token you created in step 1
- `DAGSTER_CLOUD_URL` - Your Dagster+ base URL (`https://my_org.dagster.cloud`)
- `DOCKERHUB_USERNAME` - Your DockerHub username
- `DOCKERHUB_TOKEN` - A DockerHub [access token](https://docs.docker.com/docker-hub/access-tokens/#create-an-access-token)

</TabItem>

<TabItem value="ecr" label="Amazon ECR">

- `DAGSTER_CLOUD_API_TOKEN` - The Dagster+ agent token you created in step 1
- `DAGSTER_CLOUD_URL` - Your Dagster+ base URL (`https://my_org.dagster.cloud`)
- `AWS_ACCESS_KEY` - The **Access key ID** of the AWS IAM user you created in step 3
- `AWS_SECRET_ACCESS_KEY` - The **Secret access key** of the AWS IAM user you created in step 3
- `AWS_REGION` - The AWS region where your ECR registry is located

</TabItem>

<TabItem value="gcr" label="Google Container Registry (GCR)">

- `DAGSTER_CLOUD_API_TOKEN` - The Dagster+ agent token you created in step 1
- `DAGSTER_CLOUD_URL` - Your Dagster+ base URL (`https://my_org.dagster.cloud`)
- `GCR_JSON_KEY` - Your GCR JSON credentials

</TabItem>

</Tabs>

**Step 3.4: Configure GitHub Action**

In this step, you'll update the GitHub workflow file in your repository to set up Docker registry access.

In the `.github/workflows/dagster-cloud-deploy.yml` file, un-comment the `step` associated with your registry. For example, for an Amazon ECR registry, you'd un-comment the following portion of the workflow file:

```yaml
# dagster-cloud-deploy.yml
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

**Step 3.5: Verify GitHub action runs**

The last step is to verify that the GitHub Action runs successfully.

1. In the repository, click the **Actions** tab.
2. In the list of workflows, locate the latest branch deployment run. For example:

![Show this in the UI](/images/dagster-plus/features/branch-deployments/github-verify-run.png)

  </TabItem>
  <TabItem value="gitlab" label="GitLab">

You can set up GitLab to automatically create branch deployments for new merge request, using GitLab's CI/CD workflow.

**Step 3.1: Add GitLab CI/CD script to your project**

TK - scaffold GitLab CI/CD script

**Step 3.2: Add the agent registry to build.yaml**

<UpdateBuildYaml />

**Step 3.3: Configure GitLab CI/CD variables**

1. In your project, click the **Settings** tab.
2. In the **CI/CD** section of the sidebar, expand **Variables**.
3. Click **Add variable**.
4. In the **Key** field, enter the name of the variable. For example, `DAGSTER_CLOUD_API_TOKEN`
5. In the **Value** field, paste the value of the variable.
6. Click **Add variable**.

Repeat steps 3-6 for each of the secrets required for your registry type:

<Tabs>

<TabItem value="gitlab" label="GitLab Container Registry">

- `DAGSTER_CLOUD_API_TOKEN` - The Dagster+ agent token you created in step 2
- `DAGSTER_CLOUD_URL` - Your Dagster+ base URL (`https://my_org.dagster.cloud`)

</TabItem>

<TabItem value="docker" label="Docker">

- `DAGSTER_CLOUD_API_TOKEN` - The Dagster+ agent token you created in step 2
- `DAGSTER_CLOUD_URL` - Your Dagster+ base URL (`https://my_org.dagster.cloud`)
- `DOCKERHUB_USERNAME` - Your DockerHub username
- `DOCKERHUB_TOKEN` - A DockerHub [access token](https://docs.docker.com/docker-hub/access-tokens/#create-an-access-token)

</TabItem>

<TabItem value="ecr" label="Amazon ECR">

- `DAGSTER_CLOUD_API_TOKEN` - The Dagster+ agent token you created in step 2
- `DAGSTER_CLOUD_URL` - Your Dagster+ base URL (`https://my_org.dagster.cloud`)
- `AWS_ACCESS_KEY` - The **Access key ID** of the AWS IAM user you created in step 3
- `AWS_SECRET_ACCESS_KEY` - The **Secret access key** of the AWS IAM user you created in step 3
- `AWS_REGION` - The AWS region where your ECR registry is located

</TabItem>

<TabItem value="gcr" label="Google Container Registry (GCR)">

- `DAGSTER_CLOUD_API_TOKEN` - The Dagster+ agent token you created in step 2
- `DAGSTER_CLOUD_URL` - Your Dagster+ base URL (`https://my_org.dagster.cloud`)
- `GCR_JSON_KEY` - Your GCR JSON credentials

</TabItem>

</Tabs>

**Step 3.4: Configure GitLab CI/CD script**

In this step, you'll update the GitLab CI/CD configuration file to set up Docker registry access.

In the `.gitlab-ci.yml` file, un-comment the `step` associated with your registry. For example, for the GitLab container registry, you'd un-comment the following portion of the `.gitlab-ci.yml` file:

```yaml
build-image:
  ...
  before_script:
    # For GitLab Container Registry
    - echo $CI_JOB_TOKEN | docker login --username $CI_REGISTRY_USER --password-stdin $REGISTRY_URL
```

Save and commit the files to the project.

**Step 3.5: Verify GitLab pipeline runs**

The last step is to verify that the GitLab pipeline runs successfully.

1. On the project page, click the **CI/CD** tab.
2. In the list of pipelines, locate the latest branch deployment run. For example:

![Show this in the UI](/images/dagster-plus/features/branch-deployments/gitlab-verify-run.png)

  </TabItem>
  <TabItem value="cli" label="dagster-cloud CLI">

  <BranchDeploymentCli />

  </TabItem>
</Tabs>

## Accessing branch deployments

Once configured, branch deployments can be accessed:

<Tabs>
  <TabItem value="From a GitHub pull request">

Every pull request in the repository contains a **View in Cloud** link, which will open a branch deployment - or a preview of the changes - in Dagster+.

![View in Cloud preview link highlighted in a GitHub pull request](/images/dagster-plus/features/branch-deployments/github-cloud-preview-link.png)

  </TabItem>
  <TabItem value="In Dagster+">

:::note

To access a branch deployment in Dagster+, you need permissions that grant you [access to branch deployments](/deployment/dagster-plus/authentication-and-access-control/rbac/user-roles-permissions#user-permissions-reference) and the code location associated with the branch deployment.

:::

You can also access branch deployments directly in Dagster+ from the **deployment switcher**:

![Highlighted branch deployment in the Dagster+ deployment switcher](/images/dagster-plus/full-deployments/deployment-switcher.png)

  </TabItem>
</Tabs>

## Changing the base deployment

The base deployment has two main purposes:

- It sets which [full deployment](/deployment/dagster-plus/deploying-code/full-deployments) is used to propagate Dagster+ managed environment variables that are scoped for branch deployments.
- It is used in the UI to [track changes](/deployment/dagster-plus/deploying-code/branch-deployments/change-tracking) to the branch deployment from its parent full deployment.

The default base for branch deployments is `prod`. To configure a different full deployment as the base, create a branch deployment using the dagster-cloud CLI (see step 3.1 above) and specify the deployment with the optional `--base-deployment-name` parameter.

## Best practices

To ensure the best experience when using branch deployments, we recommend:

- **Configuring jobs based on environment**. Dagster automatically sets [environment variables](/deployment/dagster-plus/management/environment-variables/built-in) containing deployment metadata, allowing you to parameterize jobs based on the executing environment. Use these variables in your jobs to configure things like connection credentials, databases, and so on. This practice will allow you to use branch deployments without impacting production data.
- **Creating jobs to automate output cleanup.** As branch deployments don't automatically remove the output they create, you may want to create an additional Dagster job to perform the cleanup.

## Next steps

- Learn more about [branch deployments](/deployment/dagster-plus/deploying-code/branch-deployments)
- Learn how to [track changes on a branch deployment](/deployment/dagster-plus/deploying-code/branch-deployments/change-tracking)
