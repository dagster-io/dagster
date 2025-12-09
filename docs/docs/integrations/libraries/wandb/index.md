---
title: Dagster & Weights & Biases
sidebar_label: Weights & Biases
sidebar_position: 1
description: Use Dagster and Weights & Biases (W&B) to orchestrate your MLOps pipelines and maintain ML assets.
tags: [community-supported]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-wandb
pypi: https://pypi.org/project/dagster-wandb
sidebar_custom_props:
  logo: images/integrations/wandb.svg
  community: true
partnerlink: https://wandb.ai/
---

import CommunityIntegration from '@site/docs/partials/\_CommunityIntegration.md';

<CommunityIntegration />

<p>{frontMatter.description}</p>

The integration with W&B makes it easy within Dagster to:

- use and create W&B Artifacts
- use and create Registered Models in W&B Model Registry
- run training jobs on dedicated compute using W&B Launch
- use the Weights & Biases client in ops and assets

The W&B Dagster integration provides a W&B-specific Dagster resource and I/O Manager:

- `wandb_resource`: a Dagster resource used to authenticate and communicate to the W&B API.
- `wandb_artifacts_io_manager`: a Dagster I/O Manager used to consume W&B Artifacts.

## Installation

To use this integration you will need a Weights and Biases account. Then you will need a W&B API Key, a W&B entity (user or team), and a W&B project. Full installation details can be found on [the Weights and Biases website here](https://docs.wandb.ai/guides/integrations/other/dagster).

**Note** that Weights & Biases do offer a free cloud account for personal (non-corporate) use. Check out their [pricing page](https://wandb.ai/site/pricing) for details.

## Example

A complete tutorial can be found on [the Weights and Biases website here](https://docs.wandb.ai/guides/integrations/other/dagster).

## About Weights & Biases

[Weights & Biases](https://wandb.ai/site) makes it easy to track your experiments, manage & version your data, and collaborate with your team so you can focus on building the best machine learning models.
