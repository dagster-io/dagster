# Data Platform Architecture Guide - Dagster Project

This directory contains a complete Dagster project demonstrating data platform architectural patterns using modern Dagster best practices: Components, multiple code locations, and dignified Python.

## Project Structure

```
data-platform-architecture-guide/
├── pyproject.toml                    # Dependencies and project config
├── workspace.yaml                    # Multi-code-location workspace
├── README.md                         # This file
├── src/
│   ├── data_platform_guide/          # Component-based code locations
│   │   ├── __init__.py
│   │   ├── databricks_delta/         # Code location 1: Databricks Delta Lakehouse
│   │   │   ├── __init__.py
│   │   │   ├── definitions.py        # Definitions for Databricks location
│   │   │   └── defs/
│   │   │       ├── components/
│   │   │       │   └── lakehouse/    # Lakehouse medallion component
│   │   │       │       ├── component.py
│   │   │       │       └── defs.yaml
│   │   │       ├── assets/
│   │   │       │   ├── bronze/       # Bronze layer (raw Delta tables)
│   │   │       │   ├── silver/       # Silver layer (validated Delta tables)
│   │   │       │   └── gold/         # Gold layer (curated Delta tables)
│   │   │       └── resources.py      # Databricks resources
│   │   └── snowflake_medallion/      # Code location 2: Snowflake dbt Medallion
│   │       ├── __init__.py
│   │       ├── definitions.py        # Definitions for Snowflake location
│   │       ├── dbt_project/          # Full dbt project
│   │       │   ├── dbt_project.yml
│   │       │   ├── models/
│   │       │   │   ├── bronze/       # Bronze layer models
│   │       │   │   ├── silver/       # Silver layer models
│   │       │   │   └── gold/        # Gold layer models
│   │       │   └── sources.yml
│   │       └── defs/
│   │           ├── components/
│   │           │   ├── medallion/    # Medallion component
│   │           │   └── dbt_project/  # dbt component
│   │           └── resources.py      # Snowflake + dbt resources
│   └── defs/                         # Main code location with architecture patterns
│       ├── __init__.py
│       ├── definitions.py            # Main Definitions export
│       ├── assets/                    # Architecture pattern examples
│       │   ├── __init__.py
│       │   ├── etl_pipeline.py       # ETL pattern
│       │   ├── elt_pipeline.py       # ELT pattern
│       │   ├── lakehouse_pipeline.py # Lakehouse pattern
│       │   └── composable_resources.py # Composable resources pattern
│       └── resources/                 # Shared resources
│           ├── __init__.py
│           └── mock_storage.py
└── tests/                            # Test suite
    ├── __init__.py
    ├── conftest.py
    └── test_assets.py
```

## Getting Started

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

1. Create a virtual environment and install dependencies:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

2. Verify installation:

```bash
dg check defs
```

### Running the Project

Start the Dagster UI:

```bash
dg dev
```

Or using the traditional command:

```bash
dagster dev
```

This will start the Dagster webserver at `http://localhost:3000` where you can:

- View all assets from both code locations
- Materialize assets individually or in groups
- Explore the asset lineage graph
- See different architecture patterns side by side

## Running Tests

Run the test suite:

```bash
pytest tests/ -v
```

Run specific test files:

```bash
pytest tests/test_assets.py -v
```

## Code Locations

This project demonstrates two separate code locations, each implementing the medallion architecture pattern:

### 1. Databricks Delta (Code Location 1)

**Pattern**: Lakehouse with Medallion Architecture  
**Storage**: Delta Lake tables  
**Technology**: Databricks, Delta Lake

**Architecture:**

- **Bronze Layer**: Raw sensor data loaded to Delta tables
- **Silver Layer**: Cleaned and validated sensor data in Delta tables
- **Gold Layer**: Aggregated sensor summaries for consumption

**Component**: `LakehouseComponent`

- Supports `demo_mode` for local development
- Real implementation uses Databricks and Delta Lake
- Demo mode uses local file system or DuckDB

**Usage:**

```python
# Component configuration in defs/components/lakehouse/defs.yaml
demo_mode: true  # Set to false for production
```

### 2. Snowflake dbt Medallion (Code Location 2)

**Pattern**: ELT with Medallion Architecture  
**Storage**: Snowflake tables  
**Technology**: Snowflake, dbt, SQL transformations

**Architecture:**

- **Bronze Layer**: Raw customer data loaded from sources
- **Silver Layer**: Cleaned and validated customer data (dbt models)
- **Gold Layer**: Curated customer summaries for business consumption (dbt models)

**Component**: `MedallionComponent`

- Integrates with full dbt project
- Uses `dagster-dbt` for dbt asset generation
- Supports `demo_mode` with DuckDB adapter

**dbt Models:**

- `bronze_customers.sql`: Raw data from sources
- `silver_customers.sql`: Cleaned and validated data
- `gold_customer_summary.sql`: Aggregated summaries

**Usage:**

```python
# Component configuration in defs/components/medallion/defs.yaml
demo_mode: true  # Set to false for production
```

## Demo Mode

Both code locations support demo mode for local development without external dependencies:

- **Databricks Delta**: Uses local file system or DuckDB instead of Databricks
- **Snowflake dbt**: Uses DuckDB adapter instead of Snowflake

To switch between demo and production modes, update the `demo_mode` parameter in the component YAML files.

## Architecture Patterns

### Medallion Architecture

Both code locations implement the medallion architecture pattern:

1. **Bronze (Raw)**: Unprocessed data as it arrives from source systems
   - Preserves original data for auditability
   - Enables reprocessing and historical analysis
   - No transformations applied

2. **Silver (Cleaned)**: Validated and standardized data
   - Data quality checks applied
   - Schema standardization
   - Deduplication and cleaning
   - Ready for internal consumption

3. **Gold (Curated)**: Business-ready aggregated data
   - Aggregated and enriched
   - Optimized for consumption
   - Designed for dashboards and applications

### When to Use Each Pattern

**Databricks Delta Lakehouse:**

- Very large volumes of data
- Need both batch and streaming processing
- Cost-effective storage is a priority
- Want to separate storage from compute
- Need ACID guarantees with Delta Lake

**Snowflake dbt Medallion:**

- Want to preserve raw data for flexibility
- Multiple teams need different transformations
- Cloud warehouse compute is affordable
- Enable self-service analytics
- Prefer SQL-based transformations

## Components

This project uses Dagster Components for reusable architecture patterns:

- **LakehouseComponent**: Implements medallion architecture for Databricks Delta
- **MedallionComponent**: Implements medallion architecture for Snowflake dbt

Components provide:

- Declarative configuration via YAML
- Demo mode support for local development
- Reusable patterns across projects
- Clear separation of concerns

## Dignified Python Standards

This project follows dignified Python standards:

- **Python 3.13+ syntax**: `list[str]`, `dict[str, int]`, `str | None`
- **ABC interfaces**: Uses `abc.ABC` instead of `typing.Protocol`
- **LBYL patterns**: Check before access, no exception-based control flow
- **Absolute imports**: Module-level imports only
- **ConfigurableResource**: Modern resource pattern instead of `@resource` decorators

## Production Considerations

### Resource Configuration

In production, configure real connections:

**Databricks:**

- Set `demo_mode: false` in component YAML
- Configure `server_hostname`, `http_path`, and `token` via environment variables
- Use actual Databricks workspace and Delta Lake storage

**Snowflake:**

- Set `demo_mode: false` in component YAML
- Configure Snowflake credentials via environment variables
- Update dbt profiles for Snowflake connection
- Run `dbt compile` to generate manifest.json

### Data Formats

- **Delta Lake**: Use Delta tables for ACID guarantees and time travel
- **Snowflake**: Use appropriate table types (transient, permanent) based on needs
- Implement partitioning for large datasets
- Consider clustering keys for query performance

### Scalability

- Use Spark or similar for large-scale processing (Databricks)
- Implement partitioning and bucketing strategies
- Consider streaming for real-time requirements
- Monitor and optimize query performance

### Observability

- Add comprehensive logging and metrics
- Track data lineage across layers
- Monitor data quality at each stage
- Set up alerts for pipeline failures

## Architecture Patterns in `src/defs/`

The `src/defs/` directory contains examples of common architecture patterns:

### ETL Pattern (`src/defs/assets/etl_pipeline.py`)

Traditional Extract-Transform-Load pattern where data is transformed before loading.

### ELT Pattern (`src/defs/assets/elt_pipeline.py`)

Extract-Load-Transform pattern where raw data is loaded first, then transformed in the warehouse.

### Lakehouse Pattern (`src/defs/assets/lakehouse_pipeline.py`)

Medallion architecture with bronze, silver, and gold layers.

### Composable Resources (`src/defs/assets/composable_resources.py`)

Demonstrates how to build reusable, composable resources using ABC interfaces and ConfigurableResource.

## Development Workflow

1. **Local Development**: Use demo mode for both code locations
2. **Testing**: Run `pytest tests/ -v` to run the test suite
3. **Validation**: Run `dg check defs` to validate definitions
4. **Materialization**: Use `dg dev` to start UI and materialize assets
5. **Production**: Update component YAML files with production configuration

## Notes

- These are simplified examples for demonstration purposes
- In production, add comprehensive error handling, logging, and resource management
- Match the architecture to your business requirements and constraints
- Start simple and evolve as needs change
- Components can be extended and customized for specific use cases
