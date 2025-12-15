---
title: Dagster & Atlan
sidebar_label: Atlan
description: The Atlan integration streams Dagster event metadata to Atlan.
tags: [dagster-supported]
partnerlink: https://atlan.com/
sidebar_custom_props:
  logo: images/integrations/atlan.svg
---

<p>{frontMatter.description}</p>

:::note
The `--api-token` and `--url` flags in the following commands are not required if you have already run `dagster-cloud config setup`, or set the `DAGSTER_CLOUD_API_TOKEN` and `DAGSTER_CLOUD_URL` environment variables.
:::

The Atlan integration can be configured using the [dagster-cloud CLI](/api/clis/dagster-cloud-cli):

## Enable the Atlan integration

```bash
dagster-cloud integration atlan set-settings $ATLAN_TOKEN $ATLAN_DOMAIN \
  --api-token $DAGSTER_CLOUD_API_TOKEN \
  --url $DAGSTER_CLOUD_URL
```

After doing this, you can confirm that the integration is correctly configured by running the following command:

```bash
dagster-cloud integration atlan preflight-check \
  --api-token $DAGSTER_CLOUD_API_TOKEN \
  --url $DAGSTER_CLOUD_URL
```

This will return a success message if the integration is correctly configured.

## Check current integration settings

To check the current integration settings, you can run the following command:

```bash
dagster-cloud integration atlan get-settings \
  --api-token $DAGSTER_CLOUD_API_TOKEN \
  --url $DAGSTER_CLOUD_URL
```

This will return the current integration settings, with the token redacted.

## Disable the Atlan integration

The Atlan integration can be disabled by deleting your Atlan settings using the [dagster-cloud CLI](/api/clis/dagster-cloud-cli):

```bash
dagster-cloud integration atlan delete-settings \
  --api-token $DAGSTER_CLOUD_API_TOKEN \
  --url $DAGSTER_CLOUD_URL
```

## About Atlan

**Atlan** is a modern data workspace platform that helps organizations with data discovery, governance, and collaboration.
