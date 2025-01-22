---
title: Retrieval
description: Retrieval from RAG system
last_update:
  author: Dennis Hume
sidebar_position: 50
---

The final asset will query our RAG system. The system is designed to answer any question related to Dagster so we will make this asset configurable at execution using a `Config`. This configuration will only consist of the question we want to ask the AI system:

<CodeExample path="project_ask_ai_dagster/project_ask_ai_dagster/assets/retrieval.py" language="python" lineStart="11" lineEnd="13"/>

In order to retrieve relevant results, the input question will need to be embedded in the same way as our source embeddings. Again we will use OpenAI and the same model (`text-embedding-3-small`) to turn a question into vectors. Next we can use Pinecone to search for similar vectors within the index that most closely match the input question. As we are searching within our index, we will limit the namespace to "dagster-github" and "dagster-docs". This is why it is possible to have an index that contains embeddings from different sources and how a vector database still allows for filtering like traditional databases:

<CodeExample path="project_ask_ai_dagster/project_ask_ai_dagster/assets/retrieval.py" language="python" lineStart="42" lineEnd="59"/>

With the relevant information retrieved from Pinecone, we can do a little prompt engineering to combine that context with the original question (in text) that was asked. The full prompt is then feed to Open AI again (now using the `gpt-4-turbo-preview` model) to get the final answer which is recorded as a `MaterializeResult` in the Dagster Catalog:

<CodeExample path="project_ask_ai_dagster/project_ask_ai_dagster/assets/retrieval.py" language="python" lineStart="85" lineEnd="115"/>

## Getting Answers

To ask a question from the pipeline, you can materialize the `query` asset and supply your question in the run configuration. The answer will be context aware and grounded in the sources used to populate Pinecone.

```yaml
ops:
  query:
    config:
        question: What is Dagster?
```

We can ensure that questions like this will be trained on the most up to date information about Dagster. But you can also ask questions confined to certain time ranges like "Tell me about the issues Dagster users have faced in the past 6 months?". This will summarize the results information across all our sources.