---
title: Dagster & Chroma
sidebar_label: Chroma
description: 'Integrate Chroma vector database capabilities into your AI pipelines powered by Dagster.'
tags: [storage]
source: https://github.com/dagster-io/community-integrations/tree/main/libraries/dagster-chroma
pypi: https://pypi.org/project/dagster-chroma/
built_by: Dagster
sidebar_custom_props:
  logo: images/integrations/chroma.png
partnerlink: https://docs.trychroma.com/
---

The `dagster-chroma` library allows you to easily interact with Chroma's vector database capabilities to build AI-powered data pipelines in Dagster. You can perform vector similarity searches, manage schemas, and handle data operations directly from your Dagster assets.

### Installation

```bash
pip install dagster dagster-chroma
```

### Example

<CodeExample path="docs_snippets/docs_snippets/integrations/chroma.py" language="python" />

### About Chroma

**Chroma** is the open-source AI application database. Chroma makes it easy to build LLM apps by making knowledge, facts, and skills pluggable for LLMs. It provides a simple API for storing and querying embeddings, documents, and metadata. Chroma can be used to build semantic search, question answering, and other AI-powered applications. The database can run embedded in your application or as a separate service.
