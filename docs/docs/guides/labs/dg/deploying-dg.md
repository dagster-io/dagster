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
- If you're using Dagster+ Hybrid, a [deployed Hybrid agent in your cloud environment](/dagster-plus/deployment/deployment-types/hybrid/),
with access to a Docker container registry to which you can push images.


## Deploying to Dagster+ from your local machine

### 1. Set up authentication to your deployment with the `dg` CLI:
<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/deploying-dg/1-dg-plus-login.txt" />

### 2. Ensure your `dg` project includes the `dagster-cloud` package in the dependencies in its `pyproject.toml` file.

If you're using `uv`, you can run:
<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/deploying-dg/2-uv-add-dagster-cloud.txt" />
to add the dependency.

### 3. Build your project and deploy it to Dagster+. The steps here vary depending on whether you
are using Dagster+ Serverless or Dagster+ Hybrid.

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

        The command to login will vary for different Docker registries. For example, for AWS ECR it might look like this:

        <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/deploying-dg/5-docker-login.txt" />

        - In your project folder, deploy your project to Dagster+:
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/deploying-dg/2-dg-plus-deploy.txt" />

    </TabItem>
</Tabs>
