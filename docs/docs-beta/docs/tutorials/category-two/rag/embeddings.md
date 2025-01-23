---
title: Embeddings
description: Generate embeddings
last_update:
  author: Dennis Hume
sidebar_position: 40
---

In order to store the data in our vector database, we need to convert the free text into embeddings. Let's look at Github first. First when we are extracting data from Github, we will want to be careful to avoid rate limiting. We can do this by partitioning our asset into weekly chunks using a `WeeklyPartitionsDefinition`:

<CodeExample path="project_ask_ai_dagster/project_ask_ai_dagster/assets/ingestion.py" language="python" lineStart="11" lineEnd="13"/>

We will supply that partition in the decorator or our asset. As well as an `AutomationCondition` to ensure that the weekly partition is updated every Monday. The rest of our asset will use the `GithubResource` we defined earlier and return a list of LangChain `Documents`:

<CodeExample path="project_ask_ai_dagster/project_ask_ai_dagster/assets/ingestion.py" language="python" lineStart="15" lineEnd="53"/>

The next asset will convert those `Documents` to vectors and upload them to Pinecone. In order to generate the embeddings we will need an AI model. In this case we will use OpenAI's `text-embedding-3-small` model to transform the text we have collected from Github into embeddings. Dagster provides an `OpenAIResource` to interact with the OpenAI client and we will use that to create the embeddings. This asset will also create the index in Pinecone:

<CodeExample path="project_ask_ai_dagster/project_ask_ai_dagster/assets/ingestion.py" language="python" lineStart="55" lineEnd="125"/>

This process will be very similar for the Github discussions content.

## Custom IO Manager
Looking at the code you may have noticed the `document_io_manager`. Because LangChain `Documents` are a special object type, we need to do some work to serialize and deserialize the data. IO Managers are responsible for handling the inputs and outputs of assets and how the data is persisted. This IO manager will use the local file system to save the output of assets returning `Documents` as JSON files. It will then read those JSON files back into `Documents` in assets that take in those inputs:

<CodeExample path="project_ask_ai_dagster/project_ask_ai_dagster/definitions.py" language="python" lineStart="13" lineEnd="44"/>

This IO manager will be attached to the `Definitions` of the project which also contains our assets and resources:

<CodeExample path="project_ask_ai_dagster/project_ask_ai_dagster/definitions.py" language="python" lineStart="55" lineEnd="65"/>


## Scraping Embeddings

The assets for the documentation scraping will behave similar to the Github assets. We do not need to worry about rate limiting in the same way as Github so we can leave out the partition that we had defined for Github. Instead we will just include half a second sleep between scraping pages. But like the Github assets, our ingestion asset will return a collection of `Documents` that will be handled by the IO manager. This asset will also include the `AutomationCondition` to update data on the same cadence as our Github source.

The asset that generates the embeddings with the documentation site will need one additional change. Because the content of the documentation pages are so large, we need to split data into chunks. The `split_text` function ensures that we split the text into equal length chunks. We also want to keep similar chunks together and associated with the page they were on so we will hash the index of the URL to ensure data correctly stays together. Once the data is chunked, it can be batched and sent to Pinecone:

<CodeExample path="project_ask_ai_dagster/project_ask_ai_dagster/assets/ingestion.py" language="python" lineStart="395" lineEnd="410"/>

Dagster is now set to continuously ingest data from all of our configured sources and populate the Pinecone index. We have now completed the main half of our RAG system. Next we need to ensure we can pull relevant information when it is answering questions. We will add one final asset to query our system.

## Next steps

- Continue this tutorial with [retrieval](retrieval)

