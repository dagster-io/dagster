---
title: Dagster & Atlan
sidebar_label: Atlan
description: The Atlan integration stream Dagster event metadata to Atlan.
tags: [dagster-supported]
partnerlink: https://atlan.com/
---

<p>{frontMatter.description}</p>

## Enable the Atlan integration via CLI

The Atlan integration can be enabled by setting your Atlan settings using the dagster-cloud CLI.

```bash 
dagster-cloud integration atlan set-settings $ATLAN_TOKEN $ATLAN_DOMAIN \
  --api-token $DAGSTER_CLOUD_API_TOKEN \
  --url $DAGSTER_CLOUD_URL
```

## Disable the Atlan integration via CLI

The Atlan integration can be disabled by deleting your Atlan settings using the dagster-cloud CLI.

```bash 
dagster-cloud integration atlan delete-settings \
  --api-token $DAGSTER_CLOUD_API_TOKEN \
  --url $DAGSTER_CLOUD_URL
```
## About Atlan

**Atlan** is a modern data workspace platform that helps organizations with data discovery, governance, and collaboration.