# dagster-rest-resources

This library exposes Dagster functionality as REST-style resources, primarily by wrapping Dagster's graphql API, with some exceptions (e.g., `artifact` makes requests directly to s3 and there may be other exceptions in the future).

## Architecture

The REST api is organized into `api`, classes that provide the actual REST-style CRUD operation semantics, `schemas`, pydantic models representing requests and responses, and `graphql_adapter`, classes that translate the REST requests into graphql queries, and the graphql responses into REST responses.
There is also a `gql_client` for actually sending the requests.

```
dagster-rest-resources/
├── api/               # REST-like interface classes
│   ├── deployments.py # DgApiDeploymentApi
│   └── asset.py       # DgApiAssetApi
├── schemas/           # Pydantic models
│   ├── deployment.py  # Deployment, DeploymentListResponse
│   └── asset.py       # Asset, AssetListResponse
├── graphql_adapter/   # GraphQL translation
│   ├── deployment.py  # list_deployments_via_graphql()
│   └── asset.py       # list_assets_via_graphql()
└── gql_client.py      # makes the graphql calls
```

## Request Flow

```
API Layer (/api/asset.py)
    - DgApiAssetApi.list_assets()
    - Apply business logic
    ↓
GraphQL Adapter (/graphql_adapter/asset.py)
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

Each resource should be added to the general compliance tests and given individual unit tests.

### Compliance Tests

Tests automatically validate:

- Method naming conventions
- Type signatures
- Response consistency
- Parameter patterns

## Adding A New Resource

In this example, we'll be implementing a `run` resource.

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

## Best Practices

### Type Safety

Always use Pydantic models for request/response.

### Error Responses

GraphQL errors are turned into python errors and bubbled up.

### Authentication

Authentication is handled by the caller of the library and and passed through.

### Pagination

```python
class ResourceListResponse(BaseModel):
    resources: list[Resource]
    cursor: str | None = None
    has_more: bool = False
```
