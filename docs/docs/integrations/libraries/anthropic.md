---
layout: Integration
status: published
name: Anthropic
title: Dagster & Anthropic
sidebar_label: Anthropic
excerpt: Integrate Anthropic calls into your Dagster pipelines, without breaking the bank.
partnerlink: https://docs.anthropic.com/en/api/getting-started
categories:
  - Other
enabledBy:
enables:
tags: [dagster-supported]
sidebar_custom_props:
  logo: images/integrations/anthropic.svg
---

The `dagster-anthropic` library allows you to easily interact with the Anthropic REST API using the Anthropic Python API to build AI steps into your Dagster pipelines. You can also log Anthropic API usage metadata in Dagster Insights, giving you detailed observability on API call credit consumption.

When paired with Dagster assets, the resource automatically logs Anthropic usage metadata in asset metadata.

### Installation

```bash
pip install dagster dagster-anthropic
```

### Example

<CodeExample path="docs_beta_snippets/docs_beta_snippets/integrations/anthropic.py" language="python" />

### About Anthropic

Anthropic is an AI research company focused on developing safe and ethical AI systems. Their flagship product, Claude, is a language model known for its strong capabilities in analysis, writing, and coding tasks while maintaining high standards of truthfulness and safety.
