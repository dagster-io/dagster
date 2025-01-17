# Dagster Support Bot Rag Application

## Project Overview

This project implements a support bot using Retrieval-Augmented Generation (RAG) with OpenAI and Pinecone vector database, orchestrated using Dagster for reliable data ingestion and retrieval pipelines.

## Features

- RAG-Powered Support Bot: Leverages advanced retrieval and generation techniques
- Pinecone Vector Database: Efficient semantic search and document retrieval
- Dagster Orchestration: Robust pipeline management for ingestion and retrieval processes
- OpenAI Integration: Powerful language model for generating responses

## Data Sources

1. Dagster Github Repository Issues
2. Dagster Github Repository Discussions
3. Dagster Docs Website

## Prerequisites

- Python 3.8+
- OpenAI API Key
- Pinecone Account and API Key
- Dagster
- Webscraping

## Environment variables

For the pipeline to be able to pull issues and discussions from GitHub, you'll need set your GitHub credentials, and to store data in Pinecone, you will need to set your API key. This is done through environment variables:
OPENAI_API_KEY=[Instructions](https://platform.openai.com/docs/quickstart)
DOCS_SITEMAP=[Docs Sitemap](https://docs.dagster.io/sitemap.xml)
PINECONE_API_KEY=[Instructions](https://docs.pinecone.io/guides/get-started/quickstart)
GITHUB_TOKEN=[Instructions](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

## Ingestion Pipeline

The ingestion pipeline handles:

- Document loading
- Text splitting
- Embedding generation
- Vector storage in Pinecone

## Retrieval Pipeline

The retrieval pipeline manages:

- Query embedding
- Semantic search in Pinecone
- Response generation with OpenAI
