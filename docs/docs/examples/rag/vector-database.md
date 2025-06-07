---
title: Vector Database
description: Vector Database
last_update:
  author: Dennis Hume
sidebar_position: 30
---

Next, we need to decide how to store the information sourced in the [previous step](/examples/rag/sources). RAG is built around being able to retrieve similar information. Unfortunately, storing unstructured text in a traditional database does not facilitate the access patterns needed. Instead, we will use a vector database and store the text as a collection of vector embeddings. Storing data this way allows for similarity searches. This will help our RAG system only retrieve information that is useful when asked specific questions.

For the vector database, we will use [Pinecone](https://www.pinecone.io/) which is a managed, cloud-based vector database. Within Pinecone, we can create indexes to store the vector embeddings. Indexes in Pinecone are similar to indexes in traditional databases. However, while traditional database indexes are optimized to look up exact matches, vector indexes allow for similarity searches based on the distance between high-dimension embeddings.

The next step in our pipeline will be creating this Pinecone resource to manage the index.

## Pinecone

The `PineconeResource` will need the ability to create an index if it does not already exist and retrieve that index so we can upload our embeddings. Creating an index is relatively simple using the Pinecone client. We just need to provide a name, the dimensions (how big the embedding will be), and a metric type (how the distance will be compared across vector embeddings). Finally, there is the cloud infrastructure that Pinecone will use to store the data (we will default to AWS):

<CodeExample
  path="docs_projects/project_ask_ai_dagster/project_ask_ai_dagster/defs/resources/pinecone.py"
  language="python"
  startAfter="start_resource"
  endBefore="end_resource"
/>

Like our other resources, we will initialize the `PineconeResource` so it can be used by our Dagster assets:

<CodeExample
  path="docs_projects/project_ask_ai_dagster/project_ask_ai_dagster/defs/resources/pinecone.py"
  language="python"
  startAfter="start_resource_int"
  endBefore="end_resource_int"
/>

Between our sources and vector database resources, we can now extract data and upload embeddings in our Dagster assets.

## Next steps

- Continue this example with [embeddings](/examples/rag/embeddings)
