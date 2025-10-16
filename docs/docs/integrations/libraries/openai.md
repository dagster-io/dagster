---
title: Dagster & OpenAI
sidebar_label: OpenAI
description: The OpenAI library allows you to easily interact with the OpenAI REST API using the OpenAI Python API to build AI steps into your Dagster pipelines. You can also log OpenAI API usage metadata in Dagster Insights, giving you detailed observability on API call credit consumption.
tags: [dagster-supported]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-openai
pypi: https://pypi.org/project/dagster-openai
sidebar_custom_props:
  logo: images/integrations/openai.svg
partnerlink: https://platform.openai.com/docs/introduction
---

<p>{frontMatter.description}</p>

Using this library's <PyObject section="libraries" module="dagster_openai" object="OpenAIResource" />, you can easily interact with the [OpenAI REST API](https://platform.openai.com/docs/introduction) via the [OpenAI Python API](https://github.com/openai/openai-python).

When used with Dagster's [asset definitions](/guides/build/assets/defining-assets), the resource automatically logs OpenAI usage metadata in [asset metadata](/guides/build/assets/metadata-and-tags).

## Getting started

Before you get started with the `dagster-openai` library, we recommend familiarizing yourself with the [OpenAI Python API library](https://github.com/openai/openai-python), which this integration uses to interact with the [OpenAI REST API](https://platform.openai.com/docs/introduction).

## Prerequisites

To get started, install the `dagster` and `dagster-openai` Python packages:

<PackageInstallInstructions packageName="dagster-openai" />

Note that you will need an OpenAI [API key](https://platform.openai.com/api-keys) to use the resource, which can be generated in your OpenAI account.

## Connecting to OpenAI

The first step in using OpenAI with Dagster is to tell Dagster how to connect to an OpenAI client using an OpenAI [resource](/guides/build/external-resources). This resource contains the credentials needed to interact with OpenAI API.

We will supply our credentials as environment variables by adding them to a `.env` file. For more information on setting environment variables in a production setting, see [Using environment variables and secrets](/guides/operate/configuration/using-environment-variables-and-secrets).

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

After materializing your asset, your OpenAI API usage metadata will be available in the **Events** and **Plots** tabs of your asset in the Dagster UI. If you are using [Dagster+](/deployment/dagster-plus), your usage metadata will also be available in [Dagster Insights](/guides/observe/insights).

## Using the OpenAI resource with ops

The OpenAI resource can also be used in [ops](/guides/build/ops).

:::note

Currently, the OpenAI resource doesn't (out-of-the-box) log OpenAI usage metadata when used in ops.

:::

<CodeExample
  startAfter="start_example"
  endBefore="end_example"
  path="docs_snippets/docs_snippets/integrations/openai/ops.py"
/>

## About OpenAI

OpenAI is a U.S. based artificial intelligence (AI) research organization with the goal of developing "safe and beneficial" artificial general intelligence, which it defines as "highly autonomous systems that outperform humans at most economically valuable work".
