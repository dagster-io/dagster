# Dagster Omni Integration - Development Notes

## Overview
This document captures the research, planning, and implementation approach for the Dagster Omni BI integration. This integration creates discrete Dagster assets for entities in Omni, displays lineage between dependent objects, and potentially upstream data sources.

## Research Summary

### Omni Platform Overview
Omni is a business intelligence platform that "combines the consistency of a shared data model with the freedom of SQL." Key characteristics:
- Dynamically builds data models as users work
- SQL-based querying and analysis
- Supports workbooks, dashboards, and visualizations
- Provides data connection and integration features
- AI integration and embedding capabilities

### Omni API Capabilities
- **Base URL**: Same as login URL with "/api" appended (e.g., `https://myorg.omniapp.co/api`)
- **Authentication**: API key authentication via Bearer token
- **Rate Limiting**: 60 requests per minute
- **Available Endpoints**:
  - Models API (`/api/v1/models`) - Create, list, delete, refresh, validate models
  - Query API (`/api/v1/query/run`) - Execute queries, returns base64 encoded Apache Arrow tables
  - Content/Documents APIs - Access workbooks, dashboards, etc.
  - Connections API (`/api/v1/connections`) - Data source connections
  - Topics, Schedules, Users, User groups, etc.

### Key Omni Entities Identified

#### Core Entities (MVP Focus)
1. **Models** - Foundation of data layer, defines structure and relationships
   - API: `/api/v1/models`
   - Metadata: Creation/update timestamps, validation status, connection details
   - Lineage: Connect to underlying database tables/connections

2. **Workbooks** - Analysis containers with queries and visualizations
   - API: Content/documents endpoints
   - Metadata: Creation date, owner, query definitions
   - Lineage: Depend on topics/models used in queries

3. **Queries** - Specific data queries and their results
   - API: `/api/v1/query/run` and content endpoints
   - Metadata: SQL definition, execution stats, result schemas
   - Lineage: Depend on models/topics they query

#### Secondary Entities (Future Versions)
- **Topics** - Logical groupings of related data/fields
- **Dashboards/Views** - End-user facing analytical artifacts
- **Connections** - Data source connections (could be external dependencies initially)

### Lineage Flow Design
```
Connections → Models → Workbooks → Queries
```

## Implementation Plan

### Package Structure
Following Dagster BI integration patterns (Tableau, PowerBI):
```
dagster-omni/
├── dagster_omni/
│   ├── __init__.py          # Public API exports
│   ├── version.py           # Version info
│   ├── resources.py         # OmniWorkspace resource and API client
│   ├── translator.py        # DagsterOmniTranslator for asset specs
│   ├── asset_utils.py       # Asset utility functions
│   └── py.typed            # Type hints marker
├── dagster_omni_tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_resources.py
│   ├── test_translator.py
│   └── test_asset_utils.py
├── setup.py                 # Package setup
├── LICENSE                  # Apache 2.0 license
├── MANIFEST.in             # Package manifest
├── README.md               # User documentation
└── tox.ini                 # Testing configuration
```

### Core Components

#### 1. OmniWorkspace Resource (`resources.py`)
- ConfigurableResource following Dagster patterns
- API client for Omni authentication and requests
- Methods for fetching models, workbooks, queries
- Caching for performance optimization
- Similar to `TableauWorkspace` and `PowerBIWorkspace`

#### 2. DagsterOmniTranslator (`translator.py`)
- Converts Omni entities to Dagster AssetSpecs
- Handles metadata extraction and asset naming
- Defines lineage relationships between entities
- Extensible for custom asset naming/grouping

#### 3. Asset Utilities (`asset_utils.py`)
- Helper functions for creating asset events
- Materialization and observation logic
- Query execution and result handling

### Technical Considerations

#### Authentication
- API key-based authentication via Bearer token
- Keys created by Organization Admins
- Keys inherit user attributes and don't expire automatically
- Need secure handling of API keys in Dagster configuration

#### Rate Limiting
- 60 requests per minute limit
- Implement exponential backoff for rate limit handling
- Consider caching strategies to minimize API calls

#### Data Handling
- Query results returned as base64 encoded Apache Arrow tables
- Need utilities to decode and process results
- Consider result size limitations and streaming for large datasets

#### Error Handling
- Handle API errors gracefully
- Provide meaningful error messages for common issues
- Implement retry logic for transient failures

### Dependencies
- `dagster` (core framework)
- `requests>=2.25.0` (HTTP client)
- Potentially `pyarrow` for handling query results

### Testing Strategy
- Mock Omni API responses for unit tests
- Test authentication and API client functionality
- Validate asset spec generation and lineage
- Test error handling and edge cases

## Implementation Status

### Completed
- ✅ Research Omni documentation and API capabilities
- ✅ Examine existing Dagster BI integrations for patterns
- ✅ Identify core Omni entities for asset representation
- ✅ Validate entity mapping with user
- ✅ Create package structure and setup files

### In Progress
- 🔄 Implement core integration components

### Pending
- ⏳ Implement OmniWorkspace resource and API client
- ⏳ Implement DagsterOmniTranslator for asset specs
- ⏳ Implement asset utility functions
- ⏳ Create comprehensive test suite
- ⏳ Run linting and code quality checks

## Key Design Decisions

1. **MVP Scope**: Focus on Models → Workbooks → Queries for initial version
2. **Skip Initially**: Schedules, folders, topics, dashboards for complexity reduction
3. **Pattern Following**: Closely follow Tableau/PowerBI integration patterns
4. **Extensibility**: Design for easy addition of more entity types later
5. **API-First**: Leverage Omni's comprehensive API for metadata and lineage

## Next Steps
1. Implement the OmniWorkspace resource with API client
2. Create the translator for converting Omni entities to Dagster assets
3. Add utility functions for asset materialization and observation
4. Write comprehensive tests
5. Add documentation and examples
6. Consider adding to Dagster's integration documentation

## Future Enhancements
- Add support for Topics and Dashboards
- Implement query result caching
- Add more sophisticated lineage detection
- Support for Omni scheduling integration
- Custom asset grouping and naming strategies
- Integration with Dagster's data quality features

## References
- [Omni Documentation](https://docs.omni.co/docs)
- [Omni API Reference](https://docs.omni.co/docs/API)
- [Dagster Tableau Integration](python_modules/libraries/dagster-tableau/)
- [Dagster PowerBI Integration](python_modules/libraries/dagster-powerbi/)