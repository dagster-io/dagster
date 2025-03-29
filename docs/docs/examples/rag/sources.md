---
title: Sources
description: Sources of data
last_update:
  author: Dennis Hume
sidebar_position: 20
---

We are going to build an AI pipeline that can answer questions specific to Dagster. In order to do this, we need to enhance an AI model. One way to do this is by adding context to an existing model using Retrieval-Augmented Generation (RAG). A RAG system combines a retrieval module, which fetches relevant external information, with a generation module to produce more informed and contextually accurate outputs. This approach improves the AI's ability to answer queries or generate content by grounding responses in retrieved data.

To begin we need our specific context. Our RAG system will combine two different data sources about Dagster, GitHub issues and discussions and the Dagster Documentation site.

## GitHub

To retrieve data from GitHub, we are going to borrow code from the [dagster-open-platform](https://github.com/dagster-io/dagster-open-platform). The open platform repository shows how we use Dagster internally, and GitHub is one of the data sources we use, and we wrote a resource to manage pulling that data. The [`GithubResource`](/api/python-api/libraries/dagster-github#resources) allows us to query GitHub using GraphQL. We are most interested in issues and discussions, so our resource will have two methods to retrieve that information over a given date range:

<CodeExample
  path="docs_projects/project_ask_ai_dagster/project_ask_ai_dagster/resources/github.py"
  language="python"
  startAfter="start_resource"
  endBefore="end_resource"
/>

Because we are working with unstructured data, we need to process it in a specific format. We can use [LangChain](https://www.langchain.com/) and return the data as `Documents`. LangChain is a framework designed for building applications with LLMs. It makes chaining tasks for AI applications, like RAG, easier to build. By converting the Github data into `Documents`, it will be easier to upload to our retrieval system later on.

Documents also allow us to add metadata. Because the metadata is unique to discussions and issues, we will create two separate methods in the resource to process the data: `convert_discussions_to_documents` and `convert_issues_to_documents`.

We now have everything we need for the `GithubResource` so we can initialize it using our `GITHUB_TOKEN`:

<CodeExample
  path="docs_projects/project_ask_ai_dagster/project_ask_ai_dagster/resources/github.py"
  language="python"
  startAfter="start_resource_init"
  endBefore="end_resource_init"
/>

## Web scraping

To scrape the Dagster documentation website, we will create a separate resource. Since the Dagster site does not have an API, we will have to scrape the data from the pages themselves. The `SitemapScraper` resource will have two functions, to parse the site map to get the individual urls and the ability to scrape page content. The Python framework [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) can assist in scraping the contents of a page.

The first step will be taking in the sitemap URL and parsing the XML into a list of all the individual pages:

<CodeExample
  path="docs_projects/project_ask_ai_dagster/project_ask_ai_dagster/resources/scraper.py"
  language="python"
  startAfter="start_sitemap"
  endBefore="end_sitemap"
/>

The next function uses `BeautifulSoup` to scrape the primary content of individual pages. As with the GitHub resource, we will use the data as a Langchain `Document`.

<CodeExample
  path="docs_projects/project_ask_ai_dagster/project_ask_ai_dagster/resources/scraper.py"
  language="python"
  startAfter="start_scrape"
  endBefore="end_scrape"
/>

Finally, we can initialize the resource:

<CodeExample
  path="docs_projects/project_ask_ai_dagster/project_ask_ai_dagster/resources/scraper.py"
  language="python"
  startAfter="start_resource_init"
  endBefore="end_resource_init"
/>

## Next steps

- Continue this example with [vector-database](/examples/rag/vector-database)
