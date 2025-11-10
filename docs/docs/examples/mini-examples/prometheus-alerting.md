---
title: Prometheus alerting
description: Different methods for monitoring and observability with Prometheus monitoring.
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/dagster-primary-mark.svg
---

In this example, we'll explore different approaches to implementing [Prometheus](https://prometheus.io/) monitoring in Dagster. Prometheus is a powerful monitoring system that collects metrics from your applications and provides alerting capabilities. When integrated with Dagster, it enables comprehensive observability for your data pipelines, allowing you to track asset execution times, failure rates, and custom business metrics.

## Problem: Limited pipeline observability

Without proper monitoring, data pipeline issues can go unnoticed until they cause downstream problems. Common challenges include:

- **Silent failures**: Assets fail but no one is notified
- **Performance degradation**: Slow assets aren't detected early
- **Lack of business metrics**: No visibility into data quality or business KPIs
- **Manual monitoring**: Checking pipeline health requires manual dashboard reviews

Prometheus monitoring addresses these issues by:

- Automatically collecting and storing metrics
- Providing alerting based on configurable thresholds
- Enabling historical analysis of pipeline performance
- Supporting custom business metrics alongside technical metrics

### Solution 1: Prometheus resource setup

The first step is configuring a Prometheus resource that connects to your Prometheus push gateway. This provides the foundation for all monitoring functionality.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/prometheus_alerting/resources.py"
  language="python"
  title="src/project_mini/defs/prometheus_alerting/resources.py"
  startAfter="start_prometheus_resources"
  endBefore="end_prometheus_resources"
/>

Key configuration parameters:

- **`gateway`**: URL of your Prometheus push gateway
- **`job_name`**: Identifier for your Dagster instance
- **`scrape_interval`**: How often Prometheus collects metrics
- **`scrape_timeout`**: Maximum time to wait for metric collection
- **`evaluation_interval`**: How often alerting rules are evaluated

### Solution 2: Asset monitoring

Once the resource is configured, you can create assets that push basic metrics to Prometheus using the built-in functionality.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/prometheus_alerting/promoetheus_assets.py"
  language="python"
  title="src/project_mini/defs/prometheus_alerting/promoetheus_assets.py"
  startAfter="start_basic_prometheus_asset"
  endBefore="end_basic_prometheus_asset"
/>

This basic approach automatically sends default metrics to Prometheus, including:

- Asset execution start and completion times
- Asset success/failure status
- Job and asset metadata

| Metric Type             | Automatically Collected | Custom Configuration |
| ----------------------- | ----------------------- | -------------------- |
| Execution time          | ✓                       | Not needed           |
| Success/failure         | ✓                       | Not needed           |
| Custom business metrics | ✗                       | Required             |

### Solution 3: Custom metrics and monitoring

For more detailed monitoring, you can define custom Prometheus metrics that track specific aspects of your data pipeline, such as row counts, data quality scores, or processing times.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/prometheus_alerting/promoetheus_assets.py"
  language="python"
  title="src/project_mini/defs/prometheus_alerting/promoetheus_assets.py"
  startAfter="start_custom_metrics_setup"
  endBefore="end_custom_metrics_setup"
/>

This setup defines four custom metrics:

1. **Counter**: `my_asset_runs_total` - tracks total number of executions
2. **Counter**: `my_asset_success_total` - tracks successful executions
3. **Counter**: `my_asset_failure_total` - tracks failed executions
4. **Histogram**: `my_asset_duration_seconds` - tracks execution time distribution

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/prometheus_alerting/promoetheus_assets.py"
  language="python"
  title="src/project_mini/defs/prometheus_alerting/promoetheus_assets.py"
  startAfter="start_custom_prometheus_asset"
  endBefore="end_custom_prometheus_asset"
/>

This pattern provides comprehensive monitoring:

1. **Increment run counter** before processing begins
2. **Time the operation** using the histogram context manager
3. **Track success/failure** with appropriate counters
4. **Push all metrics** to the gateway in the finally block

| Monitoring Level        | Basic Asset | Custom Metrics Asset |
| ----------------------- | ----------- | -------------------- |
| Execution tracking      | ✓           | ✓                    |
| Duration measurement    | Basic       | Detailed histogram   |
| Success/failure rates   | Basic       | Granular counters    |
| Custom business metrics | ✗           | ✓ (configurable)     |

### Solution 4: Failure monitoring with hooks

For comprehensive failure monitoring, you can use Dagster hooks to automatically capture and report detailed failure information to Prometheus, including asset metadata and ownership information.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/prometheus_alerting/promoetheus_failure_hook.py"
  language="python"
  title="src/project_mini/defs/prometheus_alerting/promoetheus_failure_hook.py"
  startAfter="start_failure_hook_factory"
  endBefore="end_failure_hook_factory"
/>

The failure hook implementation captures comprehensive failure context:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/prometheus_alerting/promoetheus_failure_hook.py"
  language="python"
  title="src/project_mini/defs/prometheus_alerting/promoetheus_failure_hook.py"
  startAfter="start_failure_hook_implementation"
  endBefore="end_failure_hook_implementation"
/>

Key features of the failure hook:

1. **Asset owner extraction**: Retrieves owner information from asset metadata
2. **Failure timestamp**: Records exact time of failure for alerting
3. **Custom registry**: Creates isolated metrics to avoid conflicts
4. **Comprehensive logging**: Provides detailed failure information

The hook creates labeled metrics for detailed failure tracking:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/prometheus_alerting/promoetheus_failure_hook.py"
  language="python"
  title="src/project_mini/defs/prometheus_alerting/promoetheus_failure_hook.py"
  startAfter="start_prometheus_metrics_creation"
  endBefore="end_prometheus_metrics_creation"
/>

These metrics enable sophisticated alerting rules:

- **`dagster_asset_failures_total`**: Counter with labels for asset name, owner, and job
- **`dagster_asset_last_failure_timestamp`**: Gauge showing when each asset last failed

The hook safely pushes metrics to the Prometheus gateway:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/prometheus_alerting/promoetheus_failure_hook.py"
  language="python"
  title="src/project_mini/defs/prometheus_alerting/promoetheus_failure_hook.py"
  startAfter="start_push_to_gateway"
  endBefore="end_push_to_gateway"
/>

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/prometheus_alerting/promoetheus_failure_hook.py"
  language="python"
  title="src/project_mini/defs/prometheus_alerting/promoetheus_failure_hook.py"
  startAfter="start_hook_usage_example"
  endBefore="end_hook_usage_example"
/>

The hook is attached to assets using the `op_tags` parameter with the `dagster/failure_hook` key.
