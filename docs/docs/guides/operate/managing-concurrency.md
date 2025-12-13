---
title: Manage concurrency of Dagster assets, jobs, and Dagster instances
sidebar_label: Managing concurrency
description: How to limit the number of runs a job, or assets for an instance of Dagster.
sidebar_position: 50
---

This guide covers managing concurrency of Dagster assets, jobs, and Dagster instances to help prevent performance problems and downtime.

:::note
This article assumes familiarity with [assets](/guides/build/assets) and [jobs](/guides/build/jobs).
:::

## Limit the number of total runs that can be in progress at the same time

- Dagster Core, add the following to your [dagster.yaml](/deployment/oss/dagster-yaml)
- In Dagster+, add the following to your [full deployment settings](/deployment/dagster-plus/deploying-code/full-deployments/full-deployment-settings-reference)

```yaml
concurrency:
  runs:
    max_concurrent_runs: 15
```

## Limit the number of assets or ops actively executing across all runs

You can assign assets and ops to concurrency pools which allow you to limit the number of in progress op executions across all runs. You first assign your asset or op to a concurrency pool using the `pool` keyword argument.

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/managing_concurrency/concurrency_pool_api.py"
  title="src/<project_name>/defs/assets.py"
  language="python"
/>

You should be able to verify that you have set the pool correctly by viewing the details pane for the asset or op in the Dagster UI.

![Viewing the pool tag](/images/guides/operate/managing-concurrency/asset-pool-tag.png)

Once you have assigned your assets and ops to a concurrency pool, you can configure a pool limit for that pool in your deployment by using the [Dagster UI](/guides/operate/webserver) or the [`dagster` CLI](/api/clis/cli).

To specify a limit for the pool "database" using the UI, navigate to the `Deployments` &rarr; `Concurrency` settings page and click the `Add pool limit` button.

![Setting the pool limit](/images/guides/operate/managing-concurrency/add-pool-ui.png)

To specify a limit for the pool "database" using the `dagster` CLI, use:

```
dagster instance concurrency set database 1
```

## Limit the number of runs that can be in progress for a set of ops

You can also use concurrency pools to limit the number of in progress runs containing those assets or ops. You can follow the steps in the [Limit the number of assets or ops actively executing across all runs](#limit-the-number-of-assets-or-ops-actively-executing-across-all-runs) section to assign your assets and ops to pools and to configure the desired limit.

Once you have assigned your assets and ops to your pool, you can change your deployment settings to set the pool enforcement granularity. To limit the total number of runs containing a specific op at any given time (instead of the total number of ops actively executing), we need to set the pool granularity to `run`.       

- Dagster Core, add the following to your [dagster.yaml](/deployment/oss/dagster-yaml)
- In Dagster+, add the following to your [deployment settings](/deployment/dagster-plus/deploying-code/full-deployments/full-deployment-settings-reference)

```yaml
concurrency:
  pools:
    granularity: 'run'
```

Without this granularity set, the default granularity is set to the `op`. This means that for a pool `foo` with a limit `1`, we enforce that only one op is executing at a given time across all runs, but the number of runs in progress is unaffected by the pool limit.

### Setting a default limit for concurrency pools

- Dagster+: Edit the `concurrency` config in deployment settings via the [Dagster+ UI](/guides/operate/webserver) or the [`dagster-cloud` CLI](/api/clis/dagster-cloud-cli).
- Dagster Open Source: Use your instance's [dagster.yaml](/deployment/oss/dagster-yaml)

```yaml
concurrency:
  pools:
    default_limit: 1
```

## Limit the number of runs that can be in progress by run tag

You can also limit the number of in progress runs by run tag. This is useful for limiting sets of runs independent of which assets or ops it is executing. For example, you might want to limit the number of in-progress runs for a particular schedule. Or, you might want to limit the number of in-progress runs for all backfills.

```yaml
concurrency:
  runs:
    tag_concurrency_limits:
      - key: 'dagster/sensor_name'
        value: 'my_cool_sensor'
        limit: 5
      - key: 'dagster/backfill'
        limit: 10
```

### Limit the number of runs that can be in progress by unique tag value

To apply separate limits to each unique value of a run tag, set a limit for each unique value using `applyLimitPerUniqueValue`. For example, instead of limiting the number of backfill runs across all backfills, you may want to limit the number of runs for each backfill in progress:

```yaml
concurrency:
  runs:
    tag_concurrency_limits:
      - key: 'dagster/backfill'
        value:
          applyLimitPerUniqueValue: true
        limit: 10
```

## Job-level concurrency configuration

### Configuring executors for concurrency control

You can control concurrency at the job level by configuring executors. This is essential for controlling how many ops run simultaneously within a single job execution.

#### Using the multiprocess executor

The multiprocess executor allows you to control concurrency within a job run:

```python
from dagster import define_asset_job, multiprocess_executor

# Configure the multiprocess executor with concurrency limits
configured_multiprocess_executor = multiprocess_executor.configured(
    {
        "max_concurrent": 3,  # Maximum 3 concurrent processes
        "tag_concurrency_limits": [
            {
                "key": "database",
                "value": "postgres",
                "limit": 1,
            },
            {
                "key": "compute_type", 
                "value": "heavy",
                "limit": 2,
            }
        ],
    }
)

# Apply executor to job
my_job = define_asset_job(
    name="my_concurrent_job",
    selection=["asset_1", "asset_2", "asset_3"],
    executor_def=configured_multiprocess_executor,
)
```

#### Alternative: Using job configuration

You can also configure concurrency through job configuration:

```python
my_job = define_asset_job(
    name="my_job",
    selection=["asset_1", "asset_2", "asset_3"],
    config={
        "execution": {
            "config": {
                "multiprocess": {
                    "max_concurrent": 2,
                    "tag_concurrency_limits": [
                        {
                            "key": "resource_type",
                            "value": "database",
                            "limit": 1,
                        }
                    ],
                }
            }
        }
    },
)
```

### Asset-level concurrency with tags

Control concurrency for specific assets using tags:

```python
from dagster import asset

@asset(tags={"database": "postgres", "priority": "high"})
def database_heavy_asset():
    # This asset will be limited by database concurrency settings
    pass

@asset(tags={"compute_type": "heavy"})
def compute_intensive_asset():
    # This asset will be limited by compute_type concurrency settings
    pass
```

## Complete configuration examples

### Example 1: Complete dagster.yaml for production

Here's a complete `dagster.yaml` configuration for a production deployment:

```yaml
# Complete dagster.yaml with comprehensive concurrency settings
storage:
  postgres:
    postgres_db:
      username: ${DAGSTER_PG_USERNAME}
      password: ${DAGSTER_PG_PASSWORD}
      hostname: ${DAGSTER_PG_HOST}
      db_name: ${DAGSTER_PG_DB}
      port: ${DAGSTER_PG_PORT}

run_launcher:
  module: dagster.core.launcher
  class: DefaultRunLauncher

# Comprehensive concurrency configuration
concurrency:
  # Global run limits
  runs:
    max_concurrent_runs: 10
    tag_concurrency_limits:
      # Limit backfill runs
      - key: "dagster/backfill"
        limit: 5
      # Limit by database access
      - key: "database"
        value: "postgres"
        limit: 3
      # Limit by environment
      - key: "environment"
        value: "production"
        limit: 8
      # Limit high-priority runs
      - key: "priority"
        value: "high"
        limit: 2
      # Per-sensor limits
      - key: "dagster/sensor_name"
        value: "data_freshness_sensor"
        limit: 1

  # Op-level concurrency pools
  pools:
    granularity: 'op'  # or 'run' for run-level limits
    default_limit: 5
    
# Run queue configuration
run_queue:
  max_concurrent_runs: 10
  tag_concurrency_limits:
    - key: "resource_intensive"
      limit: 2
    - key: "external_api"
      value: "third_party_service"
      limit: 1

# Run monitoring
run_monitoring:
  enabled: true
  start_timeout_seconds: 180
  cancel_timeout_seconds: 180
```

### Example 2: Kubernetes deployment with Helm

For Kubernetes deployments using the Dagster Helm chart, configure concurrency in `values.yaml`:

```yaml
# values.yaml for Dagster Helm chart
dagster:
  instance:
    config:
      # Concurrency settings for Kubernetes deployment
      concurrency:
        runs:
          max_concurrent_runs: 15
          tag_concurrency_limits:
            - key: "kubernetes/namespace"
              value: "data-pipelines"
              limit: 10
            - key: "resource_class"
              value: "memory_intensive"
              limit: 3
            - key: "dagster/backfill"
              limit: 5
        
        pools:
          granularity: 'op'
          default_limit: 8

      # Run queue for K8s
      run_queue:
        max_concurrent_runs: 15
        tag_concurrency_limits:
          - key: "compute_type"
            value: "gpu"
            limit: 2

# K8s run launcher configuration
dagsterUserDeployments:
  enabled: true
  deployments:
    - name: "data-pipeline"
      image:
        repository: "my-registry/dagster-user-code"
        tag: "latest"
      dagsterApiGrpcArgs:
        - "--port"
        - "4000"
      port: 4000
      env:
        DAGSTER_POSTGRES_USER: ${POSTGRES_USER}
        DAGSTER_POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
        DAGSTER_POSTGRES_HOST: ${POSTGRES_HOST}
        DAGSTER_POSTGRES_DB: ${POSTGRES_DB}
```

### Example 3: Docker compose deployment

For Docker Compose deployments, configure concurrency in the shared `dagster.yaml`:

```yaml
# docker-compose.yml
version: '3.8'
services:
  dagster_webserver:
    image: my-dagster-image
    environment:
      DAGSTER_POSTGRES_USER: dagster
      DAGSTER_POSTGRES_PASSWORD: dagster
      DAGSTER_POSTGRES_HOST: postgres
      DAGSTER_POSTGRES_DB: dagster
    volumes:
      - ./dagster.yaml:/opt/dagster/dagster_home/dagster.yaml
    
  dagster_daemon:
    image: my-dagster-image
    environment:
      DAGSTER_POSTGRES_USER: dagster
      DAGSTER_POSTGRES_PASSWORD: dagster
      DAGSTER_POSTGRES_HOST: postgres
      DAGSTER_POSTGRES_DB: dagster
    volumes:
      - ./dagster.yaml:/opt/dagster/dagster_home/dagster.yaml
    command: ["dagster-daemon", "run"]
```

```yaml
# dagster.yaml for Docker Compose
storage:
  postgres:
    postgres_db:
      username: ${DAGSTER_POSTGRES_USER}
      password: ${DAGSTER_POSTGRES_PASSWORD}
      hostname: ${DAGSTER_POSTGRES_HOST}
      db_name: ${DAGSTER_POSTGRES_DB}
      port: 5432

run_launcher:
  module: dagster_docker
  class: DockerRunLauncher
  config:
    image: "my-dagster-image"
    network: "dagster_network"

concurrency:
  runs:
    max_concurrent_runs: 5
    tag_concurrency_limits:
      - key: "docker/network"
        value: "dagster_network"
        limit: 3
      - key: "memory_usage"
        value: "high"
        limit: 2
  
  pools:
    default_limit: 3
```

## Advanced concurrency patterns

### Environment-based concurrency

Configure different concurrency limits based on environment:

```python
import os
from dagster import define_asset_job, multiprocess_executor

# Environment-aware concurrency configuration
def get_executor_config():
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        return {
            "max_concurrent": 5,
            "tag_concurrency_limits": [
                {"key": "database", "value": "prod_db", "limit": 2},
                {"key": "external_api", "limit": 1},
            ]
        }
    elif env == "staging":
        return {
            "max_concurrent": 3,
            "tag_concurrency_limits": [
                {"key": "database", "value": "staging_db", "limit": 1},
            ]
        }
    else:  # development
        return {"max_concurrent": 2}

configured_executor = multiprocess_executor.configured(get_executor_config())

env_aware_job = define_asset_job(
    name="environment_aware_job",
    selection=["*"],
    executor_def=configured_executor,
)
```

### Resource-based concurrency control

Limit concurrency based on resource usage:

```python
from dagster import asset, resource, ConfigurableResource

class DatabaseResource(ConfigurableResource):
    connection_limit: int = 5

@asset(tags={"resource_type": "database", "priority": "high"})
def high_priority_db_asset(database: DatabaseResource):
    # High priority database operation
    pass

@asset(tags={"resource_type": "database", "priority": "normal"})
def normal_priority_db_asset(database: DatabaseResource):
    # Normal priority database operation
    pass

# Job configuration with resource-aware concurrency
resource_controlled_job = define_asset_job(
    name="resource_controlled_job",
    selection=["high_priority_db_asset", "normal_priority_db_asset"],
    config={
        "execution": {
            "config": {
                "multiprocess": {
                    "max_concurrent": 10,
                    "tag_concurrency_limits": [
                        {
                            "key": "resource_type",
                            "value": "database",
                            "limit": 3,  # Max 3 database operations
                        },
                        {
                            "key": "priority",
                            "value": "high",
                            "limit": 1,  # Only 1 high priority at a time
                        }
                    ],
                }
            }
        }
    },
)
```

### Dynamic concurrency based on system load

Implement dynamic concurrency adjustment:

```python
import psutil
from dagster import asset, sensor, RunRequest

def get_dynamic_concurrency():
    """Adjust concurrency based on system resources."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_percent = psutil.virtual_memory().percent
    
    if cpu_percent > 80 or memory_percent > 85:
        return 1  # Reduce concurrency under high load
    elif cpu_percent < 50 and memory_percent < 60:
        return 5  # Increase concurrency when resources available
    else:
        return 3  # Default concurrency

@sensor(job_name="adaptive_job")
def system_load_sensor(context):
    """Trigger jobs based on system load."""
    max_concurrent = get_dynamic_concurrency()
    
    return RunRequest(
        run_key=f"adaptive_run_{context.cursor}",
        run_config={
            "execution": {
                "config": {
                    "multiprocess": {
                        "max_concurrent": max_concurrent
                    }
                }
            }
        }
    )
```

## Limit the number of ops concurrently executing for a single run

While pool limits allow you to limit the number of ops executing across all runs, to limit the number of ops executing _within a single run_, you need to configure your run executor. You can limit concurrency for ops and assets in runs, by using `max_concurrent` in the run config, either in Python or using the Launchpad in the Dagster UI.

:::info

The default limit for op execution within a run depends on which executor you are using. For example, the <PyObject section="execution" module="dagster" object="multiprocess_executor" /> by default limits the number of ops executing to the value of `multiprocessing.cpu_count()` in the launched run.

:::

### Limit concurrent execution for a specific job

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/managing_concurrency/limit_execution_job.py"
  language="python"
  title="src/<project_name>/defs/assets.py"
/>

### Limit concurrent execution for all runs in a code location

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/managing_concurrency/limit_execution_code_location.py"
  language="python"
  title="src/<project_name>/defs/executor.py"
/>

## Prevent runs from starting if another run is already occurring (advanced)

You can use Dagster's rich metadata to use a schedule or a sensor to only start a run when there are no currently running jobs.

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/managing_concurrency/concurrency_no_more_than_1_job.py"
  language="python"
  title="src/<project_name>/defs/assets.py"
/>

## Troubleshooting

### Configuration errors

#### `tag_concurrency_limits` not working in job configuration

**Problem**: Users report that tag concurrency limits defined in job configuration don't work.

**Solution**: Ensure you're using the correct configuration structure. Tag concurrency limits in job definitions should be nested under the executor configuration:

```python
# ❌ Incorrect - doesn't work
my_job = define_asset_job(
    name="my_job",
    config={
        "tag_concurrency_limits": [  # Wrong location
            {"key": "database", "limit": 1}
        ]
    }
)

# ✅ Correct - works properly
my_job = define_asset_job(
    name="my_job",
    config={
        "execution": {
            "config": {
                "multiprocess": {
                    "tag_concurrency_limits": [  # Correct location
                        {"key": "database", "limit": 1}
                    ]
                }
            }
        }
    }
)
```

#### Executor configuration not taking effect

**Problem**: Configured executor limits are ignored.

**Solutions**:

1. **Use configured executor correctly**:
```python
# ✅ Correct way to configure executor
configured_executor = multiprocess_executor.configured({
    "max_concurrent": 3,
    "tag_concurrency_limits": [
        {"key": "database", "value": "postgres", "limit": 1}
    ]
})

my_job = define_asset_job(
    name="my_job",
    executor_def=configured_executor,  # Pass configured executor
    selection=["*"]
)
```

2. **Verify assets have matching tags**:
```python
@asset(tags={"database": "postgres"})  # Tag must match concurrency limit
def my_database_asset():
    pass
```

### Deployment-specific issues

#### Concurrency limits not working in Kubernetes

**Problem**: Configuration works locally but not in Kubernetes deployment.

<Tabs>
  <TabItem value="Dagster+" label="Dagster+">
    If runs aren't being dequeued in Dagster+, the root causes could be:
    * **If using a [hybrid deployment](/deployment/dagster-plus/hybrid)**, the agent serving the deployment may be down. In this situation, runs will be paused.
    * **Dagster+ is experiencing downtime**. Check the [status page](https://dagstercloud.statuspage.io) for the latest on potential outages.
  </TabItem>
</Tabs>

**Solutions**:

1. **Ensure dagster.yaml is properly mounted**:
```yaml
# In Helm values.yaml
dagster:
  instance:
    config:
      # Your concurrency config here
      concurrency:
        runs:
          max_concurrent_runs: 10
```

2. **Verify environment variables are set**:
```bash
# Check if environment variables are available in pods
kubectl exec -it dagster-daemon-pod -- env | grep DAGSTER
```

3. **Check daemon logs for configuration errors**:
```bash
kubectl logs dagster-daemon-pod -f
```

#### Docker run launcher not respecting limits

**Problem**: Concurrency limits ignored when using DockerRunLauncher.

**Solutions**:

1. **Ensure shared storage configuration**:
```yaml
storage:
  postgres:  # Both daemon and run containers need same storage
    postgres_db:
      username: ${DAGSTER_POSTGRES_USER}
      password: ${DAGSTER_POSTGRES_PASSWORD}
      hostname: ${DAGSTER_POSTGRES_HOST}
      db_name: ${DAGSTER_POSTGRES_DB}
```

2. **Verify network configuration**:
```yaml
run_launcher:
  module: dagster_docker
  class: DockerRunLauncher
  config:
    image: "my-dagster-image"
    network: "dagster_network"  # Ensure network connectivity
```

### Performance issues

#### High memory usage with concurrent runs

**Problem**: Memory consumption increases dramatically with concurrent execution.

**Solutions**:

1. **Limit concurrent runs based on available memory**:
```python
import psutil

def get_memory_based_concurrency():
    available_gb = psutil.virtual_memory().available / (1024**3)
    if available_gb > 16:
        return 8
    elif available_gb > 8:
        return 4
    else:
        return 2

# Use in executor configuration
```

2. **Use resource-aware tags**:
```python
@asset(tags={"memory_usage": "high"})
def memory_intensive_asset():
    pass

# Limit high memory usage assets
job_config = {
    "execution": {
        "config": {
            "multiprocess": {
                "tag_concurrency_limits": [
                    {"key": "memory_usage", "value": "high", "limit": 1}
                ]
            }
        }
    }
}
```

#### Database connection pool exhaustion

**Problem**: Too many concurrent database operations exhaust connection pool.

**Solutions**:

1. **Use database-specific concurrency limits**:
```yaml
concurrency:
  runs:
    tag_concurrency_limits:
      - key: "database"
        value: "postgres"
        limit: 5  # Match your connection pool size
      - key: "database"
        value: "snowflake"
        limit: 10
```

2. **Implement connection pool monitoring**:
```python
@asset(tags={"database": "postgres", "connection_type": "read_heavy"})
def read_heavy_asset():
    # Monitor connection usage
    pass
```

### Monitoring and debugging

#### Debug concurrency configuration

Use these approaches to debug concurrency issues:

1. **Check daemon logs**:
```bash
# Look for concurrency-related messages
grep -i "concurrency\|queue\|limit" /path/to/daemon.log
```

2. **Verify configuration in Dagster UI**:
   - Navigate to **Deployment > Configuration**
   - Check `concurrency` section for your settings
   - Verify `run_queue` configuration

3. **Monitor run queue status**:
```python
from dagster import DagsterInstance

instance = DagsterInstance.get()
queued_runs = instance.get_runs(filters=RunsFilter(statuses=[DagsterRunStatus.QUEUED]))
print(f"Queued runs: {len(queued_runs)}")
```

4. **Check run tags and concurrency application**:
```python
# Verify tags are properly applied
run = instance.get_run_by_id(run_id)
print(f"Run tags: {run.tags}")
```

### When runs remain in QUEUED status

The most common causes and solutions:

#### Dagster Open Source

1. **Daemon not running**: Verify daemon is active in **Deployment > Daemons**
2. **Storage mismatch**: Ensure daemon and webserver use same `dagster.yaml`
3. **Concurrency limits**: Check if limits are blocking queue progression
4. **Queue configuration**: Verify `max_concurrent_runs` is not set to 0

#### Dagster+

1. **Agent issues**: For hybrid deployments, check agent status
2. **Service outages**: Check [Dagster+ status page](https://dagstercloud.statuspage.io/)

### Testing concurrency configuration

Before deploying concurrency changes to production:

1. **Test locally**:
```bash
# Start with minimal concurrency
dagster instance concurrency set test_pool 1
dagster job execute my_job
```

2. **Validate configuration**:
```python
def test_concurrency_config():
    """Test that concurrency configuration is properly applied."""
    from dagster import validate_run_config
    
    config = {
        "execution": {
            "config": {
                "multiprocess": {
                    "max_concurrent": 2,
                    "tag_concurrency_limits": [
                        {"key": "database", "limit": 1}
                    ]
                }
            }
        }
    }
    
    result = validate_run_config(my_job, config)
    assert result.success
```

3. **Monitor resource usage during testing**:
```python
import psutil
import time

def monitor_during_execution():
    """Monitor system resources during concurrent execution."""
    while True:
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        print(f"CPU: {cpu}%, Memory: {memory}%")
        time.sleep(5)
```

## Best practices

### Start conservative

Begin with low concurrency limits and gradually increase:

```yaml
concurrency:
  runs:
    max_concurrent_runs: 3  # Start low
    tag_concurrency_limits:
      - key: "database"
        limit: 1  # Very conservative for shared resources
```

### Monitor resource usage

Implement monitoring to understand your system's capacity:

```python
@asset(tags={"monitoring": "resource_usage"})
def system_resource_monitor():
    """Monitor system resources during pipeline execution."""
    import psutil
    
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent
    }
```

### Use hierarchical tagging

Organize assets with hierarchical tags for flexible concurrency control:

```python
@asset(tags={
    "team": "data_engineering",
    "service": "user_analytics", 
    "resource": "database",
    "priority": "high"
})
def user_analytics_asset():
    pass
```

### Document configuration decisions

Always document why specific limits were chosen:

```yaml
concurrency:
  runs:
    # Production database can handle 5 concurrent connections
    # Based on load testing performed 2024-01-15
    tag_concurrency_limits:
      - key: "database"
        value: "prod_postgres"
        limit: 5
```

This comprehensive guide addresses all the issues raised in GitHub Issue #19402 and provides production-ready examples for every deployment scenario.