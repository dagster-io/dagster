---
title: Observing streaming processes
description: Monitoring external Kafka and streaming infrastructure in Dagster without managing the streams directly.
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/dagster-primary-mark.svg
---

In this example, we'll explore how to observe external streaming processes (like Kafka or Azure Event Hub) in Dagster. When you have existing streaming infrastructure managed outside of Dagster, you can still incorporate it into your data lineage, monitor its health, and trigger downstream processing based on stream freshness—all without migrating the stream itself into Dagster.

## Problem: Integrating external streaming infrastructure

Imagine your organization has existing Kafka topics or Azure Event Hub streams that are managed by a dedicated streaming team. These streams feed data into your batch processing pipelines, but they live outside Dagster's control. Without proper integration, you face several challenges:

- **Invisible dependencies**: Downstream assets depend on stream data, but this relationship isn't visible in your asset graph.
- **Manual monitoring**: Stream health (consumer lag, throughput) must be checked separately from your data platform.
- **Schedule-based processing**: Batch jobs run on fixed schedules rather than when fresh data is actually available.
- **Inconsistent metadata**: Each team documents streams differently, making discovery difficult.

You can incorporate external streams into Dagster's asset graph for visibility, monitoring, and data-driven orchestration in different ways depending on the scenario:

| Scenario                                        | Pattern                                             |
| ----------------------------------------------- | --------------------------------------------------- |
| Show stream in asset graph                      | [External asset](#pattern-1-external-asset)         |
| Consistently manage multiple streams            | [Reusable component](#pattern-2-reusable-component) |
| Track stream health over time                   | [Observation sensor](#pattern-3-observation-sensor) |
| Trigger batch processing when data is available | [Freshness trigger](#pattern-4-freshness-trigger)   |

## Pattern 1: External asset

Use <PyObject section="assets" module="dagster" object="AssetSpec" /> to define an external asset representing a Kafka topic or Event Hub stream. External assets appear in the asset graph but cannot be materialized by Dagster, since they represent infrastructure you don't own. You can include metadata, such as connection details and ownership information, and add kind tags (such as `kafka`, `streaming`, and so on) that will appear in the UI.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/observing_streaming_processes/external_kafka_asset.py"
  language="python"
  title="src/project_mini/defs/observing_streaming_processes/external_kafka_asset.py"
/>

## Pattern 2: Reusable component

When you have multiple Kafka topics or Event Hub streams to observe, you can [create a component](/guides/build/components/creating-new-components/creating-and-registering-a-component) to provide a reusable, YAML-configurable pattern. This allows teams to declare new external streams without writing Python code, ensures external streams follow the same pattern with standardized metadata. Additionally, the component validates inputs and provides IDE support.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/observing_streaming_processes/external_kafka_component.py"
  language="python"
  title="src/project_mini/defs/observing_streaming_processes/external_kafka_component.py"
/>

With this component defined and registered, teams can declare external streams in YAML:

```yaml
# component.yaml
type: external_kafka_asset
attributes:
  asset_key: claims_stream
  topic: insurance-claims-v1
  broker: kafka.internal.company.com:9092
  group_name: streaming
```

### Pattern 3: Observation sensor

## Pattern 3: Observation sensor

Create a [sensor](/guides/automate/sensors) that monitors the external stream and emits observations. Observations create a time-series record of stream health without materializing the asset.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/observing_streaming_processes/observation_sensor.py"
  language="python"
  title="src/project_mini/defs/observing_streaming_processes/observation_sensor.py"
/>

The sensor:

- **Checks stream health**: Query Kafka for consumer lag, throughput, and partition status
- **Emits AssetObservation**: Records metrics without triggering materialization
- **Runs periodically**: Default interval prevents overwhelming the Kafka admin API

In production, you would query actual Kafka metrics using a library like `confluent-kafka`:

```python
from confluent_kafka.admin import AdminClient

admin = AdminClient({'bootstrap.servers': 'kafka.internal.company.com:9092'})
# Query consumer groups, offsets, and topic metadata
```

## Pattern 4: Freshness trigger

Create a [sensor](/guides/automate/sensors) that triggers downstream processing only when fresh data is available. This enables data-driven orchestration instead of fixed schedules.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/observing_streaming_processes/freshness_trigger_sensor.py"
  language="python"
  title="src/project_mini/defs/observing_streaming_processes/freshness_trigger_sensor.py"
/>

The sensor triggers runs only when message count and consumer lag meet your thresholds, so processing is driven by actual data availability rather than a fixed schedule. When conditions aren't met, it emits clear skip reasons that make it easier to debug why a run was skipped.

## Key considerations

- **Observation vs Materialization**: Observations record metadata about external state; they don't create data. Use them for monitoring, not processing.
- **Sensor intervals**: Balance between freshness and API load. 60-120 seconds is often appropriate for Kafka monitoring.
- **Stream health thresholds**: Customize lag and throughput thresholds based on your SLAs.
- **External asset benefits**: Even without materialization, external assets provide lineage visibility, documentation, and enable freshness-based automation.
