# dagster.yaml Reference

The `dagster.yaml` file is used to configure the Dagster instance. It defines various settings for storage, run execution, logging, and other aspects of a Dagster deployment.

## File Location

By default, Dagster looks for the `dagster.yaml` file in the directory specified by the `DAGSTER_HOME` environment variable.

## Using Environment Variables

You can use environment variables to override values in the `dagster.yaml` file.

```yaml
instance:
  module: dagster.core.instance
  class: DagsterInstance
  config:
    some_key:
      env: ME_ENV_VAR
```

## Full Configuration Specification

Here's a comprehensive `dagster.yaml` specification with all available options:

```yaml
local_artifact_storage:
  module: dagster.core.storage.root
  class: LocalArtifactStorage
  config:
    base_dir: '/path/to/dir'

compute_logs:
  module: dagster.core.storage.local_compute_log_manager
  class: LocalComputeLogManager
  config:
    base_dir: /path/to/compute/logs

# Alternatively, logs can be written to cloud storage providers like S3, GCS, and Azure blog storage. For example:
# compute_logs:
#   module: dagster_aws.s3.compute_log_manager
#   class: S3ComputeLogManager
#   config:
#     bucket: "mycorp-dagster-compute-logs"
#    prefix: "dagster-test-"

storage:
  sqlite:
    base_dir: /path/to/sqlite/storage
  # Or use postgres:
  # postgres:
  #   postgres_db:
  #     hostname: localhost
  #     username: dagster
  #     password: dagster
  #     db_name: dagster
  #     port: 5432

run_queue:
  max_concurrent_runs: 15
  tag_concurrency_limits:
    - key: 'database'
      value: 'redshift'
      limit: 4
    - key: 'dagster/backfill'
      limit: 10

run_storage:
  module: dagster.core.storage.runs
  class: SqliteRunStorage
  config:
    base_dir: /path/to/dagster/home/history

event_log_storage:
  module: dagster.core.storage.event_log
  class: SqliteEventLogStorage
  config:
    base_dir: /path/to/dagster/home/history

schedule_storage:
  module: dagster.core.storage.schedules
  class: SqliteScheduleStorage
  config:
    base_dir: /path/to/dagster/home/schedules

scheduler:
  module: dagster.core.scheduler
  class: DagsterDaemonScheduler

run_coordinator:
  module: dagster.core.run_coordinator
  class: DefaultRunCoordinator
  # class: QueuedRunCoordinator
  # config:
  #   max_concurrent_runs: 25
  #   tag_concurrency_limits:
  #     - key: "dagster/backfill"
  #       value: "true"
  #       limit: 1

run_launcher:
  module: dagster.core.launcher
  class: DefaultRunLauncher
  # module: dagster_docker
  # class: DockerRunLauncher
  # module: dagster_k8s.launcher
  # class: K8sRunLauncher
  # config:
  #   service_account_name: pipeline_run_service_account
  #   job_image: my_project/dagster_image:latest
  #   instance_config_map: dagster-instance
  #   postgres_password_secret: dagster-postgresql-secret

telemetry:
  enabled: true

run_monitoring:
  enabled: true
  poll_interval_seconds: 60

run_retries:
  enabled: true
  max_retries: 3
  retry_on_asset_or_op_failure: true

code_servers:
  local_startup_timeout: 360

secrets:
  my_secret:
    env: MY_SECRET_ENV_VAR

retention:
  schedule:
    purge_after_days: 90
  sensor:
    purge_after_days:
      skipped: 7
      failure: 30
      success: -1

sensors:
  use_threads: true
  num_workers: 8

schedules:
  use_threads: true
  num_workers: 8

auto_materialize:
  enabled: true
  minimum_interval_seconds: 3600
  run_tags:
    key: 'value'
  respect_materialization_data_versions: true
  max_tick_retries: 3
  use_sensors: false
  use_threads: false
  num_workers: 4
```

## Configuration Options

### `storage`

Configures how job and asset history is persisted.

```yaml
storage:
  sqlite:
    base_dir: /path/to/sqlite/storage
```

Options:

- `sqlite`: Use SQLite for storage
- `postgres`: Use PostgreSQL for storage (requires `dagster-postgres` library)
- `mysql`: Use MySQL for storage (requires `dagster-mysql` library)

### `run_launcher`

Determines where runs are executed.

```yaml
run_launcher:
  module: dagster.core.launcher
  class: DefaultRunLauncher
```

Options:

- `DefaultRunLauncher`: Spawns a new process on the same node as the job's code location
- `DockerRunLauncher`: Allocates a Docker container per run
- `K8sRunLauncher`: Allocates a Kubernetes job per run

### `run_coordinator`

Sets prioritization rules and concurrency limits for runs.

```yaml
run_coordinator:
  module: dagster.core.run_coordinator
  class: QueuedRunCoordinator
  config:
    max_concurrent_runs: 25
```

Options:

- `DefaultRunCoordinator`: Immediately sends runs to the run launcher
- `QueuedRunCoordinator`: Allows setting limits on concurrent runs

### `compute_logs`

Controls the capture and persistence of stdout and stderr logs.

```yaml
compute_logs:
  module: dagster.core.storage.local_compute_log_manager
  class: LocalComputeLogManager
  config:
    base_dir: /path/to/compute/logs
```

Options:

- `LocalComputeLogManager`: Writes logs to disk
- `NoOpComputeLogManager`: Does not store logs
- `AzureBlobComputeLogManager`: Writes logs to Azure Blob Storage
- `GCSComputeLogManager`: Writes logs to Google Cloud Storage
- `S3ComputeLogManager`: Writes logs to AWS S3

### `local_artifact_storage`

Configures storage for artifacts that require a local disk or when using the filesystem I/O manager.

```yaml
local_artifact_storage:
  module: dagster.core.storage.root
  class: LocalArtifactStorage
  config:
    base_dir: /path/to/artifact/storage
```

### `telemetry`

Controls whether Dagster collects anonymized usage statistics.

```yaml
telemetry:
  enabled: false
```

### `code_servers`

Configures how Dagster loads code in a code location.

```yaml
code_servers:
  local_startup_timeout: 360
```

### `retention`

Configures how long Dagster retains certain types of data.

```yaml
retention:
  schedule:
    purge_after_days: 90
  sensor:
    purge_after_days:
      skipped: 7
      failure: 30
      success: -1
```

### `sensors`

Configures how sensors are evaluated.

```yaml
sensors:
  use_threads: true
  num_workers: 8
```

### `schedules`

Configures how schedules are evaluated.

```yaml
schedules:
  use_threads: true
  num_workers: 8
```

### `auto_materialize`

Configures automatic materialization of assets.

```yaml
auto_materialize:
  enabled: true
  minimum_interval_seconds: 3600
  run_tags:
    key: 'value'
  respect_materialization_data_versions: true
  max_tick_retries: 3
  use_sensors: false
  use_threads: false
  num_workers: 4
```

Options:

- `enabled`: Whether auto-materialization is enabled (boolean)
- `minimum_interval_seconds`: Minimum interval between materializations (integer)
- `run_tags`: Tags to apply to auto-materialization runs (dictionary)
- `respect_materialization_data_versions`: Whether to respect data versions when materializing (boolean)
- `max_tick_retries`: Maximum number of retries for each auto-materialize tick that raises an error (integer, default: 3)
- `use_sensors`: Whether to use sensors for auto-materialization (boolean)
- `use_threads`: Whether to use threads for processing ticks (boolean, default: false)
- `num_workers`: Number of threads to use for processing ticks from multiple automation policy sensors in parallel (integer)

### `concurrency`

Configures default concurrency limits for operations.

```yaml
concurrency:
  default_op_concurrency_limit: 10
```

Options:

- `default_op_concurrency_limit`: The default maximum number of concurrent operations for an unconfigured concurrency key (integer)

## References

- [Dagster Instance Config Source Code](https://github.com/dagster-io/dagster/blob/master/python_modules/dagster/dagster/_core/instance/config.py)
