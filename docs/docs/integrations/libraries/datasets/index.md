---
title: Dagster & HF Datasets
sidebar_label: HF Datasets
sidebar_position: 1
description: Use Dagster and Hugging Face Datasets to orchestrate data pipelines, materialize dataset assets, track metadata and lineage, and publish datasets to the Hub.
tags: [community-supported, datasets, metadata, streaming]
source: https://github.com/dagster-io/community-integrations/tree/main/libraries/dagster-hf-datasets
pypi: https://pypi.org/project/dagster_hf_datasets/
sidebar_custom_props:
  logo: images/integrations/hf_datasets.svg
  community: true
partnerlink: https://github.com/huggingface/datasets
canonicalUrl: '/integrations/libraries/hf-datasets'
slug: '/integrations/libraries/hf-datasets'
---

import CommunityIntegration from '@site/docs/partials/_CommunityIntegration.md';

<CommunityIntegration />

<p>{frontMatter.description}</p>

The integration with HF Datasets makes it easy within Dagster to:

- Load a Hugging Face dataset as a Dagster asset with metadata.
- Stream large datasets efficiently in runtime-only mode
- Capture metadata and lineage for improved observability
- Build multi-asset pipelines that support dataset splits.
- Publish processed datasets back to the Hugging Face Hub.

## Installation

<PackageInstallInstructions packageName="dagster-hf-datasets" />

## Example

This example illustrates the working of a dataset pipeline for transformation, split-aware assets, and Hugging Face Hub publishing.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/hf_datasets/dataset_pipeline_example.py"
  language="python"
/>

## About HF Datasets

[HF Datasets](https://huggingface.co/docs/datasets/index) is a library for accessing, processing, and sharing AI datasets for Audio, Computer Vision, and Natural Language Processing (NLP) tasks.
