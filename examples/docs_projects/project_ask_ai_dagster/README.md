# Dagster Support Bot Rag Application

## Project Overview

This project implements a support bot using Retrieval-Augmented Generation (RAG) with OpenAI and Pinecone vector database, orchestrated using Dagster for reliable data ingestion and retrieval pipelines.

### Example Asset Lineage

![Screenshot Dagster Lineage](_static/screenshot_dagster_lineage.svg)

## Getting started

Install the project dependencies:

```bash
uv sync
```

Run Dagster:

```bash
dg dev
```

Open http://localhost:3000 in your browser.

## References

Dagster

- [Dagster Docs](https://docs.dagster.io/)
- [Dagster Docs: DuckDB](https://docs.dagster.io/_apidocs/libraries/dagster-duckdb)
- [Dagster Docs: OpenAI Integration](https://docs.dagster.io/integrations/openai)

Pinecone

- [Pinecone](https://www.pinecone.io/)

OpenAI

- [OpenAI Fine-Tuning](https://platform.openai.com/docs/guides/fine-tuning)
- [OpenAI Cookbook: How to fine-tune chat models](https://cookbook.openai.com/examples/how_to_finetune_chat_models)
- [OpenAI Cookbook: Data preparation and analysis for chat model fine-tuning](https://cookbook.openai.com/examples/chat_finetuning_data_prep)
