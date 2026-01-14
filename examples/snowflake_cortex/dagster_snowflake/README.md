# Dagster Snowflake AI Integration

This project demonstrates Dagster as the production orchestration layer for Snowflake's AI Data Cloud, showcasing Cortex AI capabilities with comprehensive workflow orchestration. The project addresses common Snowflake prospect pain points including partitioned assets, dbt integration, timezone handling, authentication, and performance optimization - all using Resources as the abstraction layer.

## Project Structure

```
dagster_snowflake/
├── src/
│   └── dagster_snowflake/
│       ├── definitions.py          # Main entry point
│       └── defs/
│           ├── assets/             # Data assets
│           │   ├── ingestion/       # Phase 1: Data ingestion
│           │   ├── cortex_ai/       # Phase 2: Cortex AI processing
│           │   └── dynamic_tables/ # Phase 3: Dynamic Tables
│           ├── resources.py         # Dagster resources
│           ├── jobs.py              # Job definitions
│           ├── schedules.py         # Schedule definitions
│           ├── sensors.py           # Sensor definitions
│           └── partitions.py       # Partition definitions
└── tests/                          # Test suite
```

## Setup

1. Install dependencies:
```bash
cd dagster_snowflake
uv sync
```

2. Set environment variables (create `.env` file):
```bash
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password  # Or use SNOWFLAKE_PRIVATE_KEY for key auth
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_SCHEMA=PUBLIC

# Optional: For private key authentication
SNOWFLAKE_PRIVATE_KEY=your_private_key
SNOWFLAKE_PRIVATE_KEY_PASSPHRASE=your_passphrase  # If key is encrypted

# Required for dbt integration
DBT_PROJECT_DIR=dbt_project
DBT_PROFILES_DIR=dbt_project
```

## Verify Definitions

Check that definitions load correctly:

```bash
# Using the check script
python check_defs.py

# Or using dagster CLI (after installing dependencies)
dagster check defs
```

## Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_definitions.py -v

# Run with coverage
uv run pytest tests/ --cov=dagster_snowflake --cov-report=html
```

## Key Features

### Why Resources Over I/O Managers

This project uses **Resources** as the abstraction layer instead of I/O Managers because:
- **Flexibility**: Full control over SQL execution and query patterns
- **SQL-first approach**: Write optimized SQL queries directly
- **Authentication**: Easy switching between password, private key, and OAuth
- **Cost optimization**: Fine-grained control over warehouse usage and query patterns
- **Production-ready**: Better suited for complex data engineering workflows

### Phase 1: Partitioned Assets

- **Partitioned Ingestion** (`raw_stories`): Daily partitioned ingestion with timezone-aware date filtering
- **Partitioned Analytics**: Daily sentiment aggregates and entity summaries using incremental MERGE patterns
- **Incremental Processing**: Process only new data per partition, reducing costs and improving performance

### Phase 2: dbt Integration (Components)

- **dbt Component**: Modern Dagster Components approach for dbt integration
- **Staging/Intermediate/Marts**: Full dbt project structure with best practices
- **Dependency Management**: Automatic dependency resolution between Cortex AI assets and dbt models
- **Incremental Models**: Support for incremental dbt models with partition awareness

### Phase 3: Cortex AI Integration
- **Sentiment Analysis** (`story_sentiment_analysis`): Uses `AI_CLASSIFY` with optimized queries (CTEs, column selection)
- **Entity Extraction** (`entity_extraction`): Uses `SNOWFLAKE.CORTEX.COMPLETE` for structured entity extraction
- **Data Engineering Stories** (`data_engineering_stories`): Dedicated asset for data engineering story analysis
- **Intelligent Aggregations** (`daily_story_summary`): Uses `AI_AGG` for story summarization

### Phase 4: Authentication & Configuration

- **Password Authentication**: Simple password-based auth for development
- **Private Key Authentication**: Production-ready PEM/DER key support with base64 encoding
- **Environment-based Configuration**: Different auth methods for dev/staging/production
- See [Authentication Examples](docs/authentication_examples.md) for detailed setup

### Phase 5: Performance & Cost Optimization

- **Column Selection**: Optimized queries selecting only needed columns (avoid SELECT *)
- **CTE Patterns**: Reusable CTEs for query optimization
- **Cost Tracking**: Query INFORMATION_SCHEMA.QUERY_HISTORY for warehouse cost monitoring
- **Query Optimization Examples**: Best practices for Snowflake query performance

### Phase 6: Dynamic Tables
- External asset definitions for Dynamic Tables with freshness monitoring

### Phase 7: Jobs, Schedules, and Sensors
- **Jobs**: Daily intelligence, dbt transformations, weekly reports
- **Schedules**: Daily (2 AM EST) and weekly (Sunday 3 AM EST) schedules
- **Sensors**: Dynamic Table freshness monitoring

## Testing Strategy

Tests follow the testing-strategies skill patterns:

1. **Unit Tests**: Test individual assets and resources with mocked dependencies
2. **Integration Tests**: Verify definitions load correctly
3. **Configuration Tests**: Test schedules, sensors, and jobs are properly configured

## Note on Package Naming

There's a naming conflict between this project (`dagster_snowflake`) and the `dagster-snowflake` package. The code uses `TYPE_CHECKING` imports to handle this gracefully. When installing dependencies, ensure `dagster-snowflake` is installed separately:

```bash
uv add dagster-snowflake
```

## Resource Patterns Best Practices

### Using Snowflake Resources

```python
from dagster_snowflake import SnowflakeResource
from dagster_snowflake_ai.defs.resources import get_snowflake_connection_with_schema

@dg.asset
def my_asset(context, snowflake: SnowflakeResource):
    with get_snowflake_connection_with_schema(snowflake) as (connection, schema):
        cursor = connection.cursor()
        # Write optimized SQL directly
        cursor.execute(f"SELECT ... FROM {schema}.table WHERE ...")
```

### Partitioned Assets

```python
from dagster_snowflake_ai.defs.partitions import daily_partitions

@dg.asset(partitions_def=daily_partitions)
def partitioned_asset(context, snowflake: SnowflakeResource):
    partition_date = context.partition_key
    # Filter by partition date for incremental processing
    # Use MERGE for efficient upserts
```

### dbt Integration

The dbt component automatically loads dbt models as Dagster assets. Configure dependencies in `defs/dbt_transform/defs.yaml`:

```yaml
post_processing:
  assets:
    - target: "stg_stories"
      attributes:
        deps: ["raw_stories"]
```

## Development

The project uses:
- **Dagster 1.12.10** for orchestration
- **dagster-snowflake** for Snowflake integration
- **dagster-dbt** for dbt integration via Components
- **cryptography** for private key authentication
- **pytest** for testing
- **uv** for dependency management

## Documentation

- [Authentication Examples](docs/authentication_examples.md) - Password and private key authentication setup
- [Migration Guide](docs/migration_guide.md) - Adding partitions, integrating dbt, optimizing queries
