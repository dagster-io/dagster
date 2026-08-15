---
title: Containerize the project
description: Build a multi-stage Docker image with uv for Dagster+
sidebar_position: 20
---

Dagster+ Hybrid agents pull user code from a container image. In this step, you'll write a multi-stage Dockerfile that produces a lean production image using `uv` for dependency management.

## Step 1: Write the Dockerfile

The image uses a two-stage build: a `builder` stage that installs dependencies into a virtual environment, and a final stage that copies only the built environment into a slim runtime image:

<CodeExample path="docs_projects/project_dagster_plus_deployment/Dockerfile" language="docker" title="Dockerfile" />

The two-step `uv sync` pattern is intentional:

1. **Copy lockfile first, sync dependencies** — Docker caches this layer. Subsequent builds that only change source code skip the dependency install entirely.
2. **Copy source, sync again** — installs the project itself into the same virtual environment.

The `--no-dev` flag excludes development tools (`dagster-webserver`, `pytest`, etc.) from the production image, keeping it small.

### Image tagging strategy

Dagster+ identifies which image to run using a tag embedded in the code location configuration. The CI/CD pipeline (configured in the next step) tags every image with two tags:

| Tag             | Purpose                                                    |
| --------------- | ---------------------------------------------------------- |
| `<commit-sha>`  | Immutable pointer to the exact code that was built         |
| `<branch-name>` | Mutable pointer used for convenience (e.g., `main`, `dev`) |

Using the commit SHA as the primary tag means every deployment is fully traceable — you can always look up the exact image that ran a given job.

## Step 2: Build and test locally

Generate the lockfile before building. The Dockerfile copies `uv.lock` to create a cacheable dependency layer, so the file must exist first. If you've already run `dg dev`, it was created automatically — otherwise run:

```shell
uv lock
```

Build the image locally to verify the Dockerfile is correct before pushing it to CI:

```shell
docker build -t dagster-deploy-demo:local .
```

Confirm the image starts correctly by running a quick `dagster` command inside it:

```shell
docker run --rm dagster-deploy-demo:local dagster --version
```

You should see the Dagster version printed without any import errors.

:::tip

If you're iterating on the Dockerfile and want to avoid slow rebuilds, use `--cache-from` to reuse layers from a previously built image:

```shell
docker build --cache-from dagster-deploy-demo:local -t dagster-deploy-demo:local .
```

:::

## Next steps

Continue this example with [setting up Kubernetes agents](/examples/full-pipelines/dagster-plus-deployment/kubernetes-agents).
