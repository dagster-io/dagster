# Local to Production Development Flow

This example contains a set of assets that can be run in various environments (local, production, etc.).
It utilizes dagster's run configuration system and swappable resources to ensure that production data
is not overwritten by local developers. It also contains tests that provide mock data to assets to ensure
correctness.

To follow along with this example, you can read this [guide](https://docs.dagster.io/guides/dagster/transitioning-data-pipelines-from-development-to-production).

## Setup
To run this example locally

```
dagster project from-example --name my-dagster-project --example development_to_production
cd my-dagster-project
pip install -e ".[dev]"

# Load it in the web UI
dagit -w workspace.yaml
```