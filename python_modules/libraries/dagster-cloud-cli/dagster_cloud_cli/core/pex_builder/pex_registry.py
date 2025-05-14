import base64
import json
import os
from tempfile import TemporaryDirectory
from typing import Any, Optional

import requests

from dagster_cloud_cli import gql, ui

GENERATE_PUT_URL_QUERY = """
mutation GenerateServerlessPexUrlMutation($filenames: [String!]!) {
    generateServerlessPexUrl(filenames: $filenames, method:PUT) {
        url
    }
}
"""

GENERATE_GET_URL_QUERY = """
mutation GenerateServerlessPexUrlMutation($filenames: [String!]!) {
    generateServerlessPexUrl(filenames: $filenames, method:GET) {
        url
    }
}
"""


def get_s3_urls_for_put(
    dagster_cloud_url: str, dagster_cloud_api_token: str, filenames: list[str]
) -> Optional[list[str]]:
    with gql.graphql_client_from_url(dagster_cloud_url, dagster_cloud_api_token) as client:
        result = client.execute(
            GENERATE_PUT_URL_QUERY,
            variable_values={"filenames": filenames},
            idempotent_mutation=True,
        )

        if result["data"]:
            return [item["url"] for item in result["data"]["generateServerlessPexUrl"]]
        else:
            return None


def get_s3_urls_for_get(
    dagster_cloud_url: str, dagster_cloud_api_token: str, filenames: list[str]
) -> Optional[list[str]]:
    with gql.graphql_client_from_url(dagster_cloud_url, dagster_cloud_api_token) as client:
        result = client.execute(
            GENERATE_GET_URL_QUERY,
            variable_values={"filenames": filenames},
            idempotent_mutation=True,
        )

        if result["data"]:
            return [item["url"] for item in result["data"]["generateServerlessPexUrl"]]
        else:
            return None


def requirements_hash_filename(requirements_hash: str, cache_tag: Optional[str]):
    # encode cache_tag as a filesystem safe string
    if cache_tag:
        cache_tag_suffix = "-" + base64.urlsafe_b64encode(cache_tag.encode("utf-8")).decode("utf-8")
    else:
        cache_tag_suffix = ""

    return f"requirements-{requirements_hash}{cache_tag_suffix}.txt"


def get_cached_deps_details(
    dagster_cloud_url: str,
    dagster_cloud_api_token: str,
    requirements_hash: str,
    cache_tag: Optional[str],
) -> Optional[dict[str, Any]]:
    """Returns a metadata dict for the requirements_hash and cache_tag.

    The dict contains:
    'deps_pex_name': filename for the deps pex, eg 'deps-123234334.pex'
    'dagster_version': dagster package version included in the deps, eg '1.0.14'
    """
    urls = get_s3_urls_for_get(
        dagster_cloud_url,
        dagster_cloud_api_token,
        [requirements_hash_filename(requirements_hash, cache_tag)],
    )
    if not urls:
        return None

    url = urls[0]
    if not url:
        return None

    result = requests.get(url)
    if result.ok:
        data = json.loads(result.content)
        # Don't return partial information
        if "deps_pex_name" in data and "dagster_version" in data:
            return data

    if result.status_code == 404:
        ui.print("No dependencies in cache")
    else:
        ui.warn(f"Unable to read cached deps details {result}")
    return None


def set_cached_deps_details(
    dagster_cloud_url: str,
    dagster_cloud_api_token: str,
    requirements_hash: str,
    cache_tag: Optional[str],
    deps_pex_name: str,
    dagster_version: str,
):
    """Saves the deps_pex_name and dagster_version into the requirements hash file."""
    filename = requirements_hash_filename(requirements_hash, cache_tag)
    content = json.dumps({"deps_pex_name": deps_pex_name, "dagster_version": dagster_version})
    with TemporaryDirectory() as tmp_dir:
        filepath = os.path.join(tmp_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        upload_files(dagster_cloud_url, dagster_cloud_api_token, [filepath])


def upload_files(dagster_cloud_url: str, dagster_cloud_api_token: str, filepaths: list[str]):
    filenames = [os.path.basename(filepath) for filepath in filepaths]
    urls = get_s3_urls_for_put(dagster_cloud_url, dagster_cloud_api_token, filenames)
    if not urls:
        ui.error(f"Cannot upload files, did not get PUT urls for: {filenames}")
        return

    # we expect response list to be in the same order as the request
    for _, filepath, url in zip(filenames, filepaths, urls):
        if not url:
            ui.print(f"No upload URL received for {filepath} - skipping")
            continue

        ui.print(f"Uploading {filepath} ...")
        with open(filepath, "rb") as f:
            response = requests.put(url, data=f)
            if response.ok:
                ui.print(f"Upload successful: {filepath}")
            else:
                ui.error(f"Upload failed for {filepath}: {response}")
                ui.error(f"Upload URL: {url}")
                ui.error(f"{response.content}")
