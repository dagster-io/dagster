
import os
import json
import requests
from dagster import asset

@asset
def ping_integration():
    # This is using k8 secrets
    api_token = os.environ['NOTEABLE_TOKEN']
    domain = os.environ['NOTEABLE_DOMAIN']
    print(domain)
    headers = requests.utils.default_headers()
    headers.update(
        {
            "Authorization": f"Bearer {api_token}"
        }
    )
    print(headers)

    r = requests.get(f"https://{domain}/gate/api/spaces?limit=10&with_deleted=false", headers=headers)
    r.raise_for_status()
    spaces = r.json()
    print(json.dumps(spaces, indent=4))
    return spaces
