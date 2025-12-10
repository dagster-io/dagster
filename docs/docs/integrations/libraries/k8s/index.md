---
title: Dagster & Kubernetes
sidebar_label: Kubernetes
sidebar_position: 1
description: The Kubernetes integration library provides the PipesK8sClient resource, enabling you to launch Kubernetes pods and execute external code directly from Dagster assets and ops. This integration allows you to pass parameters to Kubernetes pods while Dagster receives real-time events, such as logs, asset checks, and asset materializations, from the initiated jobs. With minimal code changes required on the job side, this integration is both efficient and easy to implement.
tags: [dagster-supported, compute]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-k8s
pypi: https://pypi.org/project/dagster-k8s/
sidebar_custom_props:
  logo: images/integrations/kubernetes.svg
partnerlink: https://kubernetes.io/
canonicalUrl: '/integrations/libraries/k8s'
slug: '/integrations/libraries/k8s'
---

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-k8s" />

## Example

<CodeExample path="docs_snippets/docs_snippets/integrations/kubernetes.py" language="python" />

## Deploying to Kubernetes?

- Deploying to Dagster+: Use with a Dagster+ Hybrid deployment, the Kubernetes agent executes Dagster jobs on a Kubernetes cluster. Checkout the [Dagster+ Kubernetes Agent](/deployment/dagster-plus/hybrid/kubernetes) guide for more information.
- Deploying to Open Source: Visit the [Deploying Dagster to Kubernetes](/deployment/oss/deployment-options/kubernetes) guide for more information.

## About Kubernetes

**Kubernetes** is an open source container orchestration system for automating software deployment, scaling, and management. Google originally designed Kubernetes, but the Cloud Native Computing Foundation now maintains the project.
