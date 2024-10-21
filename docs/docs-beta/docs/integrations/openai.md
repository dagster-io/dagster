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

<CodeExample filePath="integrations/openai.py" language="python" />

### About OpenAI

OpenAI is a U.S. based artificial intelligence (AI) research organization with the goal of developing "safe and beneficial" artificial general intelligence, which it defines as "highly autonomous systems that outperform humans at most economically valuable work".
