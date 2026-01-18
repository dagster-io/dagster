---
title: Dagster & Meltano
sidebar_label: Meltano
sidebar_position: 1
description: The Meltano library allows you to run Meltano using Dagster. Design and configure ingestion jobs using the popular Singer specification.
tags: [community-supported, etl]
source: https://github.com/quantile-development/dagster-meltano
pypi: https://pypi.org/project/dagster-meltano/
sidebar_custom_props:
  logo: images/integrations/meltano.svg
  community: true
partnerlink: https://meltano.com/
---

import CommunityIntegration from '@site/docs/partials/\_CommunityIntegration.md';

<CommunityIntegration />

<p>{frontMatter.description}</p>

**Note** that this integration can also be [managed from the Meltano platform](https://hub.meltano.com/utilities/dagster) using `meltano add utility dagster` and configured using `meltano config dagster set --interactive`.

## Installation

<PackageInstallInstructions packageName="dagster-meltano" />

## Example

<CodeExample path="docs_snippets/docs_snippets/integrations/meltano.py" language="python" />

## About Meltano

[Meltano](https://meltano.com) provides data engineers with a set of tools for easily creating and managing pipelines as code by providing a wide array of composable connectors. Meltano's 'CLI for ELT+' lets you test your changes before they go live.
