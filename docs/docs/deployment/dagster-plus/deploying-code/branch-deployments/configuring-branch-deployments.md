---
description: Configure branch deployments for a Dagster project in Dagster+ Serverless or Hybrid using GitHub or GitLab.
sidebar_position: 7310
sidebar_label: Configuring branch deployments
title: Configuring branch deployments with GitHub or GitLab
tags: [dagster-plus-feature]
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';
import UpdateBuildYaml from '@site/docs/partials/\_UpdateBuildYaml.md';

<DagsterPlus />

This guide covers setting up branch deployments for a [Dagster project](/guides/build/projects) in Dagster+ Serverless or Hybrid with GitHub or GitLab. Once you've set up branch deployments, any time you create or update a pull request (or merge request) in your project repository, an associated branch deployment will automatically be created or updated in Dagster+.

:::note

Output created from a branch deployment -- such as a database, table, etc. -- won't be automatically removed from storage once a branch is merged or closed. For more information on handling this output, see the [best practices section](#best-practices).

:::

## Dagster+ Serverless

Branch deployments are automatically configured for Serverless deployments when you configure CI/CD. For more information, see the [CI/CD configuration guide](/deployment/dagster-plus/deploying-code/configuring-ci-cd).

## Dagster+ Hybrid

:::info Prerequisites

To follow the steps in this section, you'll need:

- [Organization Admin permissions](/deployment/dagster-plus/authentication-and-access-control/rbac/user-roles-permissions) in Dagster+.
- The ability to run a new agent in your infrastructure.

:::

### Step 1: Configure CI/CD

Follow the [CI/CD configuration guide](/deployment/dagster-plus/deploying-code/configuring-ci-cd) to set up CI/CD for Dagster+ Hybrid with your preferred Git provider.

### Step 2: Create a branch deployment agent \{#step-2}

While you can use your existing production agent for branch deployments on Dagster+ Hybrid, we recommend creating a dedicated branch deployment agent. This ensures that your production instance isn't negatively impacted by the workload associated with branch deployments.

<Tabs>
<TabItem value="ecs" label="Amazon ECS">

1. **Deploy an ECS agent to serve your branch deployments.**

   - To create a new agent, follow the [ECS agent](/deployment/dagster-plus/hybrid/amazon-ecs/new-vpc) setup guide, making sure to set the **Enable branch deployments** parameter if using the CloudFormation template.
   - To upgrade an existing agent, follow the [upgrade guide](/deployment/dagster-plus/hybrid/amazon-ecs/existing-vpc) to ensure your template is up-to-date. Then, turn on the **Enable branch deployments** parameter.

2. Create a private [Amazon Elastic Registry (ECR) repository](https://console.aws.amazon.com/ecr/repositories). For instructions, see the [AWS ECR documentation](https://docs.aws.amazon.com/AmazonECR/latest/userguide/repository-create.html).

3. After you have created a new ECR repository, navigate back to the list of [ECR repositories](https://console.aws.amazon.com/ecr/repositories). In the list, locate the repository and its **URI**. Copy the URI to a separate text file, as you'll need it in a later step.

![Show this in the UI](/images/dagster-plus/features/branch-deployments/aws-ecr-uri.png)

4. [Create an IAM user.](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html) This user must:

   - Have push access to the ECR repository, and
   - Have programmatic access to AWS using an [access key](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)

5. After the user is created, save the **Access key ID** and **Secret access key** values shown on the confirmation page:

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

### Step 3: Update `build.yaml` with the branch deployment agent

<UpdateBuildYaml />

### Step 4: Add secrets to your Git provider

<Tabs>
<TabItem value="github" label="GitHub">

1. In your GitHub repository, click the **Settings** tab.
2. In the **Security** section of the sidebar, click **Secrets > Actions**.
3. Click **New repository secret**.
4. In the **Name** field, enter the name of the secret. For example, `DAGSTER_CLOUD_URL`
5. In the **Value** field, paste the value of the secret.
6. Click **Add secret**.

Repeat steps 3-6 for each of the secrets required for the registry used by the agent you created in step 1. See below for more details:

<Tabs>
<TabItem value="docker" label="Docker">

- `DAGSTER_CLOUD_URL` - Your Dagster+ base URL (`https://my_org.dagster.cloud`)
- `DOCKERHUB_USERNAME` - Your DockerHub username
- `DOCKERHUB_TOKEN` - A DockerHub [access token](https://docs.docker.com/docker-hub/access-tokens/#create-an-access-token)

</TabItem>
<TabItem value="ecr" label="Amazon ECR">

- `DAGSTER_CLOUD_URL` - Your Dagster+ base URL (`https://my_org.dagster.cloud`)
- `AWS_ACCESS_KEY` - The **Access key ID** of the AWS IAM user you created in step 3
- `AWS_SECRET_ACCESS_KEY` - The **Secret access key** of the AWS IAM user you created in step 3
- `AWS_REGION` - The AWS region where your ECR registry is located

</TabItem>
<TabItem value="gcr" label="Google Container Registry (GCR)">

- `DAGSTER_CLOUD_URL` - Your Dagster+ base URL (`https://my_org.dagster.cloud`)
- `GCR_JSON_KEY` - Your GCR JSON credentials

</TabItem>
</Tabs>
</TabItem>
<TabItem value="gitlab" label="GitLab">

1. In your GitLab repository, click **Settings** > **CI/CD**.
2. On the settings page, click **Variables**.
3. Under **Project variables**, click **Add variable**.
4. In the **Key** field, enter the name of the secret. For example, `DAGSTER_CLOUD_URL`.
5. In the **Value** field, paste the value of the secret.
6. Update the type, environments, visibility, flags, and description fields as needed.
7. Click **Add variable**.

Repeat steps 3-6 for each of the secrets required for the registry used by the agent you created in step 1. See below for more details:

<Tabs>
<TabItem value="docker" label="Docker">

- `DAGSTER_CLOUD_URL` - Your Dagster+ base URL (`https://my_org.dagster.cloud`)
- `DOCKERHUB_USERNAME` - Your DockerHub username
- `DOCKERHUB_TOKEN` - A DockerHub [access token](https://docs.docker.com/docker-hub/access-tokens/#create-an-access-token)

</TabItem>
<TabItem value="ecr" label="Amazon ECR">

- `DAGSTER_CLOUD_URL` - Your Dagster+ base URL (`https://my_org.dagster.cloud`)
- `AWS_ACCESS_KEY` - The **Access key ID** of the AWS IAM user you created in step 3
- `AWS_SECRET_ACCESS_KEY` - The **Secret access key** of the AWS IAM user you created in step 3
- `AWS_REGION` - The AWS region where your ECR registry is located

</TabItem>
<TabItem value="gcr" label="Google Container Registry (GCR)">

- `DAGSTER_CLOUD_URL` - Your Dagster+ base URL (`https://my_org.dagster.cloud`)
- `GCR_JSON_KEY` - Your GCR JSON credentials

</TabItem>
</Tabs>

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

The default base for branch deployments is `prod`. To configure a different full deployment as the base, create a branch deployment using the `dagster-cloud` CLI (see steps above) and specify the deployment with the optional `--base-deployment-name` parameter.

## Best practices

To ensure the best experience when using branch deployments, we recommend:

- **Configuring jobs based on environment**. Dagster automatically sets [environment variables](/deployment/dagster-plus/management/environment-variables/built-in) containing deployment metadata, allowing you to parameterize jobs based on the executing environment. Use these variables in your jobs to configure things like connection credentials, databases, and so on. This practice will allow you to use branch deployments without impacting production data.
- **Creating jobs to automate output cleanup.** As branch deployments don't automatically remove the output they create, you may want to create an additional Dagster job to perform the cleanup.
