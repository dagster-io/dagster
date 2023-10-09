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
        print(
            f"Failed to create materialization. Status Code: {response.status_code}, Message: {response.text}"
        )


def main():
    today = datetime.datetime.today() - datetime.timedelta(days=100)
    while True:
        synthetic_s3_data = [
            {
                "uri": f"s3://cdn-logs-s3-bucket/cdn_raw_logs/dt={today.strftime('%d-%m-%Y')}/{uuid.uuid4()}.log",
                "asset_key": ["cdn", "raw_logs"],
                "partition": today.strftime("%Y-%m-%d"),
                "data_version": "60bc881",
                "description": "raw cdn logs from cloudfront",
                "metadata": {"size": random.randint(10000 * 1000, 5 * 10000 * 1000)},
            },
            {
                "uri": f"s3://cdn-logs-s3-bucket/cdn_processed_logs/dt={today.strftime('%d-%m-%Y')}/{uuid.uuid4()}.log.gz",
                "asset_key": ["cdn", "processed_logs"],
                "partition": today.strftime("%Y-%m-%d"),
                "data_version": "60bc881",
                "description": "processed cdn logs from cloudfront",
                "metadata": {"size": random.randint(1000 * 1000, 5 * 1000 * 1000)},
            },
        ]
        for data in synthetic_s3_data:
            print(f"Creating asset materialization for s3 object put event ({data['uri']})")
            create_external_asset_materialization(data)
            time.sleep(2)
        time.sleep(2)
        today = today + datetime.timedelta(days=1)


if __name__ == "__main__":
    main()
