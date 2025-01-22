---
title: Vector Database
description: Vector Database
last_update:
  author: Dennis Hume
sidebar_position: 30
---

Next we need to decide how to store this information we are collecting. RAG is built around being able to retrieve similar information and unfortunately, storing unstructured text in a traditional database does not facilitate the access patterns we will need. Instead we will use a vector database and store the text as a collection of vector embeddings. Storing data this way allows for similarity searches. We will help our RAG system only retrieve information that is useful.

For the vector database, we will use [Pinecone](https://www.pinecone.io/) which is a managed, cloud based vector database. Within Pinecone we can create indexes to store the vector embeddings. Indexes in Pinecone are similar to indexes in traditional databases. However, while traditional database indexes are optimized to look up exact matches, vector indexes allow for similarity searches based on the distance between high-dimension embeddings.

So the next step in our pipeline will be creating a Pinecone resource to manage our index.

## Vector Database

Our `PineconeResource` will need to give us the ability to create an index if it does not already exist and retrieve that index so we can upload our embeddings. Creating an index is relatively simple using the Pinecone client. We just need to provide a name, the dimensions (how big the embedding will be) and a metric type (how the distance will be compared across vector embeddings). Finally there is the cloud infrastructure where Pinecone will store the data (we will default to AWS). Also using the client we can return the index itself.

<CodeExample path="project_ask_ai_dagster/project_ask_ai_dagster/resources/pinecone.py" language="python" lineStart="7" lineEnd="28"/>

Like our source resources. We will initialize the resource so it can be used by our Dagster assets.

<CodeExample path="project_ask_ai_dagster/project_ask_ai_dagster/resources/pinecone.py" language="python" lineStart="30" lineEnd="33"/>

Between our sources and vector database, we can now generate our embeddings.

## Next steps

- Continue this tutorial with [embeddings](embeddings)
