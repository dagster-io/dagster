---
title: Permission denied error with dagster_cloud_pre_install.sh in serverless deployments
sidebar_position: 150
description: Fix "Permission denied" errors that occur when Dagster+ Serverless runs dagster_cloud_pre_install.sh during the Docker build.
---

## Problem description

When executing a serverless deployment with a `dagster_cloud_pre_install.sh` script, you may encounter a permission denied error that looks like this:

```text
/bin/sh: 1: ./dagster_cloud_pre_install.sh: Permission denied
```

## Root cause

This error typically occurs due to incorrect file permissions in your Git repository. The issue occurs during the Docker build process when trying to execute the pre-install script that typically contains system-level package installations.

## Solution

To resolve this:

1. Ensure the script has executable permissions by running:

   ```bash
   git update-index --chmod=+x dagster_cloud_pre_install.sh
   ```

2. Commit the permission changes to your repository.
3. Push the changes and retry your deployment.

## Example pre-install script

Here's an example of a valid pre-install script:

```bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

# Base deps
apt-get update
apt-get install -y --no-install-recommends curl gnupg ca-certificates lsb-release

# Additional package installations
...
```

## Related documentation

For more information about serverless deployments and configuration, visit the following resources:

- [Dagster+ Serverless Deployment Guide](/deployment/dagster-plus/serverless)
