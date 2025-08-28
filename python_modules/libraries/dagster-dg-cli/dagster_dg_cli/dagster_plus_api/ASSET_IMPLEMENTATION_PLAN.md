# Implementation Plan: DgPlusApi Asset Endpoints

## Overview

Implement asset endpoints using cursor-based pagination with the DgPlusApi naming convention, following the established three-layer architecture pattern from the existing deployment implementation.

## CLI API Design

### Commands

```bash
# List assets with pagination
dg plus api asset list [--limit <n>] [--cursor <cursor>] [--json]

# Get specific asset details
dg plus api asset view <asset-key> [--json]
```

### Examples

```bash
# List first 50 assets
dg plus api asset list --limit 50

# Continue pagination with cursor
dg plus api asset list --limit 50 --cursor "eyJrZXkiOiJbXCJteVwiLFwiYXNzZXRcIl0ifQ=="

# Get specific asset (slash-separated format)
dg plus api asset view "my/asset/key"
dg plus api asset view "foo/bar"
```

## File Structure to Create

```
dagster_plus_api/
├── schemas/
│   └── asset.py                    # New file: DgPlusApiAsset models
├── graphql_adapter/
│   └── asset.py                    # New file: GraphQL queries and adapters
├── api/
│   └── asset.py                    # New file: DgPlusApiAssetAPI class
```

## Implementation Tasks

### 1. Create Asset Schema Models (`schemas/asset.py`)

```python
from typing import List, Optional
from pydantic import BaseModel

class DgPlusApiAsset(BaseModel):
    """Asset resource model."""
    id: str
    assetKey: str              # "my/asset/key"
    assetKeyParts: List[str]   # ["my", "asset", "key"]
    description: Optional[str]
    groupName: str
    kinds: List[str]
    metadataEntries: List[dict]

    class Config:
        from_attributes = True

class DgPlusApiAssetList(BaseModel):
    """GET /api/assets response."""
    items: List[DgPlusApiAsset]
    cursor: Optional[str]      # Next cursor for pagination
    hasMore: bool             # Whether more results exist
```

### 2. Create GraphQL Adapter (`graphql_adapter/asset.py`)

```python
# Two GraphQL queries needed:
# 1. ASSET_RECORDS_QUERY - for pagination (assetRecordsOrError)
# 2. ASSET_NODES_QUERY - for metadata (assetNodes)

def list_dg_plus_api_assets_via_graphql(config, limit=None, cursor=None):
    """Two-step approach:
    1. Use assetRecordsOrError for paginated asset keys
    2. Use assetNodes to fetch metadata for those keys
    3. Combine and transform data
    """

def get_dg_plus_api_asset_via_graphql(config, asset_key_parts: List[str]):
    """Single asset fetch using assetNodes with specific assetKey."""
```

### 3. Create API Class (`api/asset.py`)

```python
class DgPlusApiAssetAPI:
    def __init__(self, config: DagsterPlusCliConfig):
        self.config = config

    def list_assets(self, limit: Optional[int] = 50, cursor: Optional[str] = None) -> DgPlusApiAssetList:
        """List assets with cursor-based pagination."""

    def get_asset(self, asset_key: str) -> DgPlusApiAsset:
        """Get single asset by slash-separated key (e.g., 'foo/bar')."""
        # Parse "foo/bar" to ["foo", "bar"]
```

### 4. Key Implementation Details

#### Asset Key Format Handling

- **Input format**: `"foo/bar"` (slash-separated string)
- **Parse**: Split by `/` to get `["foo", "bar"]` for GraphQL
- **Output**: Both `assetKey: "foo/bar"` and `assetKeyParts: ["foo", "bar"]`
- **TODO**: Handle escaping for keys containing `/` characters

#### GraphQL Integration Pattern

- **Step 1**: Use `assetRecordsOrError(cursor, limit)` for paginated keys
- **Step 2**: Use `assetNodes(assetKeys: [...])` for metadata
- **Fields to fetch**: `id, assetKey, description, groupName, kinds, metadataEntries`

#### Pagination Implementation

- **Default limit**: 50 assets per page
- **Max limit**: 1000 (following existing patterns)
- **Cursor**: Opaque string returned by GraphQL
- **hasMore**: `true` when `assets.length === limit`

### 5. Future Enhancements (TODOs)

- **Asset Selection Syntax**: Add `--selection <expression>` parameter
- **Complex Queries**: Support expressions like `key_substring:my_asset and group:analytics`
- **Escaping**: Handle asset keys containing `/` characters properly

### 6. Testing Requirements

- Add to existing API compliance tests
- Test cursor-based pagination edge cases
- Test asset key parsing and transformation
- Test error handling for invalid keys/cursors

### 7. Follow Existing Patterns

- Use same error handling as `deployment.py`
- Follow same GraphQL client patterns
- Use same import structure and typing
- Maintain consistency with `DeploymentAPI` class structure

This plan provides a complete specification for implementing asset endpoints that another agent can execute by following the established patterns in the codebase.
