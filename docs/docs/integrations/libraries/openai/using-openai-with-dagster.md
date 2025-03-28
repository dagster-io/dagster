---
title: 'OpenAI & Dagster'
description: 'The dagster-openai library provides the ability to build OpenAI pipelines with Dagster and log OpenAI API usage metadata in Dagster Insights.'
---

The `dagster-openai` library allows you to build OpenAI pipelines with Dagster and log OpenAI API usage metadata in [Dagster Insights](/dagster-plus/features/insights).

Using this library's <PyObject section="libraries" module="dagster_openai" object="OpenAIResource" />, you can easily interact with the [OpenAI REST API](https://platform.openai.com/docs/introduction) via the [OpenAI Python API](https://github.com/openai/openai-python).

When used with Dagster's [asset definitions](/guides/build/assets/defining-assets), the resource automatically logs OpenAI usage metadata in [asset metadata](/guides/build/assets/metadata-and-tags/).

## Getting started

Before you get started with the `dagster-openai` library, we recommend familiarizing yourself with the [OpenAI Python API library](https://github.com/openai/openai-python), which this integration uses to interact with the [OpenAI REST API](https://platform.openai.com/docs/introduction).

## Prerequisites

To get started, install the `dagster` and `dagster-openai` Python packages:

```bash
pip install dagster dagster-openai
```

Note that you will need an OpenAI [API key](https://platform.openai.com/api-keys) to use the resource, which can be generated in your OpenAI account.

## Connecting to OpenAI

The first step in using OpenAI with Dagster is to tell Dagster how to connect to an OpenAI client using an OpenAI [resource](/guides/build/external-resources/). This resource contains the credentials needed to interact with OpenAI API.

We will supply our credentials as environment variables by adding them to a `.env` file. For more information on setting environment variables in a production setting, see [Using environment variables and secrets](/guides/deploy/using-environment-variables-and-secrets).

```bash
# .env

OPENAI_API_KEY=...
```

Then, we can instruct Dagster to authorize the OpenAI resource using the environment variables:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/openai/resource.py"
  startAfter="start_example"
  endBefore="end_example"
/>

## Using the OpenAI resource with assets

The OpenAI resource can be used in assets in order to interact with the OpenAI API. Note that in this example, we supply our credentials as environment variables directly when instantiating the <PyObject section="definitions" module="dagster" object="Definitions" /> object.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/openai/assets.py"
  startAfter="start_example"
  endBefore="end_example"
/>

After materializing your asset, your OpenAI API usage metadata will be available in the **Events** and **Plots** tabs of your asset in the Dagster UI. If you are using [Dagster+](/dagster-plus), your usage metadata will also be available in [Dagster Insights](/dagster-plus/features/insights). {/* Refer to the [Viewing and materializing assets in the UI guide](https://docs.dagster.io/guides/build/assets/defining-assets#viewing-and-materializing-assets-in-the-ui) for more information. */}

## Using the OpenAI resource with ops

The OpenAI resource can also be used in [ops](/guides/build/ops/).

:::note

Currently, the OpenAI resource doesn't (out-of-the-box) log OpenAI usage metadata when used in ops.

:::

<CodeExample
  startAfter="start_example"
  endBefore="end_example"
  path="docs_snippets/docs_snippets/integrations/openai/ops.py"
/>
