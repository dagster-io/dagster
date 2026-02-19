---
title: Dagster & Cube
sidebar_label: Cube
sidebar_position: 1
description: With the Cube integration you can setup Cube and Dagster to work together so that Dagster can push changes from upstream data sources to Cube using its integration API.
tags: [community-supported]
source:
pypi: https://pypi.org/project/dagster-cube/
sidebar_custom_props:
  logo: images/integrations/cube.svg
  community: true
partnerlink: https://cube.dev/
---

import CommunityIntegration from '@site/docs/partials/\_CommunityIntegration.md';

<CommunityIntegration />

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-cube" />

## Example

<CodeExample path="docs_snippets/docs_snippets/integrations/cube.py" language="python" />

## About Cube

**Cube.js** is the semantic layer for building data applications. It helps data engineers and application developers access data from modern data stores, organize it into consistent definitions, and deliver it to every application.
