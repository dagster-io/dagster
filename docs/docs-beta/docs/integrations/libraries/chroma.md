---
layout: Integration
status: published
name: Chroma
title: Dagster & Chroma
sidebar_label: Chroma
excerpt: 'Integrate Chroma vector database capabilities into your AI pipelines powered by Dagster.'
partnerlink: https://docs.trychroma.com/
logo: /integrations/chroma.svg
categories:
  - Storage
enabledBy:
enables:
tags: [dagster-supported, storage]
sidebar_custom_props:
  logo: images/integrations/chroma.png
---

The `dagster-chroma` library allows you to easily interact with Chroma's vector database capabilities to build AI-powered data pipelines in Dagster. You can perform vector similarity searches, manage schemas, and handle data operations directly from your Dagster assets.

### Installation

```bash
pip install dagster dagster-chroma
```

### Examples

```python
import os
import dagster as dg
from dagster_chroma import ChromaResource, LocalConfig, HttpConfig

@dg.asset
def my_table(chroma: ChromaResource):
    with chroma.get_client() as chroma_client:
        collection = chroma_client.create_collection("fruits")

        collection.add(
            documents=[
                "This is a document about oranges",
                "This is a document about pineapples",
                "This is a document about strawberries",
                "This is a document about cucumbers"],
            ids=["oranges", "pineapples", "strawberries", "cucumbers"],
        )

        results = collection.query(
            query_texts=["hawaii"],
            n_results=1,
        )

defs = dg.Definitions(
    assets=[my_table],
    resources={
        "chroma": ChromaResource(
            connection_config=
                LocalConfig(persistence_path="./chroma") if os.getenv("DEV") else
                    HttpConfig(host="192.168.0.10", port=8000)
        ),
    }
)
```

### About Chroma

**Chroma** is the open-source AI application database. Chroma makes it easy to build LLM apps by making knowledge, facts, and skills pluggable for LLMs. It provides a simple API for storing and querying embeddings, documents, and metadata. Chroma can be used to build semantic search, question answering, and other AI-powered applications. The database can run embedded in your application or as a separate service.
