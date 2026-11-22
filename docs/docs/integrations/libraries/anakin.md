---
title: Dagster & Anakin
sidebar_label: Anakin
sidebar_position: 1
description: The Anakin resource turns web pages into Dagster assets. Scrape pages to markdown or structured JSON, crawl sites, run AI web search, and run prebuilt site actions from your assets and ops.
tags: [community-supported, etl]
source: https://github.com/Anakin-Inc/dagster-anakin
pypi: https://pypi.org/project/dagster-anakin
sidebar_custom_props:
  logo: images/integrations/anakin.png
  community: true
partnerlink: https://anakin.io
---

import CommunityIntegration from '@site/docs/partials/\_CommunityIntegration.md';

<CommunityIntegration />

<p>{frontMatter.description}</p>

For more information, see the [dagster-anakin GitHub repository](https://github.com/Anakin-Inc/dagster-anakin) and the [Anakin documentation](https://anakin.io/docs).

## Installation

<PackageInstallInstructions packageName="dagster-anakin" />

## Example

Set `ANAKIN_API_KEY` in the environment where your code location runs. `AnakinResource()` reads it at run time.

```python
import dagster as dg
from dagster_anakin import AnakinResource, build_anakin_scrape_asset

# Re-scrapes the page to markdown on every materialization.
dagster_blog = build_anakin_scrape_asset("dagster_blog", "https://dagster.io/blog")


@dg.asset(kinds={"anakin"})
def blog_posts(anakin: AnakinResource) -> dict:
    """Structured post data extracted from the page with AI."""
    doc = anakin.scrape_url(
        "https://dagster.io/blog",
        output_schema={
            "type": "object",
            "properties": {
                "posts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"title": {"type": "string"}, "url": {"type": "string"}},
                    },
                }
            },
        },
    )
    return doc["generated_json"]


defs = dg.Definitions(
    assets=[dagster_blog, blog_posts],
    # Reads ANAKIN_API_KEY from the environment at run time.
    resources={"anakin": AnakinResource()},
)
```

`build_anakin_scrape_asset` records the URL, the Anakin job ID, whether the result came from cache, and a markdown preview as materialization metadata, so you can read the page in the Dagster UI.

## About Anakin

[Anakin](https://anakin.io) is a web data API. It scrapes and crawls websites, runs AI web search, and returns clean markdown or structured JSON for data pipelines and AI agents.
