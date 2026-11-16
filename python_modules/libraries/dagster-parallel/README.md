# Dagster Parallel Search

Use this resource to collect URLs and short passages from public sites as an
asset. For example, a team tracking upstream dependency changes can put release
notes into a review queue even when it does not know the page URLs in advance.

From a Dagster source checkout, install the library with
`uv sync --group test --project python_modules/libraries/dagster-parallel`.

Register the resource with the endpoint shown below. The asset sends its
objective and keyword queries to the [keyless Parallel MCP service](https://docs.parallel.ai/integrations/mcp/installation)
when it materializes. Use public search terms and keep private asset data out of
them. The keyless service is subject to rate limits.

Save the example as `definitions.py` at the root of the Dagster checkout and run:

```sh
uv run --project python_modules/libraries/dagster-parallel \
  dagster asset materialize -f definitions.py --select dagster_release_sources
```

The asset returns rows for downstream review. It keeps hits for the requested
Dagster release that include an excerpt.

```python
from urllib.parse import urlsplit

import dagster as dg
from dagster_parallel import ParallelSearchResource


@dg.asset
async def dagster_release_sources(parallel_search: ParallelSearchResource):
    results = await parallel_search.search(
        objective=(
            "Find the official Dagster 1.13.0 release notes in the "
            "dagster-io/dagster GitHub repository."
        ),
        search_queries=[
            "site:github.com Dagster 1.13.0 release notes",
            "site:docs.dagster.io Dagster 1.13 release notes",
        ],
    )
    rows = []
    for result in results:
        source = urlsplit(result.url)
        if (
            source.scheme != "https"
            or source.netloc != "github.com"
            or source.path != "/dagster-io/dagster/releases/tag/1.13.0"
        ):
            continue
        excerpt = next((passage for passage in result.excerpts if passage.strip()), "")
        if excerpt:
            rows.append(
                {"url": result.url, "title": result.title, "excerpt": excerpt.strip()[:500]}
            )
    return rows


defs = dg.Definitions(
    assets=[dagster_release_sources],
    resources={"parallel_search": ParallelSearchResource(endpoint="https://mcp.parallel.ai/mcp")},
)
```
