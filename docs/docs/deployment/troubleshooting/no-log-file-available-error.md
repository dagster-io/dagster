---
title: Compute logs not visible in Dagster+ UI — "No Log File Available" error
sidebar_position: 70
description: Fix "No Log File Available" in the Dagster+ UI by using the correct compute_logs configuration key.
---

## Problem description

AWS hybrid agents successfully capture compute logs in S3 buckets, but the logs are not visible in the Dagster+ UI. Users see the message `"No Log File Available"` even though logs are being written to S3 correctly.

## Symptoms

- Message `"No Log File Available"` appears in the UI.
- Both stdout and stderr tabs appear empty.
- Log links at the bottom start with `/tmp/` instead of `s3:/`.
- Logs are successfully written to S3 bucket but not displayed in the UI.

## Root cause

The compute log manager is not configured correctly in the deployment configuration. Specifically, the configuration key uses `computeLogs` instead of the correct `compute_logs` format.

## Solution

Change `computeLogs` to `compute_logs` in your deployment configuration.

### Step-by-step resolution

1. Locate your deployment configuration (typically in Helm chart values).
2. Update the configuration key from `computeLogs` to `compute_logs`:

   ```yaml
   compute_logs: # <- here
     enabled: true
     custom:
       module: dagster_aws.s3.compute_log_manager
       class: S3ComputeLogManager
       config:
         show_url_only: false
         bucket: your-s3-bucket-name
         region: us-east-1
         prefix: 'your-deployment-name'
         use_ssl: true
         verify: true
         verify_cert_path: '/etc/ssl/certs/ca-certificates.crt'
   ```

3. Deploy the updated configuration.
4. Verify that new runs show logs in both stdout and stderr tabs.
5. Check that log links now start with `s3:/` instead of `/tmp/`.

### Alternative solutions

Ensure your S3 bucket is in the same region as your Dagster+ organization and verify IAM permissions allow Dagster+ to read from S3.

## Prevention

Always use the correct configuration key format `compute_logs` when setting up S3 compute log managers. Double-check your deployment configuration against the official documentation before deploying.

## Related documentation

- [S3ComputeLogManager documentation](/integrations/libraries/obstore#s3computelogmanager)
