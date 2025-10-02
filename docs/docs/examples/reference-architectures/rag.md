---
title: Retrieval-augmented generation (RAG)
description: A RAG system that indexes data and uses retrieved context to generate responses.
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/integrations/weaviate.png
---

## Objective

Build a retrieval-augmented generation (RAG) system that extracts data from GitHub using the GitHub API. The extracted content is stored in a vector database (Weaviate) to enable efficient semantic search. When a user submits a question through an asset at runtime, relevant context is retrieved from Weaviate and passed to OpenAI to generate a response grounded in the source material.

## Architecture

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#FFFFFF',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#FFFFFF'
    }
  }
}%%
graph LR
    GH[<img src='/images/examples/icons/github.svg' width='50' height='50' /> Github]
    OA[<img src='/images/examples/icons/openai.svg' width='50' height='50' /> OpenAI]
    WV[<img src='/images/examples/icons/weaviate.png' width='50' height='50' /> Weaviate]

    GH ==> OA
    OA <==> WV
```

## Dagster Architecture

![2048 resolution](/images/examples/reference-architectures/rag.png)

### 1. Github ingestion

Data is extracted from GitHub using the GitHub GraphQL API and can be implemented as a custom resource in Dagster. To avoid unnecessary re-importing, the data can be partitioned and scheduled, ensuring only new or updated content is fetched during each run.

**Dagster Features**

- [Resources](/guides/build/external-resources)
- [Partitions](/guides/build/partitions-and-backfills)
- [Schedules](/guides/automate/schedules)

---

### 2. Generate embeddings

The raw unstructured data from GitHub must be converted into vector embeddings before it can be inserted into a vector database. Using an LLM like OpenAI, the text is transformed into embeddings that capture its semantic meaning for efficient retrieval.

**Dagster Features**

- [Dagster OpenAI](/integrations/libraries/openai)

---

### 3. Upsert embeddings into Weaviate

An index is managed in Weaviate to store embeddings, with new or updated GitHub embeddings continuously loaded into the index as changes occur.

**Dagster Features**

- [Dagster Weaviate](/integrations/libraries/weaviate)

---

### 4. Retrieve information with OpenAI

An asset is configured with a run configuration to enable dynamic runtime execution. This allows questions to be posed to the LLM with the added context of data stored in the vector database.

```yaml
ops:
  openai_retrieval:
    config:
      question: What is Dagster?
```

**Dagster Features**

- [Dagster OpenAI](/integrations/libraries/openai)
- [Run configuration](/guides/operate/configuration/run-configuration)
