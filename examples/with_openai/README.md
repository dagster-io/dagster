# Using Dagster with OpenAI & LangChain

This directory contains a pipeline leveraging Dagster, [OpenAI](https://openai.com/) and [LangChain](https://www.langchain.com/) to create a support bot. This pipeline is discussed in our [blog post](https://dagster.io/blog/building-cost-effective-ai-pipelines-openai-langchain-dagster).

For more information about using OpenAI with Dagster, visit our [OpenAI integration page](https://docs.dagster.io/integrations/openai).

## Getting started

Bootstrap your own Dagster project with this example:

```bash
dagster project from-example --name my-dagster-project --example with_openai
```

To install this example and its Python dependencies, run:

```bash
pip install -e ".[dev]"
```

Once you've done this, you can run:

```
dagster dev
```
