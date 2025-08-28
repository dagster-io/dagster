# Dagster Plus API Architecture: CLI → REST → GraphQL Layering

## Overview

This package implements a three-layer architecture that provides a clean separation between the CLI interface and the Dagster Plus backend. The design follows a CLI → REST-esque Python API → GraphQL pattern, where each layer has distinct responsibilities and can evolve independently.

The goal is the provide an obvious mapping between the CLI and REST semantics, and to set us up to deploy an REST API on plus at some point in the future. REST is a much better interface for API consumption across organizations and for simple use cases.

This structure also makes this subsystem ideal for AI codegen to expand surface area.

## Architecture Layers

### 1. CLI Layer (`dagster_dg_cli/cli/`)

**Example:**

```bash
dg api deployment list --json
```

The API is modeled on `gh`, which is quite nice.

Every command has a `--json` for scripting use cases.

### 2. REST-like API Layer (`dagster_dg_cli/dagster_plus_api/`)

An intermediate abstraction layer that provides REST semantics.

**Structure:**

- `api/` - REST-like interface classes (e.g., `DgApiDeploymentApi`)
- `schemas/` - Pydantic models for type-safe request/response structures
- `graphql_adapter/` - Adapters that translate REST calls to GraphQL queries

## Request Flow Example

Here's how a request flows through the layers for `dg api deployment list`:

```
User Input: dg api deployment list
    ↓
CLI Layer: Click command handler
    - Validates arguments
    - Checks authentication (DagsterPlusCliConfig)
    ↓
API Layer: DgApiDeploymentApi.list_deployments()
    - Instantiates API client with config
    - Calls the appropriate method
    ↓
GraphQL Adapter: list_deployments_via_graphql()
    - Constructs GraphQL query: `fullDeployments`
    - Creates GraphQL client with auth headers
    ↓
GraphQL Client: DagsterPlusGraphQLClient
    - Sends authenticated HTTP request
    - Handles GraphQL response/errors
```

## Directory Structure

```
dagster_plus_api/
├── __init__.py
├── README.md          # This file
├── api/               # REST-like interface layer
│   ├── __init__.py
│   └── deployments.py # DgApiDeploymentApi class
├── graphql_adapter/   # GraphQL translation layer
│   ├── __init__.py
│   └── deployment.py  # GraphQL queries and adapters
└── schemas/           # Data models
    ├── __init__.py
    ├── CLAUDE.md      # Note about Pydantic usage
    └── deployment.py  # Deployment models
```

## Naming Conventions

All API classes follow the naming convention `DgPlusApi{Resource}Api` where `{Resource}` is the resource name in PascalCase:

- `DgApiDeploymentApi` for deployment operations
- `DgPlusApiMyResourceApi` for a hypothetical "my resource" operations

This convention ensures consistency and makes it clear that these classes are part of the Dagster Plus API layer.

## Adding New Endpoints

To add a new REST-like endpoint:

1. **Define the schema** in `schemas/`:

   ```python
   # schemas/my_resource.py
   class MyResource(BaseModel):
       id: int
       name: str
   ```

2. **Create the GraphQL adapter** in `graphql_adapter/`:

   ```python
   # graphql_adapter/my_resource.py
   def list_my_resources_via_graphql(config):
       # GraphQL query implementation
       pass
   ```

3. **Implement the API class** in `api/`:

   ```python
   # api/my_resources.py
   class DgPlusApiMyResourceApi:
       def list_resources(self):
           return list_my_resources_via_graphql(self.config)
   ```

4. **Add the CLI command** in the appropriate CLI module

5. Add test to enforce naming conventions and standards in the API layer in test_rest_compliance.

def get_all_api_classes():
"""Get all API classes to test."""
return [..., DgPlusApiMyResourceApi]
