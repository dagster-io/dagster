# Dagster Parallel Search

Use this resource to collect URLs and short passages from public sites as an
asset. For example, a team tracking upstream dependency changes can put release
notes into a review queue even when it does not know the page URLs in advance.

From a Dagster source checkout, install the library with
`uv sync --group test --project python_modules/libraries/dagster-parallel`.

Register the resource with the exact endpoint shown below. The asset sends its
objective and keyword queries to the keyless Parallel MCP service when it
materializes. Use public search terms and keep private asset data out of them.
The keyless service is subject to rate limits.

Save this as `definitions.py` and run `dagster asset materialize -f definitions.py --select dagster_release_sources`.
The asset returns rows for downstream review. Results are ranked search hits, so
the example checks the repository and path before retaining a source.

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
            source.scheme == "https"
            and source.netloc == "github.com"
            and source.path.startswith("/dagster-io/dagster/releases/tag/")
            and result.excerpts
        ):
            rows.append(
                {"url": result.url, "title": result.title, "excerpt": result.excerpts[0][:500]}
            )
    return rows


defs = dg.Definitions(
    assets=[dagster_release_sources],
    resources={"parallel_search": ParallelSearchResource(endpoint="https://mcp.parallel.ai/mcp")},
)
```
