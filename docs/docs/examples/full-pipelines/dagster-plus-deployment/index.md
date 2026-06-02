---
title: Deploying Dagster+ to Kubernetes
description: Learn how to deploy Dagster+ across multiple environments using Kubernetes hybrid agents and GitHub Actions
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/dagster-primary-mark.svg
tags: [code-example]
canonicalUrl: '/examples/full-pipelines/dagster-plus-deployment'
slug: '/examples/full-pipelines/dagster-plus-deployment'
---

In this tutorial, you'll deploy a Dagster+ project to Kubernetes using [Dagster+ Hybrid](/deployment/dagster-plus/hybrid). You'll set up three long-lived environments (dev, staging, and prod) and a GitHub Actions pipeline that automatically creates branch deployments for every pull request.

By the end, you'll have:

- Environment-aware assets that behave differently in dev, staging, and prod
- A multi-stage Docker image built with `uv`
- Separate Helm-managed Kubernetes agents for each environment
- A CI/CD workflow that maps branches to deployments and handles PR branch deploys automatically

## Prerequisites

To follow this guide, you'll need:

- Python 3.10+ and `uv` installed (see the [uv installation guide](https://docs.astral.sh/uv))
- A [Dagster+](https://dagster.cloud) account with three deployments named `dev`, `staging`, and `prod`
- A Kubernetes cluster (GKE, EKS, AKS, or similar) with `kubectl` and `helm` configured
- A container registry (GitHub Container Registry, Google Artifact Registry, etc.)
- A GitHub repository for your code

## Step 1: Bootstrap the project

Scaffold a new Dagster project with `dg`:

```shell
uvx -U create-dagster project dagster-deploy-demo
cd dagster-deploy-demo
```

Add the `dagster-cloud` package so your code can interact with Dagster+ APIs:

```shell
uv add dagster-cloud
```

### Project layout

The project follows the standard `dg` project structure:

```
dagster-deploy-demo/
├── dagster_cloud.yaml          # Dagster+ code location config
├── Dockerfile                  # Multi-stage image built with uv
├── pyproject.toml
├── helm/
│   └── dagster-agent/
│       ├── values-dev.yaml
│       ├── values-staging.yaml
│       └── values-prod.yaml
├── .github/
│   └── workflows/
│       └── dagster-cloud-deploy.yml
└── src/
    └── project_dagster_plus_deployment/
        ├── definitions.py
        └── defs/
            ├── assets.py
            └── schedules.py
```

## Step 2: Run locally

Start the Dagster webserver to confirm the project loads correctly:

```shell
dg dev
```

Open [http://127.0.0.1:3000](http://127.0.0.1:3000) to see the empty asset graph.

## Next steps

Continue this example with [defining environment-aware assets](/examples/full-pipelines/dagster-plus-deployment/define-assets).
