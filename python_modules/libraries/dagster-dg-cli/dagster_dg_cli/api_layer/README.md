# Dagster Plus API Architecture

## QUICKSTART

Highly recommend you use prompting (and point the AI to thie file) to accomplish it.

We have the dagster plus schema checked in at python_modules/libraries/dagster-dg-cli/dagster_dg_cli/cli/plus/schema.graphql
which is critical to have in context. It should be combine to generate most of this code easily.

For a given noun you want to add to the system, have it interrgate the schema, ensure that you are picking
the most up-to-date queries, and then have it follow the patterns here for implementation and the testing

patterns in python_modules/libraries/dagster-dg-cli/dagster_dg_cli_tests/cli_tests/api_tests/README.md.

### Add a new API endpoint in 4 steps:

1. **Define the schema** in `schemas/my_resource.py`:

   ```python
   class MyResource(BaseModel):
       id: int
       name: str
   ```

2. **Create GraphQL adapter** in `graphql_adapter/my_resource.py`:

   ```python
   def list_my_resources_via_graphql(config):
       # GraphQL implementation
       pass
   ```

3. **Implement API class** in `api/my_resources.py`:

   ```python
   class DgApiMyResourceApi:
       def list_resources(self):
           return list_my_resources_via_graphql(self.config)
   ```

4. **Add CLI command** and **test it**:
   ```bash
   # Add to scenarios.yaml, record GraphQL, run tests
   dagster-dev dg-api-record my_resource
   pytest api_tests/my_resource_tests/
   ```

That's it! Your API endpoint is ready. 🚀

## Overview

This package implements a three-layer architecture: **CLI → REST-like API → GraphQL**

Each layer has distinct responsibilities:

- **CLI**: User interface and argument validation
- **REST API**: Business logic and REST semantics
- **GraphQL**: Backend communication

The goal is to provide an obvious mapping between CLI and REST semantics, setting us up to deploy a REST API on Dagster Plus in the future. REST is a better interface for API consumption across organizations.

## Architecture Layers

### 1. CLI Layer (`dagster_dg_cli/cli/api/`)

User-facing commands with consistent interface:

```bash
dg api deployment list --json
dg api asset list --json
dg api asset get my-asset --json
```

Every command supports `--json` for scripting. The API is modeled on GitHub's `gh` CLI.

### 2. REST-like API Layer (`dagster_plus_api/`)

Intermediate abstraction providing REST semantics:

```
dagster_plus_api/
├── api/               # REST-like interface classes
│   ├── deployments.py # DgApiDeploymentApi
│   └── asset.py       # DgApiAssetApi
├── schemas/           # Pydantic models
│   ├── deployment.py  # Deployment, DeploymentListResponse
│   └── asset.py       # Asset, AssetListResponse
└── graphql_adapter/   # GraphQL translation
    ├── deployment.py  # list_deployments_via_graphql()
    └── asset.py       # list_assets_via_graphql()
```

### 3. GraphQL Layer (`utils/plus/gql_client.py`)

Handles backend communication with authentication and error handling.

## Request Flow

Example flow for `dg api asset list`:

```
User: dg api asset list --json
    ↓
CLI Layer (cli/api/asset.py)
    - Parse arguments
    - Check authentication
    ↓
API Layer (api/asset.py)
    - DgApiAssetApi.list_assets()
    - Apply business logic
    ↓
GraphQL Adapter (graphql_adapter/asset.py)
    - list_assets_via_graphql()
    - Construct GraphQL query
    ↓
GraphQL Client
    - Send authenticated request
    - Return parsed response
```

## Naming Conventions

### API Classes

All API classes follow: `DgApi{Resource}Api`

- ✅ `DgApiDeploymentApi`
- ✅ `DgApiAssetApi`
- ✅ `DgApiRunApi`
- ❌ `DgPlusApiResourceApi` (old convention)

### Methods

REST-style method naming:

- `list_*` - Return multiple items
- `get_*` - Return single item by ID
- `create_*` - Create new resource
- `update_*` - Modify existing resource
- `delete_*` - Remove resource

### Schemas

Pydantic models for type safety:

- `{Resource}` - Single resource model
- `{Resource}ListResponse` - List response with pagination

## Testing Strategy

### Add a new API endpoint test in 3 steps:

1. **Add test scenario** in `api_tests/{domain}_tests/scenarios.yaml`:

   ```yaml
   success_list_assets:
     command: "dg api asset list --json"
   ```

2. **Record GraphQL responses:**

   ```bash
   dagster-dev dg-api-record asset --recording success_list_assets
   ```

3. **Generate snapshots:**
   ```bash
   pytest api_tests/asset_tests/ --snapshot-update
   ```

### Update tests when logic changes:

```bash
# Re-record responses (when API behavior changes)
dagster-dev dg-api-record asset --recording success_list_assets

# Update snapshots (when CLI output changes)
pytest api_tests/asset_tests/ --snapshot-update
```

For detailed testing documentation, troubleshooting, and advanced workflows, see [api_tests/README.md](../../../dagster_dg_cli_tests/cli_tests/api_tests/README.md).

### Compliance testing

Tests automatically validate:

- Method naming conventions
- Type signatures (primitives + Pydantic only)
- Response consistency
- Parameter patterns

## Adding New Resources

### Step 1: Define Schema

```python
# schemas/run.py
from pydantic import BaseModel

class Run(BaseModel):
    id: str
    status: str
    started_at: str

class RunListResponse(BaseModel):
    runs: list[Run]
    cursor: str | None = None
```

### Step 2: Create GraphQL Adapter

```python
# graphql_adapter/run.py
def list_runs_via_graphql(config, limit=None):
    query = """
    query {
        runs(limit: $limit) {
            nodes { id status startedAt }
            cursor
        }
    }
    """
    # Execute and transform response
```

### Step 3: Implement API Class

```python
# api/runs.py
class DgApiRunApi:
    def __init__(self, config):
        self.config = config

    def list_runs(self, limit: int = None) -> RunListResponse:
        return list_runs_via_graphql(self.config, limit)
```

### Step 4: Add CLI Command

```python
# cli/api/run.py
@click.group("run")
def run_group():
    """Manage runs."""
    pass

@run_group.command("list")
@click.option("--json", is_flag=True)
def list_runs(json):
    api = DgApiRunApi(config)
    response = api.list_runs()
    # Output handling
```

### Step 5: Add Tests

1. Add to `test_rest_compliance.py`:

   ```python
   def get_all_api_classes():
       return [..., DgApiRunApi]
   ```

2. Create `api_tests/run_tests/scenarios.yaml`

3. Record fixtures and run tests

## Best Practices

1. **Type Safety**: Always use Pydantic models for request/response
2. **Error Handling**: Let GraphQL errors bubble up naturally
3. **Pagination**: Include cursor in list responses
4. **Testing**: Record real GraphQL responses for fixtures
5. **Documentation**: Update this README when adding resources

## Common Patterns

### Pagination

```python
class ResourceListResponse(BaseModel):
    resources: list[Resource]
    cursor: str | None = None
    has_more: bool = False
```

### Error Responses

GraphQL errors are automatically handled by the client and converted to appropriate CLI output.

### Authentication

Authentication is handled by `DagsterPlusCliConfig` and passed through all layers automatically.
