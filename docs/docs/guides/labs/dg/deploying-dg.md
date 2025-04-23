---
title: 'Deploying to Dagster+'
sidebar_position: 350
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

This guide covers how to deploy a `dg`-compatible project to Dagster+.

## Prerequisites

- The `dg` command-line interface should be [installed](/guides/labs/dg#installation).
- A `dg`-compatible project. If you don't have one, you can create one by either:
  - [Initializing a new project](/guides/labs/dg/scaffolding-a-project)
  - [Migrating an existing project to dg](/guides/labs/dg/incrementally-adopting-dg/migrating-project)
- A [Dagster+ account](https://dagster.cloud/signup).
- If you're using Dagster+ Hybrid, a [deployed Hybrid agent in your cloud environment](dagster-plus/deployment/deployment-types/hybrid),
with access to a Docker container registry to which you can push images.


## Deploying to Dagster+ from your local machine

### 1. Set up authentication to your deployment with the `dg` CLI:
<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/deploying-dg/1-dg-plus-login.txt" />

### 2. Ensure your `dg` project includes the `dagster-cloud` package in the dependencies in its `pyproject.toml` file.

If you're using `uv`, you can run:
<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/deploying-dg/2-uv-add-dagster-cloud.txt" />
to add the dependency.

### 3. Build your project and deploy it to Dagster+.

The steps here vary depending on whether you are using Dagster+ Serverless or Dagster+ Hybrid.

<Tabs groupId="deployment">
    <TabItem value="serverless" label="Dagster+ Serverless">
        - Run the `dg plus deploy` command to build a Docker image with your project in it and deploy it to Dagster+:
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/deploying-dg/2-dg-plus-deploy.txt" />
    </TabItem>

    <TabItem value="hybrid" label="Dagster+ Hybrid">
        - Scaffold a Dockerfile and build.yaml file in your project folder:
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/deploying-dg/3-dg-scaffold-build-artifacts.txt" />

        This command will create a `Dockerfile` file and `build.yaml` file in the project folder. The
        `Dockerfile` is used during the deploy process to package your project into a Docker image,
        and the `build.yaml` includes metadata that can be used to configure the build process.

        - Add your Docker registry to the scaffolded `build.yaml` file:

        For many projects the scaffolded `Dockerfile` will work with no additional changes, but
        the `build.yaml` file needs to be modified to reference the Docker registry you want the
        agent to access.

        <CodeExample
            path="docs_snippets/docs_snippets/guides/dg/deploying-dg/4-build.yaml"
            language="YAML"
            title="build.yaml"
        />

        - Run `docker login` to ensure that the deploy command can push to your registry.

        The command do this will vary for different Docker registries. For example, for AWS ECR it might look like this:

        <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/deploying-dg/5-docker-login.txt" />

        - In your project folder, deploy your project to Dagster+:
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/deploying-dg/2-dg-plus-deploy.txt" />

    </TabItem>
</Tabs>

## Setting up CI/CD

You can configure CI/CD for your project using GitHub or a non-GitHub CI/CD provider.

- If you use [GitHub](#github) as a CI/CD provider, you can use the `dg scaffold github-actions` command to scaffold a Github Actions workflow for your `dg` project or workspace.
- If you use a [non-GitHub CI/CD provider](#non-github), you can configure CI/CD using the `dg` CLI.

## GitHub

You can scaffold a Github action workflow using the following command:
```
dg scaffold github-actions
```

The command will create a new Github Actions workflow at `.github/workflows/dagster-plus-deploy.yml` in the current Github repository, and output commands that you can run with the Github API to add a Dagster+ API token and any other secrets needed by the workflow.

The GitHub workflow deploys your code to Dagster+ using these steps:

- **Initialize:** Your code is checked out and the `build.yaml` file in your project or workspace is validated.
- **Docker image push:** A Docker image is built from your code and uploaded to your container registry.
- **Deploy to Dagster+** The code locations in Dagster+ are updated to use the new Docker image.

During the deployment, the agent will attempt to load your code and update the metadata in Dagster+. When that has finished, you should see the GitHub Action complete successfully, and also be able to see the code location under the **Deployment** tag in Dagster+.

## Non-GitHub CI/CD provider \{#non-github}

If you are using a non-GitHub CI/CD provider, your system should use the `dg plus deploy` command to deploy code locations to Dagster+.

1. Set the build environment variables. Note that all variables are required:
   - `DAGSTER_CLOUD_ORGANIZATION`: The name of your organization in Dagster+.
   - `DAGSTER_CLOUD_API_TOKEN`: A Dagster+ user or agent token. **Note:** This is a sensitive
   value and should be stored as a CI/CD secret if possible.
2. Initialize the build session.

   ```
   dg plus deploy start --deployment prod
   ```
   This reads the build.yaml and pyproject.toml configuration for each of your projects
   and initializes the build session.

   By default, the CLI will deploy to the deployment specified in the `--deployment` argument if the branch for the current Github context is `main` or `master`, or to a branch deployment with that full deployment as a base if the Github context is in some other branch. You can override this default behavior by setting the `--deployment-type` argument to `full` or `branch`, respectively.

3. Build and upload Docker images for your projects.

   It is a good idea to use a unique image tag for each Docker build. You can build one image per code location or a shared image for multiple code locations. As an example image tag, you can use the git commit SHA:

   ```
   export IMAGE_TAG=`git log --format=format:%H -n 1`
   ```

   Use this tag to build and upload your Docker image, for example:

   ```
   docker build . -t ghcr.io/org/dagster-plus-image:$IMAGE_TAG
   docker push ghcr.io/org/dagster-plus-image:$IMAGE_TAG
   ```

    The Docker image should contain a Python environment with `dagster`, `dagster-cloud`, and your code. The Dockerfile created by the `dg scaffold build-artifacts` in the previous section will work for many uv-based projects.

   The upload step is specific to your Docker container registry and will require authentication. The only requirement is that the registry you upload to must match the registry specified in your `build.yaml`.

4. Update the build session with the Docker image tag. For each code location you want to deploy, run the following command passing the `IMAGE_TAG` used in the previous step:

   ```
   dg plus deploy set-build-output --location-name=code-location-a --image-tag=IMAGE_TAG
   ```

   This command does not deploy the code location but just updates the local state in `DAGSTER_BUILD_STATEDIR`.

5. Finish deploying to Dagster+:

   ```
   dg plus deploy finish
   ```

   This command updates the code locations in Dagster+. Once this command completes, you should be able to see the code locations under the **Deployments** tab in Dagster+.
