---
title: Lambda run launcher
description: Running Dagster jobs on AWS Lambda instead of containers.
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/dagster-primary-mark.svg
---

In this example, we'll explore how to run Dagster jobs on [AWS Lambda functions](https://aws.amazon.com/pm/lambda/) instead of spinning up new ECS tasks or containers. This approach is useful for lightweight, configuration-driven jobs that benefit from Lambda's instant startup time.

| Factor           | Lambda                            | ECS/Kubernetes                   |
| ---------------- | --------------------------------- | -------------------------------- |
| **Startup time** | Sub-second                        | 30-60 seconds                    |
| **Max runtime**  | 15 minutes                        | Unlimited                        |
| **Dependencies** | Pre-packaged in Lambda            | Full Python environment          |
| **Concurrency**  | Thousands of parallel invocations | Limited by cluster capacity      |
| **Best for**     | API calls, webhooks, quick tasks  | Heavy compute, long-running jobs |

## Problem: Instant job execution for lightweight workloads

Imagine you have jobs that invoke external APIs, trigger webhooks, or perform quick data validations. These jobs spend more time waiting for containers to start than actually executing. You want sub-second startup times while maintaining full Dagster orchestration.

The key question is: How can you route certain jobs to Lambda for instant execution while keeping heavier workloads on traditional compute?

| Solution                                                                    | Best for                                                                     |
| --------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| [Basic Lambda job](#solution-1-basic-lambda-job-configuration)              | New Lambda functions, simple invocations, async fire-and-forget              |
| [Multi-agent architecture](#solution-2-multi-agent-architecture)            | Mixed workloads requiring both Lambda and ECS/Kubernetes compute             |
| [Wrapping existing Lambdas](#solution-3-wrapping-existing-lambda-functions) | Existing Lambda functions with specific payload formats, zero-code migration |

## Solution 1: Basic Lambda job configuration

Configure a job to run on Lambda by adding tags that specify the Lambda function name and invocation type. The Lambda run launcher reads these tags and invokes the appropriate function.

### Async invocation (fire and forget)

Use `invocation_type: "Event"` for fire-and-forget execution. The job triggers the Lambda and returns immediately without waiting for a response. This is ideal for triggering webhooks, sending notifications, or kicking off background processes.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/lambda_run_launcher/basic_lambda_job.py"
  language="python"
  title="Async Lambda invocation"
  startAfter="start_async_lambda_job"
  endBefore="end_async_lambda_job"
/>

### Sync invocation (wait for response)

Use `invocation_type: "RequestResponse"` when you need to wait for the Lambda to complete and return a result. This is useful when subsequent steps depend on the Lambda's output or when you need to capture errors.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/lambda_run_launcher/basic_lambda_job.py"
  language="python"
  title="Sync Lambda invocation"
  startAfter="start_sync_lambda_job"
  endBefore="end_sync_lambda_job"
/>

### Using Lambda ARN

Instead of a function name, you can specify the full Lambda ARN using the `lambda/function_arn` tag. This is useful when invoking Lambda functions in different AWS accounts or regions.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/lambda_run_launcher/basic_lambda_job.py"
  language="python"
  title="Lambda ARN-based job"
  startAfter="start_arn_lambda_job"
  endBefore="end_arn_lambda_job"
/>

### Multi-op ETL job

Lambda jobs can have multiple ops with dependencies. The entire job graph is passed to Lambda, which executes the ops in order. This works well for lightweight ETL pipelines where each step is configuration-driven.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/lambda_run_launcher/basic_lambda_job.py"
  language="python"
  title="Multi-op ETL job"
  startAfter="start_etl_lambda_job"
  endBefore="end_etl_lambda_job"
/>

### Lambda handler

The Lambda function receives a payload containing run metadata, job configuration, and environment variables. The handler extracts the ops configuration and processes each op:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/lambda_run_launcher/basic_lambda_handler.py"
  language="python"
  title="Lambda handler for Dagster jobs"
/>

The payload includes:

- `dagster_run`: Run metadata (run_id, job_name, deployment_name, location_name)
- `run_config`: Job configuration including ops config
- `environment_variables`: Environment context from Dagster Cloud
- `dagster_cloud`: Organization and deployment IDs
- `metadata`: Launcher metadata (launched_at, launcher_version)

## Solution 2: Multi-agent architecture

Since each Dagster agent supports only one run launcher, use multiple agents with queue routing to handle both Lambda and traditional compute workloads. Code locations specify which agent queue they target.

### Lambda agent jobs

Lambda is ideal for lightweight, configuration-driven jobs that complete quickly:

- **API triggers**: Call external APIs, webhooks, or notifications
- **Event dispatchers**: Send messages to SQS, SNS, or EventBridge
- **Data checks**: Quick validation or existence checks
- **Orchestration triggers**: Kick off downstream processes

These jobs benefit from Lambda's sub-second startup time and pay-per-invocation pricing.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/lambda_run_launcher/lambda_agent_jobs.py"
  language="python"
  title="Lambda agent jobs"
/>

### ECS agent jobs

ECS (or Kubernetes) is better suited for jobs that need:

- **Python dependencies**: pandas, scikit-learn, pytorch, spark
- **Long runtimes**: Jobs exceeding Lambda's 15-minute limit
- **Large memory**: Processing datasets larger than Lambda's 10GB limit
- **Custom environments**: Specific Python versions or system packages

These jobs trade slower startup time for full Python environment flexibility.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/lambda_run_launcher/ecs_agent_jobs.py"
  language="python"
  title="ECS agent jobs"
/>

### Queue routing configuration

Configure each code location's `dagster_cloud.yaml` to route to the appropriate agent:

```yaml
# For Lambda jobs
locations:
  - location_name: lambda_jobs
    code_source:
      package_name: lambda_jobs
    agent_queue: lambda # Routes to Lambda agent
```

```yaml
# For ECS/compute-heavy jobs
locations:
  - location_name: python_jobs
    code_source:
      package_name: python_jobs
    agent_queue: ecs # Routes to ECS agent
```

## Solution 3: Wrapping existing Lambda functions

If you have existing Lambda functions that expect a specific payload format, use payload modes to adapt the Dagster run configuration to match what your Lambda expects—no Lambda code changes required.

| Payload mode       | What Lambda receives                                     |
| ------------------ | -------------------------------------------------------- |
| **full** (default) | Complete payload with run metadata, config, and env vars |
| **config_only**    | Just the run_config dictionary                           |
| **ops_only**       | Just the ops config from run_config.ops                  |
| **custom**         | Extract a specific path using `payload_config_path`      |

### Ops-only payload mode

Use `payload_mode='ops_only'` when your Lambda expects the ops configuration structure but not the outer `run_config` wrapper.

Suppose you have an existing Lambda function that expects a payload like:

```json
{
  "copy_files_op": {
    "config": {
      "source_bucket": "my-bucket",
      "destination_bucket": "other-bucket",
      "file_pattern": "*.csv"
    }
  }
}
```

Configure your Dagster job to send exactly this structure:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/lambda_run_launcher/existing_lambda.py"
  language="python"
  title="Ops-only payload mode"
  startAfter="start_ops_only_example"
  endBefore="end_ops_only_example"
/>

Here's how the existing Lambda handler receives and processes this payload:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/lambda_run_launcher/existing_lambda_handler.py"
  language="python"
  title="Lambda handler for ops-only payload"
  startAfter="start_ops_aware_lambda"
  endBefore="end_ops_aware_lambda"
/>

### Custom payload mode

Use `payload_mode='custom'` with `payload_config_path` to extract a specific nested value from your run config. This lets you invoke existing Lambdas that expect a flat configuration object without any Dagster-specific structure.

If your Lambda expects a flat config like `{"api_key": "...", "endpoint": "...", "data": [...]}`, use the `payload_config_path` tag to extract just the op config:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/lambda_run_launcher/existing_lambda.py"
  language="python"
  title="Custom payload mode"
  startAfter="start_custom_example"
  endBefore="end_custom_example"
/>

The Lambda receives exactly what it expects—no Dagster-specific structure:

```json
{
  "api_key": "...",
  "endpoint": "...",
  "data": [...]
}
```

Here's how an existing Lambda handler receives this flat configuration:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/lambda_run_launcher/existing_lambda_handler.py"
  language="python"
  title="Lambda handler for custom payload"
  startAfter="start_simple_existing_lambda"
  endBefore="end_simple_existing_lambda"
/>

### Config-only payload mode

Use `payload_mode='config_only'` when your Lambda expects the full `run_config` dictionary but not the Dagster run metadata. This is useful when your Lambda function is already designed to work with Dagster's run_config structure.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/lambda_run_launcher/existing_lambda.py"
  language="python"
  title="Config-only payload mode"
  startAfter="start_config_only_example"
  endBefore="end_config_only_example"
/>

The Lambda receives the full run_config structure:

```json
{
  "ops": {
    "transform_op": {
      "config": {"input_file": "...", "output_file": "..."}
    },
    "load_op": {
      "config": {"destination": "..."}
    }
  }
}
```

Here's how a Lambda handler processes this structure:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/lambda_run_launcher/existing_lambda_handler.py"
  language="python"
  title="Lambda handler for config-only payload"
  startAfter="start_run_config_lambda"
  endBefore="end_run_config_lambda"
/>

### Real-world example

Here's a complete example of an existing ETL Lambda that can be orchestrated by Dagster without any code changes. The Lambda expects a specific payload format, and Dagster's custom payload mode extracts exactly what it needs:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/lambda_run_launcher/existing_lambda_handler.py"
  language="python"
  title="Real-world ETL Lambda"
  startAfter="start_real_world_etl_lambda"
  endBefore="end_real_world_etl_lambda"
/>
