---
title: Dagster & Weaviate
sidebar_label: Weaviate
description: The Weaviate library allows you to easily interact with Weaviate's vector database capabilities to build AI-powered data pipelines in Dagster. You can perform vector similarity searches, manage schemas, and handle data operations directly from your Dagster assets.
tags: [community-supported, storage]
source: https://github.com/dagster-io/community-integrations/tree/main/libraries/dagster-weaviate
pypi: https://pypi.org/project/dagster-weaviate
sidebar_custom_props:
  logo: images/integrations/weaviate.png
  community: true
partnerlink: https://weaviate.io/
---

import CommunityIntegration from '@site/docs/partials/\_CommunityIntegration.md';

<CommunityIntegration />

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-weaviate" />

## Examples

<CodeExample path="docs_snippets/docs_snippets/integrations/weaviate.py" language="python" />

## About Weaviate

**Weaviate** is an open-source vector database that enables you to store and manage vector embeddings at scale. You can start with a small dataset and scale up as your needs grow. This enables you to build powerful AI applications with semantic search and similarity matching capabilities. Weaviate offers fast query performance using vector-based search and GraphQL APIs, making it a powerful tool for AI-powered applications and machine learning workflows.
