---
title: Dagster & Census
sidebar_label: Census
description: With the Census integration you can execute a Census sync and poll until that sync completes, raising an error if it's unsuccessful.
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

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-census" />

## Example

<CodeExample path="docs_snippets/docs_snippets/integrations/census.py" language="python" />

## About Census

**Census** syncs data from your cloud warehouse to the SaaS tools your organization uses. It allows everyone in your organization to take action with good data, no custom scripts or API integrations required.
