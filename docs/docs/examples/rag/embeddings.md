---
title: Embeddings
description: Generate embeddings
last_update:
  author: Dennis Hume
sidebar_position: 40
---

In order to store the data in our vector database, we need to convert the free text into embeddings. Let's look at GitHub first. First when we are extracting data from GitHub, we will want to be careful to avoid rate limiting. We can do this by partitioning our asset into weekly chunks using a `WeeklyPartitionsDefinition`:

<CodeExample path="docs_projects/project_ask_ai_dagster/project_ask_ai_dagster/assets/ingestion.py" language="python" startAfter="start_partition" endBefore="end_partition"/>

We will supply that partition in the decorator of our asset, as well as an <PyObject section="assets" module="dagster" object="AutomationCondition" /> to ensure that the weekly partition is updated every Monday. The rest of our asset will use the `GithubResource` we defined earlier and return a list of LangChain `Documents`:

<CodeExample path="docs_projects/project_ask_ai_dagster/project_ask_ai_dagster/assets/ingestion.py" language="python" startAfter="start_github_issues_raw" endBefore="end_github_issues_raw"/>

The next asset will convert those `Documents` to vectors and upload them to Pinecone. In order to generate the embeddings, we will need an AI model. In this case, we will use OpenAI's `text-embedding-3-small` model to transform the text we have collected from GitHub into embeddings. Dagster provides an `OpenAIResource` to interact with the OpenAI client ,and we will use that to create the embeddings. This asset will also create the index in Pinecone:

<CodeExample path="docs_projects/project_ask_ai_dagster/project_ask_ai_dagster/assets/ingestion.py" language="python" startAfter="start_github_issues_embeddings" endBefore="end_github_issues_embeddings"/>

This process will be very similar for the GitHub discussions content.

## Custom IO Manager
Looking at the code, you may have noticed the `document_io_manager`. Because LangChain `Documents` are a special object type, we need to do some work to serialize and deserialize the data. [I/O Managers](/guides/build/io-managers/) are responsible for handling the inputs and outputs of assets and how the data is persisted. This I/O manager will use the local file system to save the output of assets returning `Documents` as JSON files. It will then read those JSON files back into `Documents` in assets that take in those inputs:

<CodeExample path="docs_projects/project_ask_ai_dagster/project_ask_ai_dagster/definitions.py" language="python" startAfter="start_io_manager" endBefore="end_io_manager"/>

This I/O manager will be attached to the <PyObject section="definitions" module="dagster" object="Definitions" /> of the project, which also contains our assets and resources:

<CodeExample path="docs_projects/project_ask_ai_dagster/project_ask_ai_dagster/definitions.py" language="python" startAfter="start_def" endBefore="end_def"/>


## Scraping embeddings

The assets for the documentation scraping will behave similar to the GitHub assets. We will not partition by date like Github, so we can leave out that out of the asset. But like the GitHub assets, our ingestion asset will return a collection of `Documents` that will be handled by the I/O manager. This asset will also include the <PyObject section="assets" module="dagster" object="AutomationCondition" /> to update data on the same cadence as our GitHub source.

The asset that generates the embeddings with the documentation site will need one additional change. Because the content of the documentation pages is so large, we need to split data into chunks. The `split_text` function ensures that we split the text into equal length chunks. We also want to keep similar chunks together and associated with the page they were on so we will hash the index of the URL to ensure data stays together. correctly Once the data is chunked, it can be batched and sent to Pinecone:

<CodeExample path="docs_projects/project_ask_ai_dagster/project_ask_ai_dagster/assets/ingestion.py" language="python" startAfter="start_batch" endBefore="end_batch"/>

Dagster is now set to continuously ingest data from all of our configured sources and populate the Pinecone index. We have now completed the main half of our RAG system. Next we need to ensure we can pull relevant information when it is answering questions. We will add one final asset to query our system.

## Next steps

- Continue this example with [retrieval](retrieval)

