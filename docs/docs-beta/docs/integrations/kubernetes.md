---
layout: Integration
status: published
name: Kubernetes
title: Dagster & Kubernetes
sidebar_label: Kubernetes
excerpt: Launch Kubernetes pods and execute external code directly from Dagster.
date: 2024-08-30
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-k8s
docslink: https://docs.dagster.io/concepts/dagster-pipes/kubernetes
partnerlink: https://kubernetes.io/
logo: /integrations/Kubernetes.svg
categories:
  - Compute
enabledBy:
enables:
---

### About this integration

The `dagster-k8s` integration library provides the `PipesK8sClient` resource, enabling you to launch Kubernetes pods and execute external code directly from Dagster assets and ops. This integration allows you to pass parameters to Kubernetes pods while Dagster receives real-time events, such as logs, asset checks, and asset materializations, from the initiated jobs. With minimal code changes required on the job side, this integration is both efficient and easy to implement.

### Installation

```bash
pip install dagster-k8s
```

### Example

<CodeExample filePath="integrations/kubernetes.py" language="python" />

### Deploying to Kubernetes?

- Deploying to Dagster+: Use with a Dagster+ Hybrid deployment, the Kubernetes agent executes Dagster jobs on a Kubernetes cluster. Checkout the [Dagster+ Kubernetes Agent](https://docs.dagster.io/dagster-plus/deployment/agents/kubernetes) guide for more information.
- Deploying to Open Source: Visit the [Deploying Dagster to Kubernetes](https://docs.dagster.io/deployment/guides/kubernetes) guide for more information.

### About Kubernetes

**Kubernetes** is an open source container orchestration system for automating software deployment, scaling, and management. Google originally designed Kubernetes, but the Cloud Native Computing Foundation now maintains the project.
