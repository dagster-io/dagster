---
title: GCP Components
sidebar_label: Components
sidebar_position: 1
description: Configuration-driven GCP resources using Dagster Components.
tags: [dagster-supported, gcp, components]
---

<p>{frontMatter.description}</p>

The `dagster-gcp` library provides a set of components that allow you to configure GCP resources directly in YAML. These components wrap existing `dagster-gcp` resources, enabling faster setup and better reusability.

## Service Components

### BigQuery & GCS

Components for interacting with BigQuery and Google Cloud Storage.

- **BigQueryResourceComponent**: Provides a standard `BigQueryResource`.
- **GCSResourceComponent**: Provides a standard `GCSResource`.
- **GCSFileManagerResourceComponent**: Provides a `GCSFileManager` for artifact storage.

### Dataproc

Manage Dataproc clusters.

- **DataprocResourceComponent**: Configures a `DataprocResource` (Beta).

## Examples

### BigQuery (Default Credentials)

```yaml
type: dagster_gcp.BigQueryResourceComponent
attributes:
  project: my-gcp-project
  location: us-central1
  resource_key: bigquery
```

### GCS Resource

```yaml
type: dagster_gcp.GCSResourceComponent
attributes:
  project: my-gcp-project
  resource_key: gcs
```

### Dataproc Cluster

```yaml
type: dagster_gcp.DataprocResourceComponent
attributes:
  project_id: my-gcp-project
  region: us-central1
  cluster_name: dagster-cluster
  cluster_config_dict:
    master_config:
      num_instances: 1
      machine_type_uri: n1-standard-4
    worker_config:
      num_instances: 2
      machine_type_uri: n1-standard-4
  resource_key: dataproc
```
