# Graph-backed assets Example

If generating an asset involves multiple discrete computations, you can use graph-backed assets by separating each computation into an op and building a graph to combine your computations. Graph-backed assets are also useful if you have an existing graph that produces and consumes assets.

Check out [Graph-backed assets](https://docs.dagster.io/concepts/assets/software-defined-assets#graph-backed-assets) for more details.

## Getting started

```bash
dagster project from-example --name my-dagster-project --example feature_graph_backed_assets
```