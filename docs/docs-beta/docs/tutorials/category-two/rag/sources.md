---
title: Sources
description: Sources of data
last_update:
  author: Dennis Hume
sidebar_position: 20
---

We are going to build an AI pipeline to answer questions specific to Dagster. One way to optimize a model for a given context is using Retrieval-Augmented Generation (RAG). A RAG system combines a retrieval module, which fetches relevant external information (e.g., from a database or documents), with a generation module, typically a language model, to produce more informed and contextually accurate outputs. This approach enhances the AI's ability to answer queries or generate content by grounding responses in specific, retrieved data.

For our RAG system we will combine two different data sources. Information from the Dagster Github and the Dagster Documentation site.

## Github

To retrieve data from Github, we are going to borrow some code from the [dagster-open-platform](https://github.com/dagster-io/dagster-open-platform). This repository shows how we use Dagster internally and Github is one of those data sources. The code we are interested in reusing is the `GithubResource`. This resource allows us to query Github using GraphQL. We are most interested in issues and discussions so our resource will have two public methods to retrieve that information over a given date range.

<CodeExample path="project_ask_ai_dagster/project_ask_ai_dagster/resources/github.py" language="python" lineStart="13" lineEnd="43"/>

Most of the code we can use is from the Open Platform. Because we are working with unstructured data, we need to retrieve it in a specific format. We can use [LangChain](https://www.langchain.com/) and return the data as `Documents`. This allows us to combine the contents with metadata which will be useful for when we ultimately upload the data to our vector database. Because the metadata is unique discussions and issues. We will create two separate functions to process the data: `convert_discussions_to_documents` and `convert_discussions_to_documents`.

We now have everything we need for the `GithubResource` so we can initialize it using our `GITHUB_TOKEN`

<CodeExample path="project_ask_ai_dagster/project_ask_ai_dagster/resources/github.py" language="python" lineStart="213"/>


## Web Scraping

To scrape the Dagster website we will create a separate resource. Since the Dagster site does not have an API, we will have to scrape the data. We will use [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/). To create our `SitemapScraper` resource we need to parse the XML from the sitemap to get all the urls for all the individual pages.

<CodeExample path="project_ask_ai_dagster/project_ask_ai_dagster/resources/scraper.py" language="python" lineStart="12" lineEnd="21"/>

Then we can create a function to scrape the individual pages. Like the Github resource, we will return the contents of the page as a Langchain Document.

<CodeExample path="project_ask_ai_dagster/project_ask_ai_dagster/resources/scraper.py" language="python" lineStart="22" lineEnd="51"/>

Finally we can initialize the resource.

<CodeExample path="project_ask_ai_dagster/project_ask_ai_dagster/resources/scraper.py" language="python" lineStart="54"/>


## Next steps

- Continue this tutorial with [vector-database](vector-database)