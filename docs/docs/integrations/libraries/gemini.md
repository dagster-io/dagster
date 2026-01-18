---
title: Dagster & Gemini
sidebar_label: Gemini
sidebar_position: 1
description: The Gemini library allows you to easily interact with the Gemini REST API using the Gemini Python API to build AI steps into your Dagster pipelines. You can also log Gemini API usage metadata in Dagster Insights, giving you detailed observability on API call credit consumption.
tags: [community-supported, ai]
source: https://github.com/dagster-io/community-integrations/tree/main/libraries/dagster-gemini
pypi: https://pypi.org/project/dagster-gemini/
sidebar_custom_props:
  logo: images/integrations/gemini.svg
  community: true
partnerlink: https://ai.google.dev/docs
---

import CommunityIntegration from '@site/docs/partials/\_CommunityIntegration.md';

<CommunityIntegration />

<p>{frontMatter.description}</p>

When paired with Dagster assets, the resource automatically logs Gemini usage metadata in asset metadata.

## Installation

<PackageInstallInstructions packageName="dagster-gemini" />

## Example

<CodeExample path="docs_snippets/docs_snippets/integrations/gemini.py" language="python" />

## About Gemini

Gemini is Google's most capable AI model family, designed to be multimodal from the ground up. It can understand and combine different types of information like text, code, audio, images, and video. Gemini comes in different sizes optimized for different use cases, from the lightweight Gemini Nano for on-device tasks to the powerful Gemini Ultra for complex reasoning. The model demonstrates strong performance across language understanding, coding, reasoning, and creative tasks.
