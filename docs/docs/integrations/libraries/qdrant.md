---
layout: Integration
status: published
name: Qdrant
title: Dagster & Qdrant
sidebar_label: Qdrant
excerpt: 'Integrate Qdrant vector search features into your workflows powered by Dagster.'
partnerlink: https://qdrant.tech/
logo: /integrations/qdrant.svg
categories:
  - Storage
enabledBy:
enables:
tags: [dagster-supported, storage]
sidebar_custom_props:
  logo: images/integrations/qdrant.png
---

The `dagster-qdrant` library lets you integrate Qdrant's vector database with Dagster, making it easy to build AI-driven data pipelines. You can run vector searches and manage data directly within Dagster.

### Installation

```bash
pip install dagster dagster-qdrant
```

### Example

<CodeExample path="docs_snippets/docs_snippets/integrations/qdrant.py" language="python" />

### About Qdrant

Qdrant (read: quadrant) is a vector similarity search engine. It provides a production-ready service with a convenient API to store, search, and manage vectors with additional payload and extended filtering support. It makes it useful for all sorts of neural network or semantic-based matching, faceted search, and other applications.

Learn more from the [Qdrant documentation](https://qdrant.tech/).
