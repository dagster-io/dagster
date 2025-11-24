---
title: Dagster & Census (Pythonic)
sidebar_label: Census (Pythonic)
description: The dagster-census library provides a CensusComponent, which can be used to represent Census syncs as assets in Dagster.
tags: [community-supported, etl]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-census
pypi: https://pypi.org/project/dagster-census/
sidebar_custom_props:
  logo: images/integrations/census.svg
  community: true
partnerlink: https://www.getcensus.com/
---

import CommunityIntegration from '@site/docs/partials/\_CommunityIntegration.md';

<CommunityIntegration />

:::note

If you are just getting started with the Census integration, we recommend using the new [Census component](/integrations/libraries/census).

:::

This guide provides instructions for using Dagster with Census using the `dagster-census` library. Your Census syncs can be represented as assets in the Dagster asset graph, allowing you to track lineage and dependencies between Census assets and data assets you are already modeling in Dagster. You can also use Dagster to orchestrate Census syncs, allowing you to trigger syncs on a cadence or based on upstream data changes.

## Installation

<PackageInstallInstructions packageName="dagster-census" />

## Example

<CodeExample path="docs_snippets/docs_snippets/integrations/census.py" language="python" />

## About Census

**Census** syncs data from your cloud warehouse to the SaaS tools your organization uses. It allows everyone in your organization to take action with good data, no custom scripts or API integrations required.
