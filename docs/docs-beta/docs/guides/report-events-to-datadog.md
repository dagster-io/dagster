---
title: Log Dagster events to Datadog
description: Learn how to report Dagster events to Datadog
sidebar_label: Log Events to Datadog
---

It's possible to monitor the events that occur in Dagster through Datadog by implementing a custom sensor; a mapping occurs between the Dagster event, and then the event is logged.

<details>
<summary>Prerequisites</summary>

To follow this guide, you'll need:

- Familiarity with [Assets](/concepts/sensors)
</details>

## Creating a custom sensor

First, we create a method that polls the Dagster instance for all events that have occurred since the last invocation of the sensor. The method `poll_instance_for_latest_events` is defined which takes in a `DagsterInstance`, the previous `cursor` value, and additional arguments for filtering of events.


```python title="poll_instance.py"
from typing import List

from dagster import (
    AssetKey,
    DagsterEventType,
    DagsterInstance,
    EventLogRecord,
    EventRecordsFilter,
)

DEFAULT_MONITORED_EVENT_TYPES = [
    DagsterEventType.ASSET_MATERIALIZATION,
    DagsterEventType.STEP_FAILURE,
    DagsterEventType.STEP_SUCCESS,
    DagsterEventType.STEP_SKIPPED,
    DagsterEventType.PIPELINE_SUCCESS,
    DagsterEventType.PIPELINE_FAILURE,
    DagsterEventType.ASSET_CHECK_EVALUATION,
]


def poll_instance_for_latest_events(
    instance: DagsterInstance,
    cursor: int | None = None,
    asset_key: AssetKey | None = None,
    event_types: List[DagsterEventType] = DEFAULT_MONITORED_EVENT_TYPES,
    limit: int = 500,
) -> List[EventLogRecord]:
    "Takes a Dagster instance and fetches the latest records from it."
    all_events: List[EventLogRecord] = []
    for t in event_types:
        matched = instance.get_event_records(
            EventRecordsFilter(
                asset_key=asset_key,
                event_type=t,
                after_cursor=cursor,
            ),
            ascending=False,
            limit=limit,
        )
        all_events.extend(matched)
    return all_events
```

We then make use of the `poll_instance_for_latest_events` method in our sensor definition. Polling for all of the events, mapping them to a Datadog event type, and then logging them to Datadog using the `log_datadog_asset_event` function.

```python title="sensor.py"
import json
from typing import List

import pydantic
from dagster import (
    DagsterEventType,
    EventLogRecord,
    SensorEvaluationContext,
    SkipReason,
    build_resources,
    get_dagster_logger,
    sensor,
)
from datadog import DogStatsd
from datadog_api_client.exceptions import ApiException
from datadog_api_client.v1.model.event_create_request import EventCreateRequest
from datadog_api_client.v2.model.metric_intake_type import MetricIntakeType
from datadog_api_client.v2.model.metric_payload import MetricPayload
from datadog_api_client.v2.model.metric_point import MetricPoint
from datadog_api_client.v2.model.metric_resource import MetricResource
from datadog_api_client.v2.model.metric_series import MetricSeries

from .resources.datadog import (
    DatadogApiResource,
)

from .utils.sensors import poll_instance_for_latest_events


statsd = DogStatsd()



class DatadogDagsterAssetEvent(pydantic.BaseModel):
    "Maps a Dagster AssetMaterialization event to a Datadog event."

    event_name: str = "AssetMaterialization"
    asset_key: str
    job_name: str
    job_run_id: str
    message: str
    event_timestamp: int
    is_success: bool = True

    @property
    def tags(self) -> List[str]:
        return [
            f"asset_key:{self.asset_key}",
            f"event_name:{self.event_name}",
            f"success:{self.is_success}",
            f"environment:{CURRENT_DEPLOYMENT}",
        ]

    @property
    def aggregation_key(self) -> str:
        if len(self.asset_key) < 100:
            return self.asset_key
        return self.asset_key[:100]

    def to_event_create_request(self) -> EventCreateRequest:
        return EventCreateRequest(
            title=f"dagster.{self.event_name.lower()}",
            text=json.dumps(self.dict(), indent=2),
            tags=self.tags,
            date_happened=self.event_timestamp,
            priority="normal",
            source_type_name="dagster",
            aggregation_key=self.aggregation_key,
        )



def extract_asset_attributes(
    event_record: EventLogRecord,
) -> DatadogDagsterAssetEvent:
    "Casts a Dagster Asset event into a DatadogDagsterAssetEvent."

    # Cast the event_log_entry to json and then re-read as a dict
    # so that custom Dagster classes are converted to dicts.
    entry_dict = json.loads(event_record.event_log_entry.to_json())

    event_dict = entry_dict["dagster_event"]["event_specific_data"]

    # this operation is equivalent to `AssetKey.to_user_string()`
    asset_key = "/".join(event_dict["materialization"]["asset_key"]["path"])

    return DatadogDagsterAssetEvent(
        event_name=entry_dict["dagster_event"]["event_type_value"],
        asset_key=asset_key,
        job_name=entry_dict["dagster_event"]["pipeline_name"],
        job_run_id=entry_dict["run_id"],
        event_timestamp=int(entry_dict["timestamp"]),
        message=entry_dict["user_message"],
    )



def log_datadog_asset_event(
    datadog_api_resource: DatadogApiResource, event: DatadogDagsterAssetEvent
):
    "Pushes an asset completion event to Datadog."

    body = event.to_event_create_request()

    try:
        datadog_api_resource.create_event(body=body)
    except ApiException as e:
        logger.error(e)


@sensor(
    default_status=default_sensor_status,
)
def dagster_cloud_asset_sensor(context: SensorEvaluationContext):
    current_cursor = int(context.cursor) if context.cursor else None

    matched_events = poll_instance_for_latest_events(
        instance=context.instance,
        event_types=[DagsterEventType.ASSET_MATERIALIZATION],
        cursor=current_cursor,
        limit=200,
    )
    context.log.info("Count of events: %s", len(matched_events))

    with build_resources(required_resources) as r:
        for event_record in matched_events:
            event = extract_asset_attributes(event_record)
            context.log.info(
                "Logging materialization event for asset %s.", event.asset_key
            )
            log_datadog_asset_event(r.datadog_api, event)

    if len(matched_events) > 0:
        max_id = max(r.storage_id for r in matched_events)
        context.update_cursor(str(max_id))
        yield SkipReason(
            f"Submitted {len(matched_events)} asset events to Datadog."
        )
    else:
        yield SkipReason("No run completions detected.")
```
