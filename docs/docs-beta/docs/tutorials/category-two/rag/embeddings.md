---
title: Embeddings
description: Generate embeddings
last_update:
  author: Dennis Hume
sidebar_position: 40
---

As already mentioned, in order to store our data in our vector database, we need to first convert it into embeddings. Let's look at Github first. One thing we will want to be careful of when extracting data from Github is to avoid rate limiting. We can do this by partitioning our asset into weekly chunks using a `WeeklyPartitionsDefinition`:

<CodeExample path="project_ask_ai_dagster/project_ask_ai_dagster/assets/ingestion.py" language="python" lineStart="11" lineEnd="13"/>

We will supply that partition in the decorator or our asset. As well as an `AutomationCondition` to ensure that the weekly partition is updated every Monday. The rest of our asset will use the `GithubResource` we defined earlier and return a list of LangChain `Documents`:

<CodeExample path="project_ask_ai_dagster/project_ask_ai_dagster/assets/ingestion.py" language="python" lineStart="15" lineEnd="53"/>

The next asset will convert those `Documents` to vectors and upload them to Pinecone. In order to generate the embeddings we will need an AI model. In this case we will use OpenAI's `text-embedding-3-small` model to turn the text we have collected from the Github issues into embeddings. Dagster provides an `OpenAIResource` to interact with the OpenAI client directly. This asset create an index in Pinecone, convert the Documents from the `github_issues_raw` asset into embeddings with OpenAI and then upsert the embeddings into the Pinecone index:

<CodeExample path="project_ask_ai_dagster/project_ask_ai_dagster/assets/ingestion.py" language="python" lineStart="55" lineEnd="125"/>

This process will be very similar for the Github discussions content.


## Custom IO Manager
Looking at the code you may have noticed the `document_io_manager`. Because LangChain `Documents` are special, we need to do some custom work to serialize and deserialize the data across our assets. IO Managers are responsible for handling the inputs and output of assets and how data is persisted. This IO manager will use the local file system to save the output of assets returning `Documents` as JSON files. It will then read those JSON files back into `Documents` in assets that accept those inputs.


<CodeExample path="project_ask_ai_dagster/project_ask_ai_dagster/definitions.py" language="python" lineStart="13" lineEnd="44"/>

This IO manager will be attached to the `Definitions` of the project so any asset that references that IO manager, will use it without any other configurations being necessary:

<CodeExample path="project_ask_ai_dagster/project_ask_ai_dagster/definitions.py" language="python" lineStart="55" lineEnd="65"/>


## Scraping Embeddings

The assets for the documentation scraping will behave similar to the Github assets. We do not need to worry about rate limiting in the same way as Github so we can leave out the partition that we had defined for the Github assets. Instead we will just include half a second sleep between scraping pages. But like the Github assets, we will get a collection of `Documents` that will be handled by the IO manager. This asset will also include the same `AutomationCondition` to update data on the same cadence as our Github source.

<CodeExample path="project_ask_ai_dagster/project_ask_ai_dagster/assets/ingestion.py" language="python" lineStart="245" lineEnd="300"/>

The asset that generates the embeddings with the documentation site will need one additional change. Because the contents are so large, we will need to split data into chunks. The `split_text` function ensures that we can split our text into equal length chunks. We still want to keep similar chunks together so we will hash the index of the URL to ensure we keep similar data together:

<CodeExample path="project_ask_ai_dagster/project_ask_ai_dagster/assets/ingestion.py" language="python" lineStart="395" lineEnd="410"/>

But otherwise the embeddings will upload to Pinecone.

Dagster is now set to continuously ingest data from all of our configured sources. You may have noticed that all the data from our sources added to the same index in Pinecone. This is exactly what we want so our RAG system can pull relevant information from one location when it is answering questions. We add one final asset so we can query our system.

## Next steps

- Continue this tutorial with [retrieval](retrieval)

