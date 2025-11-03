---
title: 'Configuring versioned state storage'
description: Learn how to configure the state storage backend for state-backed components in your Dagster project.
sidebar_position: 300
---

import Beta from '@site/docs/partials/_Beta.md';

<Beta />

When using the `VERSIONED_STATE_STORAGE` state management strategy, you need to configure a state storage backend in your Dagster instance. Under the hood, you are just configuring a [UPath](https://github.com/fsspec/universal_pathlib) to your specific storage backend under which all state files will be stored.

## Instance configuration

Configure the storage backend in your `dagster.yaml` file (or equivalent helm chart settings):

<Tabs groupId="cloud-provider">
<TabItem value="aws" label="AWS S3">

```yaml
# dagster.yaml
defs_state_storage:
  module: dagster._core.storage.defs_state.blob_storage_state_storage
  class: UPathDefsStateStorage
  config:
    base_path: s3://my-bucket/dagster/defs-state
    storage_options:
      ...
```

</TabItem>
<TabItem value="gcs" label="Google Cloud Storage">

```yaml
# dagster.yaml
defs_state_storage:
  module: dagster._core.storage.defs_state.blob_storage_state_storage
  class: UPathDefsStateStorage
  config:
    base_path: gs://my-bucket/dagster/defs-state
    storage_options:
      ...
```

</TabItem>
<TabItem value="azure" label="Azure Blob Storage">

```yaml
# dagster.yaml
defs_state_storage:
  module: dagster._core.storage.defs_state.blob_storage_state_storage
  class: UPathDefsStateStorage
  config:
    base_path: az://my-container/dagster/defs-state
    storage_options:
      ...

```

</TabItem>
</Tabs>

Refer to the [universal-pathlib documentation](https://github.com/fsspec/universal_pathlib) for information on configuring your specific storage backend. The `storage_options` field is used to pass additional options to your specific `UPath`.

:::note

If you are deploying using Helm, make sure to set the `includeInstance` flag to true in your `dagster-user-deployments` values. This will mount the Dagster instance ConfigMap into your user code pods, enabling them to correctly load your definitions.

:::

## Next steps

- Learn how to [manage state in CI/CD](/guides/build/components/state-backed-components/managing-state-in-ci-cd) deployments