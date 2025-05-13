---
title: 'Deploying to Dagster+'
sidebar_position: 350
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

This guide covers deploying a `dg`-compatible project to Dagster+.

## Prerequisites

To follow the steps in this guide, you will need:

- The `dg` command-line interface [installed](/guides/labs/dg#installation).
- A `dg`-compatible project. If you don't have one, you can create one by either:
  - [Initializing a new project](/guides/labs/dg/scaffolding-a-project)
  - [Migrating an existing project to dg](/guides/labs/dg/incrementally-adopting-dg/migrating-project)
- A [Dagster+ account](https://dagster.cloud/signup).
- If you're using Dagster+ Hybrid, a [deployed Hybrid agent in your cloud environment](/dagster-plus/deployment/deployment-types/hybrid/),
with access to a Docker container registry to which you can push images.


## Steps

### 1. Authenticate to your deployment
<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/deploying-dg/1-dg-plus-login.txt" />

### 2. Add the `dagster-cloud` package as a dependency to your project

If you're using `uv`, you can run:
<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/deploying-dg/2-uv-add-dagster-cloud.txt" />
to add the dependency. If not, you can add `dagster-cloud` as a dependency to your project in the same place where your `dagster` depedency is defined (for example, your `pyproject.toml`, `setup.py`, or `pyproject.toml` file.)

### 3. Build your project and deploy it to Dagster+

The steps here vary depending on whether you
are using Dagster+ Serverless or Dagster+ Hybrid.

#### Dagster+ Serverless

Run the `dg plus deploy` command to build a Docker image with your project in it and deploy it to Dagster+:
<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/deploying-dg/2-dg-plus-deploy.txt" />

#### Dagster+ Hybrid

1. Scaffold a Dockerfile and `build.yaml` file in your project folder:
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/deploying-dg/3-dg-scaffold-build-artifacts.txt" />
    :::note
    This command will create a `Dockerfile` file and `build.yaml` file in the project folder. The
    `Dockerfile` is used during the deploy process to package your project into a Docker image,
    and the `build.yaml` includes metadata that can be used to configure the build process.
    :::

2. Add your Docker registry to the scaffolded `build.yaml` file:

    <CodeExample
        path="docs_snippets/docs_snippets/guides/dg/deploying-dg/4-build.yaml"
        language="YAML"
        title="build.yaml"
    />

    :::note
    For many projects the scaffolded `Dockerfile` will work with no additional changes, but the `build.yaml` file needs to be modified to reference the Docker registry you want the agent to access.
    :::

3. Run `docker login` to ensure that the deploy command can push to your registry. The command to do this will vary for different Docker registries. For example, for AWS ECR, it might look like this:
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/deploying-dg/5-docker-login.txt" />

4. In your project folder, deploy your project to Dagster+:
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/deploying-dg/2-dg-plus-deploy.txt" />