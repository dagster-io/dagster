---
title: GitHub CI/CD build process fails with self-hosted Ubuntu 20.04 runners
sidebar_position: 120
description: Replace the PEX file install with a direct dagster-cloud CLI install to work around Ubuntu 20.04 self-hosted runner limitations.
---

## Problem description

When using self-hosted Ubuntu 20.04 runners for GitHub CI/CD workflows, the build process fails due to inability to build wheels for cryptography and missing Python 3.10. This typically occurs when switching from `ubuntu-latest` to older self-hosted runners due to network restrictions or Azure Container Registry (ACR) access requirements.

## Symptoms

- CI/CD workflow breaks when using self-hosted Ubuntu 20.04 runners.
- Unable to build wheels for cryptography package.
- Python 3.10 not found errors.
- Connection issues to Azure Container Registry from IP addresses outside the network.

## Root cause

The issue occurs because older Ubuntu versions (20.04) may not have the required Python version or dependencies needed for the default Dagster+ CLI PEX file installation. Network restrictions may also force the use of self-hosted runners that lack the proper environment setup.

## Solution

Replace the PEX file installation method with direct `dagster-cloud` CLI installation in your GitHub Actions workflow.

### Step-by-step resolution

1. Modify your GitHub Actions workflow to install the `dagster-cloud` CLI directly instead of using the PEX file.
2. Move the CLI installation step to the beginning of your workflow to ensure it's available for all subsequent steps, including branch deployment cleanup.
3. Test the modified workflow on your self-hosted Ubuntu 20.04 runner to verify it can successfully build images and upload to ACR.

### Alternative solutions

If you don't require `dagster-pipes` functionality, you can use a downgraded version of the CI/CD workflow that provides basic functionality for building images and uploading to ACR while maintaining compatibility with Ubuntu 20.04.

## Prevention

When setting up self-hosted runners, ensure they have the required Python version and dependencies installed. Consider using containerized runners or updating to more recent Ubuntu versions when network policies allow.

## Related documentation

- [Dagster+ CI/CD integration](/deployment/dagster-plus/deploying-code/configuring-ci-cd)
