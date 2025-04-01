---
layout: Integration
status: published
name: obstore
title: Dagster & obstore
sidebar_label: obstore
excerpt: The community-supported `dagster-obstore` package provides an integration with obstore.
sidebar_custom_props:
  logo: images/integrations/obstore.png
  community: true
---

The community-supported `dagster-obstore` package provides an integration with obstore, providing three lean integrations with object stores, ADLS, GCS & S3.

### S3ComputeLogManager

The `S3ComputeLogManager` writes `stdout` and `stderr` to any S3 compatible endpoint.

```yaml
# there are multiples ways to configure the S3ComputeLogManager
# Explicitly set S3 secrets
compute_logs:
  module:  dagster_obstore.s3.compute_log_manager
  class: S3ComputeLogManager
  config:
    bucket: "dagster-logs"
    access_key_id:
      env: ACCESS_KEY_ID
    secret_access_key:
      env: SECRET_KEY
    local_dir: "/tmp/dagster-logs"
    allow_http: false
    allow_invalid_certificates: false
    timeout: "60s"  # Timeout for obstore requests
    region: "us-west-1"
# Use S3 with custom endpoint (Minio, Cloudflare R2 etc.)
compute_logs:
  module:  dagster_obstore.s3.compute_log_manager
  class: S3ComputeLogManager
  config:
    bucket: "dagster-logs"
    access_key_id: "access-key-id"
    secret_access_key: "my-key"
    local_dir: "/tmp/dagster-logs"
    endpoint: "http://alternate-s3-host.io"
    region: "us-west-1"
# Don't set secrets through config, but let obstore pick it up from ENV VARS
compute_logs:
  module:  dagster_obstore.s3.compute_log_manager
  class: S3ComputeLogManager
  config:
    bucket: "dagster-logs"
    local_dir: "/tmp/dagster-logs"
```

### ADLSComputeLogManager

The `ADLSComputeLogManager` writes `stdout` and `stderr` to Azure Datalake/Blob storage.

```yaml
# there are multiples ways to configure the ADLSComputeLogManager
# Authenticate with access key
compute_logs:
  module:  dagster_obstore.azure.compute_log_manager
  class: ADLSComputeLogManager
  config:
    storage_account: "my-az-account"
    container: "dagster-logs"
    access_key:
      env: ACCESS_KEY
    local_dir: "/tmp/dagster-logs"
    allow_http: false
    allow_invalid_certificates: false
    timeout: "60s"  # Timeout for obstore requests
# Authenticate with service principal
compute_logs:
  module:  dagster_obstore.azure.compute_log_manager
  class: ADLSComputeLogManager
  config:
    storage_account: "my-az-account"
    container: "dagster-logs"
    client_id: "access-key-id"
    client_secret: "my-key"
    tenant_id: "tenant-id"
    local_dir: "/tmp/dagster-logs"
# Authenticate with use_azure_cli
compute_logs:
  module:  dagster_obstore.azure.compute_log_manager
  class: ADLSComputeLogManager
  config:
    storage_account: "my-az-account"
    container: "dagster-logs"
    use_azure_cli: true
    local_dir: "/tmp/dagster-logs"
# Don't set secrets through config, but let obstore pick it up from ENV VARS
compute_logs:
  module:  dagster_obstore.azure.compute_log_manager
  class: ADLSComputeLogManager
  config:
    storage_account: "my-az-account"
    container: "dagster-logs"
    local_dir: "/tmp/dagster-logs"
```

### GCSComputeLogManager

The `GCSComputeLogManager` writes `stdout` and `stderr` to Google Cloud Storage.

```yaml
# there are multiples ways to configure the GCSComputeLogManager
# Authenticate with service account
compute_logs:
  module:  dagster_obstore.gcs.compute_log_manager
  class: GCSComputeLogManager
  config:
    bucket: "dagster-logs"
    service_account: "access-key-id"
    service_account_key: "my-key"
    local_dir: "/tmp/dagster-logs"
# Don't set secrets through config, but let obstore pick it up from ENV VARS
compute_logs:
  module:  dagster_obstore.gcs.compute_log_manager
  class: GCSComputeLogManager
  config:
    bucket: "dagster-logs"
    local_dir: "/tmp/dagster-logs"
```

---

For more information, see the [dagster-obstore GitHub repository](https://github.com/dagster-io/community-integrations/tree/main/libraries/dagster-obstore).
