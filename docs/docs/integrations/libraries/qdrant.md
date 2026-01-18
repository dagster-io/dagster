---
title: Dagster & Qdrant
sidebar_label: Qdrant
sidebar_position: 1
description: The Qdrant library lets you integrate Qdrant's vector database with Dagster, making it easy to build AI-driven data pipelines. You can run vector searches and manage data directly within Dagster.
tags: [community-supported, storage]
source:
pypi: https://pypi.org/project/dagster-qdrant
sidebar_custom_props:
  logo: images/integrations/qdrant.png
  community: true
partnerlink: https://qdrant.tech/
---

import CommunityIntegration from '@site/docs/partials/\_CommunityIntegration.md';

<CommunityIntegration />

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-qdrant" />

## Example

<CodeExample path="docs_snippets/docs_snippets/integrations/qdrant.py" language="python" />

## About Qdrant

Qdrant (read: quadrant) is a vector similarity search engine. It provides a production-ready service with a convenient API to store, search, and manage vectors with additional payload and extended filtering support. It makes it useful for all sorts of neural network or semantic-based matching, faceted search, and other applications.

Learn more from the [Qdrant documentation](https://qdrant.tech).
