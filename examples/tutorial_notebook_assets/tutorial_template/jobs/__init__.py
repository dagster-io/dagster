import json
import os

import requests
from dagster import job, op

# This file contains a helper job to confirm that you can connect to Noteable


@op
def ping_noteable_op(context):
    api_token = os.environ["NOTEABLE_TOKEN"]
    domain = os.getenv("NOTEABLE_DOMAIN", "app.noteable.io")
    headers = requests.utils.default_headers()
    headers.update({"Authorization": f"Bearer {api_token}"})

    r = requests.get(
        f"https://{domain}/gate/api/spaces?limit=10&with_deleted=false", headers=headers
    )
    r.raise_for_status()
    spaces = r.json()
    context.log.info(json.dumps(spaces, indent=4))
    return spaces


@job
def ping_noteable():
    ping_noteable_op()
