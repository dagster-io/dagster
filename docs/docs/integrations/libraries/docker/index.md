---
title: Dagster & Docker
sidebar_label: Docker
sidebar_position: 1
description: The Docker integration library provides the PipesDockerClient resource, enabling you to launch Docker containers and execute external code directly from Dagster assets and ops. This integration allows you to pass parameters to Docker containers while Dagster receives real-time events, such as logs, asset checks, and asset materializations, from the initiated jobs. With minimal code changes required on the job side, this integration is both efficient and easy to implement.
tags: [dagster-supported, compute]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-docker
pypi: https://pypi.org/project/dagster-docker/
sidebar_custom_props:
  logo: images/integrations/docker.svg
partnerlink: https://www.docker.com/
---

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-docker" />

## Example

<CodeExample path="docs_snippets/docs_snippets/integrations/docker.py" language="python" />

## Deploying to Docker?

- Deploying to Dagster+: Use with a Dagster+ Hybrid deployment, the Docker agent executes Dagster jobs on a Docker cluster. Checkout the [Dagster+ Docker Agent](/deployment/dagster-plus/hybrid/docker) guide for more information.
- Deploying to Open Source: Visit the [Deploying Dagster to Docker](/deployment/oss/deployment-options/docker) guide for more information.

## About Docker

**Docker** is a set of platform-as-a-service products that use OS-level virtualization to deliver software in packages called containers. The service has both free and premium tiers. The software that hosts the containers is called Docker Engine.
