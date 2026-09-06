---
title: Set up CI/CD with GitHub Actions
description: Automate image builds and Dagster+ deployments with GitHub Actions
sidebar_position: 40
---

With agents running in Kubernetes, the final piece is a CI/CD pipeline that builds your Docker image and tells Dagster+ to use it. All of the sections below are part of a single workflow file: `.github/workflows/dagster-cloud-deploy.yml`.

The workflow handles three scenarios:

- **Push to `main`, `staging`, or `dev`:** Deploy to the corresponding long-lived environment
- **Pull request opened or updated:** Create or update a branch deployment
- **Pull request closed:** Tear down the branch deployment

## Step 1: Configure required secrets and variables

In your GitHub repository settings, add:

**Secrets** (Settings → Secrets and variables → Actions → Secrets):

| Name                      | Value                                       |
| ------------------------- | ------------------------------------------- |
| `DAGSTER_CLOUD_API_TOKEN` | CI token from `dg plus create ci-api-token` |
| `REGISTRY_USERNAME`       | Container registry username                 |
| `REGISTRY_PASSWORD`       | Container registry password or token        |

**Variables** (Settings → Secrets and variables → Actions → Variables):

| Name                         | Value                                                                        |
| ---------------------------- | ---------------------------------------------------------------------------- |
| `DAGSTER_CLOUD_ORGANIZATION` | Your Dagster+ org name (the subdomain in `<org>.dagster.cloud`)              |
| `CONTAINER_REGISTRY`         | Registry prefix, e.g. `ghcr.io/your-org` or `us-docker.pkg.dev/project/repo` |

## Step 2: Create the workflow

### Triggers and concurrency

The workflow fires on pushes to the three long-lived branches and on all pull request lifecycle events. The `concurrency` block ensures only one deploy runs per branch or PR at a time — if a new push arrives while a deploy is in progress, GitHub cancels the older run:

<CodeExample
  path="docs_projects/project_dagster_plus_deployment/.github/workflows/dagster-cloud-deploy.yml"
  language="yaml"
  startAfter="start_triggers"
  endBefore="end_triggers"
  title=".github/workflows/dagster-cloud-deploy.yml"
/>

### Step 2.1: Add `configure` job

This job runs first and determines where to deploy. It maps branch names to Dagster+ deployment names and computes an immutable image tag from the commit SHA. All downstream jobs read from its outputs, so the branch-to-deployment mapping lives in one place:

<CodeExample
  path="docs_projects/project_dagster_plus_deployment/.github/workflows/dagster-cloud-deploy.yml"
  language="yaml"
  startAfter="start_job_configure"
  endBefore="end_job_configure"
  title=".github/workflows/dagster-cloud-deploy.yml"
/>

### Step 2.2: Add `build-and-push` job

This job builds the Docker image and pushes two tags: the commit SHA (immutable, used by the deploy jobs), and the branch name (mutable convenience pointer). GitHub Actions layer caching makes rebuilds fast when only source files change. This job is skipped entirely when a PR is closed, since there's nothing to build:

<CodeExample
  path="docs_projects/project_dagster_plus_deployment/.github/workflows/dagster-cloud-deploy.yml"
  language="yaml"
  startAfter="start_job_build"
  endBefore="end_job_build"
  title=".github/workflows/dagster-cloud-deploy.yml"
/>

### Step 2.3: Add `deploy-full` job

This job runs on pushes to `main`, `staging`, or `dev`. It calls `dagster-cloud deployment code-location update` to point the target deployment at the newly built image, recording the commit SHA and Git URL for traceability in the Dagster+ UI:

<CodeExample
  path="docs_projects/project_dagster_plus_deployment/.github/workflows/dagster-cloud-deploy.yml"
  language="yaml"
  startAfter="start_job_deploy_full"
  endBefore="end_job_deploy_full"
  title=".github/workflows/dagster-cloud-deploy.yml"
/>

### Step 2.4: Add `deploy-branch` job

This job handles pull requests. On open or sync, it creates or updates a branch deployment named `pr-<number>`, then points its code location at the new image. On PR close, it deletes the branch deployment. The `always()` condition ensures cleanup runs even when `build-and-push` was skipped:

<CodeExample
  path="docs_projects/project_dagster_plus_deployment/.github/workflows/dagster-cloud-deploy.yml"
  language="yaml"
  startAfter="start_job_deploy_branch"
  endBefore="end_job_deploy_branch"
  title=".github/workflows/dagster-cloud-deploy.yml"
/>

## Step 3: Verify the pipeline

Push a commit to your `dev` branch and watch the workflow run in the **Actions** tab. After it completes:

1. Open the Dagster+ UI and navigate to your `dev` deployment.
2. Check **Deployment → Code Locations** — the image tag should match the commit SHA.
3. Open a pull request and confirm a new branch deployment appears in Dagster+.
4. Close the PR and confirm the branch deployment is removed.

## Summary

You now have a complete Dagster+ deployment on Kubernetes:

- **Assets** that read `DAGSTER_CLOUD_DEPLOYMENT_NAME` to adapt to their environment
- **A multi-stage Docker image** built with `uv` and cached in GitHub Actions
- **Three Helm-managed agents** — one per environment, isolated in their own namespaces, with resource limits and TTLs appropriate for each tier
- **A GitHub Actions workflow** that maps branches to deployments and manages branch deploy lifecycle automatically

## Typical developer workflow

Once CI/CD is set up, the day-to-day flow for shipping a change looks like this:

1. **Create a feature branch** off `dev`:

   ```shell
   git checkout dev
   git checkout -b feature/my-change
   ```

2. **Develop locally** with `dg dev`, write tests, iterate.

3. **Open a PR against `dev`** — GitHub Actions builds the image and creates a branch deployment named `pr-<number>`. You can test your pipeline changes in the Dagster+ UI under that branch deployment before merging.

4. **Merge to `dev`** — CI deploys to the `dev` deployment. Run integration tests against dev data.

5. **Promote to staging:** merge `dev` → `staging`. CI deploys to `staging` for pre-production validation.

6. **Promote to prod:** merge `staging` → `main`. CI deploys to `prod`.
