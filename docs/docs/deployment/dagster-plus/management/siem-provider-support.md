---
description: Export Dagster+ compute logs to SIEM providers like Arctic Wolf or Sentinel One by routing logs through cloud storage.
sidebar_position: 7100
title: Exporting logs to SIEM providers
tags: [dagster-plus-feature]
---

Dagster+ does not integrate directly with SIEM providers (Arctic Wolf, Sentinel One, Splunk, etc.). Instead, the supported pattern is to route compute logs to your own cloud storage bucket and configure your SIEM to ingest from there.

## Pattern

1. Configure Dagster+ to write compute logs to your own cloud storage (Amazon S3, Azure Blob Storage, or Google Cloud Storage) by setting up a custom `ComputeLogManager`. See [Managing compute logs and error messages](/deployment/dagster-plus/management/managing-compute-logs-and-error-messages) for the full configuration steps.
2. Set `show_url_only: true` in the manager configuration so Dagster Labs only sees pre-signed URLs to your bucket. Your log content stays in your account.
3. Configure your SIEM provider to monitor and ingest log objects from that bucket as a data source.
4. Verify ingestion end-to-end after the first runs complete.

For a typical S3 setup with periodic uploads and server-side encryption:

```yaml
# dagster.yaml
compute_logs:
  module: dagster_aws.s3.compute_log_manager
  class: S3ComputeLogManager
  config:
    bucket: 'your-company-dagster-logs'
    prefix: 'dagster-'
    region: 'us-west-1'
    upload_interval: 30 # Upload partial logs every 30 seconds
    skip_empty_files: true
    show_url_only: true
    upload_extra_args:
      ServerSideEncryption: 'AES256'
```

## Alternative: insights export

If you only need pipeline metrics rather than full compute logs, Dagster+ Insights can deliver insights data via the Dagster API. This is more limited than compute log export but may be sufficient for monitoring use cases. See [Dagster+ Insights](/guides/observe/insights).

## Related documentation

- [Managing compute logs and error messages](/deployment/dagster-plus/management/managing-compute-logs-and-error-messages)
- [Customizing agent settings](/deployment/dagster-plus/management/customizing-agent-settings)
