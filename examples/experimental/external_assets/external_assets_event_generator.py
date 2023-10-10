import datetime
import json
import os
import random
import time
import uuid

import requests

IS_CLOUD = os.getenv("USE_DAGSTER_CLOUD", "false").lower() in ["true", "1", "t"]
CLOUD_API_TOKEN = os.getenv("DAGSTER_CLOUD_TOKEN", "user:test:joe")


def create_external_asset_materialization(data):
    if IS_CLOUD:
        url = "http://localhost:3000/test/report_asset_materialization/"
        headers = {"content-type": "application/json", "Dagster-Cloud-Api-Token": CLOUD_API_TOKEN}
    else:
        url = "http://localhost:3000/report_asset_materialization/"
        headers = {"content-type": "application/json"}
    response = requests.post(
        url=url,
        data=json.dumps(data),
        headers=headers,
    )

    if response.status_code != 200:
        print(  # noqa: T201
            f"Failed to create materialization. Status Code: {response.status_code}, Message: {response.text}"
        )


def main():
    today = datetime.datetime.today() - datetime.timedelta(days=100)

    create_external_asset_materialization(
        {
            "uri": "s3://iot-s3-bucket/admin_boundaries/boundaries.geojson",
            "asset_key": ["static", "admin_boundaries"],
            "data_version": "60bc881",
            "description": "boundary data for administrative regions for iot processing",
            "metadata": {
                "uri": "s3://iot-s3-bucket/admin_boundaries/boundaries.geojson",
                "size": random.randint(10000 * 1000, 5 * 10000 * 1000),
            },
        }
    )
    while True:
        synthetic_s3_data = [
            {
                "uri": f"s3://iot-s3-bucket-apac/raw_traces/dt={today.strftime('%d-%m-%Y')}/{uuid.uuid4()}.pbf",
                "asset_key": ["s3", "iot_raw_telem_apac"],
                "partition": today.strftime("%Y-%m-%d"),
                "data_version": "60bc881",
                "description": "iot device traces from apac",
                "metadata": {
                    "uri": f"s3://iot-s3-bucket-apac/raw_traces/dt={today.strftime('%d-%m-%Y')}/{uuid.uuid4()}.pbf",
                    "size": random.randint(10000 * 1000, 5 * 10000 * 1000),
                },
            },
            {
                "uri": f"s3://iot-s3-bucket-eu/raw_traces/dt={today.strftime('%d-%m-%Y')}/{uuid.uuid4()}.pbf",
                "asset_key": ["s3", "iot_raw_telem_eu"],
                "partition": today.strftime("%Y-%m-%d"),
                "data_version": "60bc881",
                "description": "iot device traces from eu",
                "metadata": {
                    "uri": f"s3://iot-s3-bucket-eu/raw_traces/dt={today.strftime('%d-%m-%Y')}/{uuid.uuid4()}.pbf",
                    "size": random.randint(10000 * 1000, 5 * 10000 * 1000),
                },
            },
            {
                "uri": f"s3://iot-s3-bucket-americas/raw_traces/dt={today.strftime('%d-%m-%Y')}/{uuid.uuid4()}.pbf",
                "asset_key": ["s3", "iot_raw_telem_americas"],
                "partition": today.strftime("%Y-%m-%d"),
                "data_version": "60bc881",
                "description": "iot device traces from americas",
                "metadata": {
                    "uri": f"s3://iot-s3-bucket-americas/raw_traces/dt={today.strftime('%d-%m-%Y')}/{uuid.uuid4()}.pbf",
                    "size": random.randint(10000 * 1000, 5 * 10000 * 1000),
                },
            },
            {
                "uri": f"s3://iot-s3-bucket-apac/scrubbed_traces/dt={today.strftime('%d-%m-%Y')}/{uuid.uuid4()}.pbf",
                "asset_key": ["s3", "iot_scrubbed_telem_apac"],
                "partition": today.strftime("%Y-%m-%d"),
                "data_version": "60bc881",
                "description": "scrubbed iot device traces from apac",
                "metadata": {
                    "uri": f"s3://iot-s3-bucket-apac/scrubbed_traces/dt={today.strftime('%d-%m-%Y')}/{uuid.uuid4()}.pbf",
                    "size": random.randint(10000 * 1000, 5 * 10000 * 1000),
                },
            },
            {
                "uri": f"s3://iot-s3-bucket-eu/scrubbed_traces/dt={today.strftime('%d-%m-%Y')}/{uuid.uuid4()}.pbf",
                "asset_key": ["s3", "iot_scrubbed_telem_eu"],
                "partition": today.strftime("%Y-%m-%d"),
                "data_version": "60bc881",
                "description": "scrubbed iot device traces from eu",
                "metadata": {
                    "uri": f"s3://iot-s3-bucket-eu/scrubbed_traces/dt={today.strftime('%d-%m-%Y')}/{uuid.uuid4()}.pbf",
                    "size": random.randint(10000 * 1000, 5 * 10000 * 1000),
                },
            },
            {
                "uri": f"s3://iot-s3-bucket-americas/scrubbed_traces/dt={today.strftime('%d-%m-%Y')}/{uuid.uuid4()}.pbf",
                "asset_key": ["s3", "iot_scrubbed_telem_americas"],
                "partition": today.strftime("%Y-%m-%d"),
                "data_version": "60bc881",
                "description": "scrubbed iot device traces from americas",
                "metadata": {
                    "uri": f"s3://iot-s3-bucket-americas/scrubbed_traces/dt={today.strftime('%d-%m-%Y')}/{uuid.uuid4()}.pbf",
                    "size": random.randint(10000 * 1000, 5 * 10000 * 1000),
                },
            },
            {
                "uri": f"s3://vendor-foo-bucket/traces/dt={today.strftime('%d-%m-%Y')}/{uuid.uuid4()}.json",
                "asset_key": ["vendors", "telem_vendor_foo"],
                "partition": today.strftime("%Y-%m-%d"),
                "data_version": "60bc881",
                "description": "vendor trace data",
                "metadata": {
                    "uri": f"s3://vendor-foo-bucket/traces/dt={today.strftime('%d-%m-%Y')}/{uuid.uuid4()}.json",
                    "size": random.randint(10000 * 1000, 5 * 10000 * 1000),
                },
            },
            {
                "uri": f"s3://vendor-bar-bucket/traces/dt={today.strftime('%d-%m-%Y')}/{uuid.uuid4()}.json",
                "asset_key": ["vendors", "telem_vendor_bar"],
                "partition": today.strftime("%Y-%m-%d"),
                "data_version": "60bc881",
                "description": "vendor trace data",
                "metadata": {
                    "uri": f"s3://vendor-bar-bucket/traces/dt={today.strftime('%d-%m-%Y')}/{uuid.uuid4()}.json",
                    "size": random.randint(10000 * 1000, 5 * 10000 * 1000),
                },
            },
            {
                "uri": f"s3://iot-s3-bucket/joined_traces/dt={today.strftime('%d-%m-%Y')}/{uuid.uuid4()}.json",
                "asset_key": ["s3", "joined_sensor_telem"],
                "partition": today.strftime("%Y-%m-%d"),
                "data_version": "60bc881",
                "description": "joined trace data",
                "metadata": {
                    "uri": f"s3://iot-s3-bucket/joined_traces/dt={today.strftime('%d-%m-%Y')}/{uuid.uuid4()}.json",
                    "size": random.randint(10000 * 1000, 5 * 10000 * 1000) * 10,
                },
            },
        ]
        for data in synthetic_s3_data:
            print(  # noqa: T201
                f"Creating asset materialization for s3 object put event ({data['uri']})"
            )
            create_external_asset_materialization(data)
            time.sleep(1)
        time.sleep(30)
        today = today + datetime.timedelta(days=1)


if __name__ == "__main__":
    main()
