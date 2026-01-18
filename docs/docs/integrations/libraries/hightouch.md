---
title: Dagster & Hightouch
sidebar_label: Hightouch
sidebar_position: 1
description: With this integration you can trigger Hightouch syncs and monitor them from within Dagster. Fine-tune when Hightouch syncs kick-off, visualize their dependencies, and monitor the steps in your data activation workflow.
tags: [community-supported, etl]
source: https://github.com/dagster-io/community-integrations/tree/main/libraries/dagster-hightouch
pypi: https://pypi.org/project/dagster-hightouch/
sidebar_custom_props:
  logo: images/integrations/hightouch.svg
  community: true
partnerlink: https://hightouch.com/
---

import CommunityIntegration from '@site/docs/partials/\_CommunityIntegration.md';

<CommunityIntegration />

<p>{frontMatter.description}</p>

This native integration helps your team more effectively orchestrate the last mile of data analytics—bringing that data from the warehouse back into the SaaS tools your business teams live in. With the `dagster-hightouch` integration, Hightouch users have more granular and sophisticated control over when data gets activated.

## Installation

<PackageInstallInstructions packageName="dagster-hightouch" />

## Example

<CodeExample path="docs_snippets/docs_snippets/integrations/hightouch.py" language="python" />

## About Hightouch

**Hightouch** syncs data from any data warehouse into popular SaaS tools that businesses run on. Hightouch uses the power of Reverse ETL to transform core business applications from isolated data islands into powerful integrated solutions.
