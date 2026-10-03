# Resource Renaming/Aliasing

Dagster provides the ability to rename or alias resource keys across jobs, ops, assets, and schedules. This is useful when you want to reuse existing definitions with different resource configurations, or when transitioning between different resource setups.

## Overview

The `rename_resources()` method is available on:
- `OpDefinition` 
- `JobDefinition`
- `AssetsDefinition`
- `ScheduleDefinition`

It accepts a mapping from old resource key to new resource key and returns a new definition with the resources renamed.

## Examples

### Renaming Op Resources

```python
import dagster as dg

@dg.op(
    required_resource_keys={"database"},
    ins={"data": dg.In(input_manager_key="csv_manager")},
    outs={"result": dg.Out(io_manager_key="parquet_manager")}
)
def process_data(context, data):
    # Use the database resource
    db = context.resources.database
    return db.process(data)

# Rename resources for different environments
dev_op = process_data.rename_resources({
    "database": "dev_database",
    "csv_manager": "dev_csv_manager", 
    "parquet_manager": "dev_parquet_manager"
})

prod_op = process_data.rename_resources({
    "database": "prod_database",
    "csv_manager": "prod_csv_manager",
    "parquet_manager": "prod_parquet_manager"
})
```

### Renaming Job Resources

```python
@dg.resource
def postgres_db():
    return PostgresConnection(...)

@dg.resource  
def mysql_db():
    return MySQLConnection(...)

@dg.job(resource_defs={"database": postgres_db, "cache": redis_cache})
def my_job():
    process_data()

# Create a version of the job that uses MySQL instead
mysql_job = my_job.rename_resources({"database": "mysql_database"})

# Provide the MySQL resource with the new key
mysql_job_configured = mysql_job.with_top_level_resources({
    "mysql_database": mysql_db,
    "cache": redis_cache
})
```

### Renaming Asset Resources

```python
@dg.asset(resource_defs={"warehouse": snowflake_resource})
def customer_data(context):
    return context.resources.warehouse.query("SELECT * FROM customers")

# Create a version that uses a different warehouse
test_customer_data = customer_data.rename_resources({"warehouse": "test_warehouse"})

# Use in different environments
@dg.Definitions(
    assets=[test_customer_data],
    resources={
        "test_warehouse": test_database_resource,
    }
)
def test_definitions():
    pass
```

### Renaming Schedule Resources

```python
@dg.schedule(cron_schedule="0 0 * * *", job=my_job)
def daily_job_schedule():
    return {}

# Create a version for different environment
dev_schedule = daily_job_schedule.rename_resources({
    "database": "dev_database"
})
```

## Use Cases

### Environment-Specific Deployments

Use resource renaming to deploy the same logic across different environments with environment-specific resources:

```python
# Base definitions
@dg.job(resource_defs={"db": prod_db, "storage": s3_storage})
def etl_job():
    extract_op()
    transform_op() 
    load_op()

# Environment-specific versions
dev_job = etl_job.rename_resources({"db": "dev_db", "storage": "local_storage"})
staging_job = etl_job.rename_resources({"db": "staging_db", "storage": "staging_storage"})
```

### Team Isolation

Allow different teams to use shared ops with their own resource configurations:

```python
# Shared op
@dg.op(required_resource_keys={"database"})
def shared_analytics_op(context):
    return context.resources.database.run_query("SELECT * FROM analytics")

# Team-specific versions
team_a_op = shared_analytics_op.rename_resources({"database": "team_a_database"})
team_b_op = shared_analytics_op.rename_resources({"database": "team_b_database"})
```

### Migration and Gradual Rollouts

Use resource renaming during migrations to gradually transition to new resource configurations:

```python
# Original job
@dg.job(resource_defs={"old_api": legacy_api})
def data_sync_job():
    sync_data_op()

# Create version with new API alongside old one
migrated_job = data_sync_job.rename_resources({"old_api": "new_api"})

# Deploy both versions during transition period
@dg.Definitions(
    jobs=[data_sync_job, migrated_job],
    resources={
        "old_api": legacy_api_resource,
        "new_api": new_api_resource
    }
)
def definitions():
    pass
```

## Important Notes

1. **Validation**: The `rename_resources()` method validates that all keys in the mapping exist in the original definition. Unknown keys will raise a `DagsterInvalidDefinitionError`.

2. **Partial Mapping**: You only need to include keys that you want to rename. Other resource keys will remain unchanged.

3. **Immutability**: Resource renaming creates new definition objects. The original definitions are not modified.

4. **Transitive Renaming**: For `JobDefinition`, resource renaming is applied transitively to all ops in the job graph that support it.

5. **Input/Output Managers**: For `OpDefinition`, both required resource keys and input/output manager keys are renamed.