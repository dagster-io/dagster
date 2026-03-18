---
title: dagster-hightouch integration reference
description: API reference for the Dagster Hightouch integration.
sidebar_position: 500
---

This reference provides an overview of the APIs available in the [`dagster-hightouch`](/integrations/libraries/hightouch) library.

## Relevant APIs

| Name | Description |
| --- | --- |
| `HightouchSyncComponent` | A component that represents a Hightouch sync as a Dagster asset. |
| `ConfigurableHightouchResource` | A resource for connecting to the Hightouch API using pythonic configuration. |
| `HightouchResource` | Client for the Hightouch REST API. |
| `hightouch_sync_op` | An op that triggers a Hightouch sync and polls until completion. |

## Components

The `HightouchSyncComponent` is the modern, declarative way to define Hightouch syncs as Dagster assets. When materialized, it calls the Hightouch API, polls for completion, and reports metadata such as rows processed and sync status.

```yaml
type: HightouchSyncComponent
attributes:
  sync_id: "12345"
  asset:
    key: ["marketing", "salesforce_sync"]
```

| Attribute | Description |
| --- | --- |
| `sync_id` | The ID of the Hightouch sync. Can be a literal string or an environment variable (e.g., `$HIGHTOUCH_SYNC_ID`). |
| `asset` | The specification of the asset that this sync produces. |

## Resources

### ConfigurableHightouchResource

The recommended resource for modern Dagster projects using pythonic configuration.

<CodeExample path="docs_snippets/docs_snippets/integrations/hightouch_resource.py" language="python" />

| Attribute | Type | Default | Description |
| --- | --- | --- | --- |
| `api_key` | `str` | Required | Your Hightouch API key. |
| `request_max_retries` | `int` | `3` | Maximum number of retries for API requests. |
| `request_retry_delay` | `float` | `0.25` | Delay between retries in seconds. |
| `fail_on_warning` | `bool` | `False` | Whether to treat sync warnings as failures. |
| `poll_interval` | `float` | `3` | Time in seconds between successive status polls. |
| `poll_timeout` | `float \| None` | `None` | Maximum time to wait before timing out. `None` means no timeout. |

**Methods:**

- `sync_and_poll(sync_id, fail_on_warning=None, poll_interval=None, poll_timeout=None)` — Triggers a sync and polls until completion. Returns a `HightouchOutput`.

### HightouchResource (Legacy)

A lower-level client for the Hightouch REST API. For modern Dagster projects, use `ConfigurableHightouchResource` instead.

**Methods:**

| Method | Description |
| --- | --- |
| `make_request(method, endpoint, params=None)` | Sends a request to the Hightouch API with automatic retries. |
| `start_sync(sync_id)` | Triggers a sync and returns the sync request ID. |
| `poll_sync(sync_id, sync_request_id, ...)` | Polls for the completion of a sync run. |
| `sync_and_poll(sync_id, ...)` | Triggers a sync and polls until completion. Returns a `HightouchOutput`. |
| `get_sync_details(sync_id)` | Gets details about a sync. |
| `get_sync_run_details(sync_id, sync_request_id)` | Gets details about a specific sync run. |
| `get_destination_details(destination_id)` | Gets details about a destination. |

## Ops

### hightouch_sync_op

Executes a Hightouch sync for a given `sync_id`, and polls until that sync completes, raising an error if it is unsuccessful. It outputs a `HightouchOutput` which contains the details of the Hightouch connector after the sync run successfully completes.

Requires the `hightouch` resource key to be configured with a `HightouchResource`.

| Config option | Type | Default | Description |
| --- | --- | --- | --- |
| `sync_id` | `str` | Required | The Sync ID that this op will trigger. |
| `poll_interval` | `float` | `3` | Time in seconds between successive polls. |
| `fail_on_warning` | `bool` | `False` | Whether to consider warnings a failure. |
| `poll_timeout` | `float \| None` | `None` | Maximum time to wait before timing out. |

## Types

### HightouchOutput

Contains recorded information about the state of a Hightouch sync after a sync completes.

| Attribute | Type | Description |
| --- | --- | --- |
| `sync_details` | `Dict[str, Any]` | Details about the sync. See [Hightouch API: GetSync](https://hightouch.io/docs/api-reference/#operation/GetSync). |
| `sync_run_details` | `Dict[str, Any]` | Details about the sync run. See [Hightouch API: ListSyncRuns](https://hightouch.io/docs/api-reference/#operation/ListSyncRuns). |
| `destination_details` | `Dict[str, Any]` | Details about the destination. See [Hightouch API: GetDestination](https://hightouch.io/docs/api-reference/#operation/GetDestination). |
