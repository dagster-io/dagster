# Local to Production Development Flow

This example contains a set of assets that can be run in various environments (local, production, etc.).
It utilizes dagster's run configuration system and swappable resources to ensure that production data
is not overwritten by local developers. It also contains tests that provide mock data to assets to ensure
correctness.

To follow along with this example, you can read this [guide](https://docs.dagster.io/guides/dagster/local-to-production-tutorial).

## Setup
To run this example locally

```
# Install the example so that it will be on your Python path
pip install -e .

# Load it in the web UI
dagit -w workspace.yaml
```