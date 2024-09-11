---
layout: Integration
status: published
name: OpenAI
title: Dagster & OpenAI
sidebar_label: OpenAI
excerpt: Integrate OpenAI calls into your Dagster pipelines, without breaking the bank.
date: 2024-03-12
apireflink: https://platform.openai.com/docs/introduction
docslink: https://docs.dagster.io/integrations/openai
partnerlink: 
logo: /integrations/openai.svg
categories:
  - Other
enabledBy:
enables:
---

### About this integration

The `dagster-openai` library allows you to easily interact with the OpenAI REST API using the OpenAI Python API to build AI steps into your Dagster pipelines. You can also log OpenAI API usage metadata in Dagster Insights, giving you detailed observability on API call credit consumption.

When paired with Dagster assets, the resource automatically logs OpenAI usage metadata in asset metadata.

### Installation

```bash
pip install dagster dagster-openai
```

### Example

```python
from dagster_openai import OpenAIResource

from dagster import (
    AssetExecutionContext,
    Definitions,
    EnvVar,
    asset,
    define_asset_job,
)


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

### About OpenAI

OpenAI is a U.S. based artificial intelligence (AI) research organization with the goal of developing "safe and beneficial" artificial general intelligence, which it defines as "highly autonomous systems that outperform humans at most economically valuable work".
