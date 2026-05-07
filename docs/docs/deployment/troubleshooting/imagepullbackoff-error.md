---
title: ImagePullBackOff error when using GitHub Container Registry with Kubernetes
sidebar_position: 130
description: How to configure a Kubernetes image pull secret so your cluster can authenticate with GitHub Container Registry (ghcr.io).
---

## Problem description

When deploying to Dagster+ using GitHub Container Registry (`ghcr.io`) in a Kubernetes environment, you may encounter an `ImagePullBackOff` error even with valid GitHub credentials. This typically occurs because the Kubernetes cluster itself needs access to the container registry.

## Symptoms

The error message will look similar to this:

```text
Container 'dagster' status: Waiting: ImagePullBackOff: Back-off pulling image "ghcr.io/<redacted_image>": ErrImagePull: failed to pull and unpack image "ghcr.io/<redacted_image>": failed to resolve reference "ghcr.io/<redacted_image>": failed to authorize: failed to fetch anonymous token: unexpected status from GET request to https://ghcr.io/token?scope=repository%<redacted_repo>: 401 Unauthorized
```

This occurs because while your GitHub Actions workflow may have the correct credentials, the Kubernetes cluster requires its own authentication to pull images.

## Solution

To resolve this issue:

1. Create a Kubernetes secret with your GitHub Container Registry credentials.
2. Apply the secret to your Kubernetes cluster in the `dagster-cloud` namespace.
3. Configure your deployment to use these credentials for pulling images.

## Related documentation

For more information about Dagster+ deployments and container configuration, visit the [Dagster+ deployment documentation](/deployment/dagster-plus).
