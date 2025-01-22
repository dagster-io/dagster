---
title: "OpenAI & Dagster | Dagster Docs"
description: "The dagster-openai library provides the ability to build OpenAI pipelines with Dagster and log OpenAI API usage metadata in Dagster Insights."
---

:::

This feature is considered **experimental**

:::

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

```python startafter=start_example endbefore=end_example file=/integrations/openai/resource.py
from dagster_openai import OpenAIResource

from dagster import EnvVar

# Pull API key from environment variables
openai = OpenAIResource(
    api_key=EnvVar("OPENAI_API_KEY"),
)
```

## Using the OpenAI resource with assets

The OpenAI resource can be used in assets in order to interact with the OpenAI API. Note that in this example, we supply our credentials as environment variables directly when instantiating the <PyObject section="definitions" module="dagster" object="Definitions" /> object.

{/* TODO convert to <CodeExample> */}
```python startafter=start_example endbefore=end_example file=/integrations/openai/assets.py
from dagster_openai import OpenAIResource

from dagster import AssetExecutionContext, Definitions, EnvVar, asset, define_asset_job


@asset(compute_kind="OpenAI")
def openai_asset(context: AssetExecutionContext, openai: OpenAIResource):
    with openai.get_client(context) as client:
        client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say this is a test."}],
        )


openai_asset_job = define_asset_job(name="openai_asset_job", selection="openai_asset")

defs = Definitions(
    assets=[openai_asset],
    jobs=[openai_asset_job],
    resources={
        "openai": OpenAIResource(api_key=EnvVar("OPENAI_API_KEY")),
    },
)
```

After materializing your asset, your OpenAI API usage metadata will be available in the **Events** and **Plots** tabs of your asset in the Dagster UI. If you are using [Dagster+](/dagster-plus), your usage metadata will also be available in [Dagster Insights](/dagster-plus/features/insights). {/* Refer to the [Viewing and materializing assets in the UI guide](https://docs.dagster.io/guides/build/assets/defining-assets#viewing-and-materializing-assets-in-the-ui) for more information. */}

## Using the OpenAI resource with ops

The OpenAI resource can also be used in [ops](/guides/build/ops).

:::note

Currently, the OpenAI resource doesn't (out-of-the-box) log OpenAI usage metadata when used in ops.

:::

{/* TODO convert to <CodeExample> */}
```python startafter=start_example endbefore=end_example file=/integrations/openai/ops.py
from dagster_openai import OpenAIResource

from dagster import Definitions, EnvVar, GraphDefinition, OpExecutionContext, op


@op
def openai_op(context: OpExecutionContext, openai: OpenAIResource):
    with openai.get_client(context) as client:
        client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say this is a test"}],
        )


openai_op_job = GraphDefinition(name="openai_op_job", node_defs=[openai_op]).to_job()

defs = Definitions(
    jobs=[openai_op_job],
    resources={
        "openai": OpenAIResource(api_key=EnvVar("OPENAI_API_KEY")),
    },
)
```
