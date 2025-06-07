---
title: Retrieval
description: Retrieval from RAG system
last_update:
  author: Dennis Hume
sidebar_position: 50
---

The final asset will query our RAG system. Since the pipeline is designed to answer any question related to Dagster, we will make this asset configurable by including a <PyObject section="config" module="dagster" object="Config" />. This configuration only consists of the question we want to ask the AI system:

<CodeExample
  path="docs_projects/project_ask_ai_dagster/project_ask_ai_dagster/defs/assets/retrieval.py"
  language="python"
  startAfter="start_config"
  endBefore="end_config"
/>

In order to do similarity searches, the input question will need to be embedded in the same way as the source embeddings sent to Pinecone. Again, we will use OpenAI and the same model (`text-embedding-3-small`) to turn a question into vectors. Next we can use Pinecone to search for similar vectors within the index that most closely match the input question. As we are searching within our index, we will limit the namespace to "dagster-github" and "dagster-docs" (the two sources we ingested data from). Filtering data like this shows how vector databases still support many of the same functions as traditional databases:

<CodeExample
  path="docs_projects/project_ask_ai_dagster/project_ask_ai_dagster/defs/assets/retrieval.py"
  language="python"
  startAfter="start_query"
  endBefore="end_query"
/>

With the relevant information retrieved from Pinecone, we can add some prompt engineering to combine that context extracted from Pinecone with the original question (in text). The full prompt is then sent to Open AI again (now using the `gpt-4-turbo-preview` model) to get the final answer which is recorded as a <PyObject section="assets" module="dagster" object="MaterializeResult" /> in the Dagster Catalog:

<CodeExample
  path="docs_projects/project_ask_ai_dagster/project_ask_ai_dagster/defs/assets/retrieval.py"
  language="python"
  startAfter="start_prompt"
  endBefore="end_prompt"
/>

## Getting answers

To ask a question from the pipeline, you can materialize the `query` asset and supply your question in the run configuration. The answer will be context-aware and grounded in the sources used to populate Pinecone:

```yaml
ops:
  query:
    config:
      question: What is Dagster?
```

We can ensure that questions like this will be trained on the most up-to-date information about Dagster. We can also ask questions confined to certain time ranges, like "Tell me about the issues Dagster users have faced in the past 6 months?". This will summarize the results information across all our sources.
