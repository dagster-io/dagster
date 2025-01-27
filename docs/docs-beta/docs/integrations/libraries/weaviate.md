---
layout: Integration
status: published
name: Weaviate
title: Dagster & Weaviate
sidebar_label: Weaviate
excerpt: 'Using this integration, you can seamlessly integrate Weaviate into your Dagster workflows, leveraging Weaviates data warehousing capabilities for your data pipelines.'
partnerlink: https://weaviate.io/
logo: /integrations/weaviate.png
categories:
  - Storage
enabledBy:
enables:
tags: [dagster-supported, storage]
sidebar_custom_props:
  logo: images/integrations/weaviate.png
---

The `dagster-weaviate` library allows you to easily interact with Weaviate's vector database capabilities to build AI-powered data pipelines in Dagster. You can perform vector similarity searches, manage schemas, and handle data operations directly from your Dagster assets.

### Installation

```bash
pip install dagster dagster-weaviate
```

### Examples

<CodeExample path="docs_beta_snippets/docs_beta_snippets/integrations/weaviate.py" language="python" />

### About Weaviate

**Weaviate** is an open-source vector database that enables you to store and manage vector embeddings at scale. You can start with a small dataset and scale up as your needs grow. This enables you to build powerful AI applications with semantic search and similarity matching capabilities. Weaviate offers fast query performance using vector-based search and GraphQL APIs, making it a powerful tool for AI-powered applications and machine learning workflows.
