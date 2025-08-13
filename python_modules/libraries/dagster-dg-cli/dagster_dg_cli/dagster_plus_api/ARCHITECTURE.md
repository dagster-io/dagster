# Dagster Plus API Architecture

## Overview

This module provides a clean API interface for Dagster Plus operations, with a clear separation between the API contract and its implementation.

## Structure

```
dagster_plus_api/
├── api/                          # REST-like API interface (stable contract)
│   └── v1/
│       └── endpoints/
│           ├── deployments.py   # Deployment operations
│           ├── runs.py          # Pipeline run operations (future)
│           └── secrets.py       # Secret management (future)
├── schemas/                      # Pydantic models (shared with future FastAPI)
│   ├── deployment.py            # Deployment schemas
│   ├── run.py                   # Run schemas (future)
│   └── secret.py               # Secret schemas (future)
└── graphql_adapter/             # Current GraphQL implementation (replaceable)
    ├── deployment.py            # GraphQL queries for deployments
    ├── run.py                   # GraphQL queries for runs (future)
    └── secret.py               # GraphQL queries for secrets (future)
```

## Design Principles

1. **Stable API Interface**: The `api/v1/endpoints/` layer defines the public interface that CLI commands use. This interface will remain stable.

2. **Implementation Flexibility**: The `graphql_adapter/` contains the current GraphQL implementation. This can be replaced with REST calls without changing the API interface.

3. **Shared Schemas**: The `schemas/` directory contains Pydantic models that will be shared with the future FastAPI server.

4. **FastAPI Alignment**: The structure mirrors standard FastAPI patterns:
   - `api/v1/endpoints/` → FastAPI routers
   - `schemas/` → Pydantic models for validation
   - Method signatures match REST patterns (GET, POST, etc.)

## Usage Example

```python
# CLI layer uses the API interface
from dagster_dg_cli.dagster_plus_api.api.v1.endpoints.deployments import DeploymentAPI

api = DeploymentAPI(config)
deployments = api.list_deployments()  # Returns DeploymentList schema
```

## Migration Path

When migrating from GraphQL to REST:

1. Keep `api/v1/endpoints/` unchanged
2. Keep `schemas/` unchanged
3. Replace `graphql_adapter/` with REST implementation
4. CLI commands continue working without modification

## Adding New Endpoints

1. Define schemas in `schemas/<resource>.py`
2. Create API interface in `api/v1/endpoints/<resource>.py`
3. Implement GraphQL adapter in `graphql_adapter/<resource>.py`
4. Use from CLI in `cli/plus/api/<resource>.py`
