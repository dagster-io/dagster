---
title: Dagster & Hightouch
sidebar_label: Hightouch
description: Integrate with Hightouch to trigger and monitor syncs.
tags: [dagster-supported, reverse-etl]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-hightouch
pypi: https://pypi.org/project/dagster-hightouch/
sidebar_custom_props:
  logo: images/integrations/hightouch.svg
partnerlink: https://hightouch.com
canonicalUrl: '/integrations/libraries/hightouch'
slug: '/integrations/libraries/hightouch'
---

The Hightouch integration allows data engineers to trigger and monitor syncs from their data warehouse to various SaaS destinations using the `ConfigurableHightouchResource` and the modern `HightouchSyncComponent`.

## Installation

<PackageInstallInstructions packageName="dagster-hightouch" />

## Examples

### Using the Hightouch Sync Component (Modern)

The `HightouchSyncComponent` allows you to define Hightouch syncs as Dagster assets declaratively. This is the recommended approach for modern Dagster projects.

```python
import dagster as dg
from dagster_hightouch import HightouchSyncComponent

# Components are typically loaded from YAML, but can be used in Python definitions
hightouch_sync = HightouchSyncComponent(
    sync_id="my-hightouch-sync-id",
    asset={"key": ["hightouch", "marketing_sync"]}
)

defs = dg.Definitions(
    assets=[hightouch_sync.build_defs(None)]
)
```


For job-based workflows, the `ConfigurableHightouchResource` can be used with the `hightouch_sync_op` to trigger syncs within a job.
For job-based workflows, the ConfigurableHightouchResource can be used with the hightouch_sync_op to trigger syncs within a job.


```python
import dagster as dg
from dagster_hightouch import ConfigurableHightouchResource, hightouch_sync_op

@dg.job(
    resource_defs={
        "hightouch": ConfigurableHightouchResource(
            api_key=dg.EnvVar("HIGHTOUCH_API_KEY")
        )
    }
)
def sync_job():
    hightouch_sync_op()
```

## About Hightouch

[Hightouch](https://hightouch.com/) is a leading Reverse ETL platform that syncs data from your data warehouse to the operational tools your business teams use every day, such as Salesforce, HubSpot, and Marketo. By integrating Hightouch with Dagster, you can ensure that your downstream SaaS tools are always populated with the freshest data from your pipelines.
