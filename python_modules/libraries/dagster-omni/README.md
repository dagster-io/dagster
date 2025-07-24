# dagster-omni

This library provides an integration between Dagster and Omni Analytics, allowing you to represent Omni content as Dagster assets.

## Features

- **Asset representation**: Models, workbooks, and queries from Omni are represented as Dagster assets
- **Lineage tracking**: Automatic dependency detection between Omni entities
- **Metadata integration**: Rich metadata from Omni content surfaces in Dagster
- **Extensible translator**: Customize how Omni content maps to Dagster assets

## Installation

```bash
pip install dagster-omni
```

## Quick Start

```python
from dagster import Definitions
from dagster_omni import OmniWorkspace, load_omni_asset_specs

# Configure your Omni workspace
omni_workspace = OmniWorkspace(
    workspace_url="https://myorg.omniapp.co",
    api_key="your-api-key-here"
)

# Load Omni content as Dagster assets
omni_assets = load_omni_asset_specs(omni_workspace)

defs = Definitions(
    assets=omni_assets,
    resources={"omni": omni_workspace}
)
```

## Supported Omni Entities

- **Models**: Data models that provide structured access to underlying data sources
- **Workbooks**: Analysis containers with queries and visualizations  
- **Queries**: Executable queries that produce analytical results

## Configuration

The `OmniWorkspace` resource requires:

- `workspace_url`: Your Omni workspace URL (e.g., `https://myorg.omniapp.co`)
- `api_key`: API key created by an Omni Organization Admin

## Custom Translators

You can customize how Omni content is represented in Dagster by extending the `DagsterOmniTranslator`:

```python
from dagster_omni import DagsterOmniTranslator, OmniTranslatorData

class MyOmniTranslator(DagsterOmniTranslator):
    def get_asset_key(self, content_type, properties):
        # Custom asset key logic
        return AssetKey([...])
        
    def get_description(self, content_type, properties):
        # Custom description logic
        return "..."

# Use your custom translator
omni_assets = load_omni_asset_specs(
    omni_workspace, 
    dagster_omni_translator=MyOmniTranslator()
)
```

## API Reference

See the [Dagster documentation](https://docs.dagster.io) for complete API reference.

## Development

This integration is in beta. See `DEVELOPMENT_NOTES.md` for implementation details and future roadmap.