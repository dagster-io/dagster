import json
import os

import requests

DAGSTER_URL = os.getenv("DAGSTER_CLOUD_API_TOKEN")


def lambda_handler(event, context):
    # Extract bucket and object key from the S3 event
    for record in event["Records"]:
        key = record["s3"]["object"]["key"]
        path_values = key.split("/")
        url = f"{DAGSTER_URL}/report_asset_materialization/"
        headers = {"content-type": "application/json"}

        response = requests.post(
            url=url,
            data=json.dumps(
                {
                    "asset_key": path_values[0],
                    "partition": path_values[1],
                }
            ),
            headers=headers,
        )
        response.raise_for_status()
