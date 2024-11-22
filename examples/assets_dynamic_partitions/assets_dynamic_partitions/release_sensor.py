import json
import os
from typing import Tuple

import requests
from dagster import AssetSelection, RunRequest, SensorResult, SkipReason, sensor

from . import assets


def semver_tuple(release: str) -> tuple[int, ...]:
    return tuple(map(int, release.split(".")))


@sensor(asset_selection=AssetSelection.all())
def release_sensor(context):
    """Polls the Github API for new releases.

    When we find one, add it to the set of partitions and run the pipeline on it.
    """
    latest_tracked_release = context.cursor

    response = requests.get(
        "https://api.github.com/repos/dagster-io/dagster/releases",
        auth=(os.environ["GITHUB_USER_NAME"], os.environ["GITHUB_ACCESS_TOKEN"]),
    )
    if not response.ok:
        response.raise_for_status()

    response_content = json.loads(response.content)
    all_releases = [release_blob["tag_name"] for release_blob in response_content]

    if latest_tracked_release is None:
        new_releases = all_releases
    else:
        new_releases = [
            release
            for release in all_releases
            if semver_tuple(release) > semver_tuple(latest_tracked_release)
        ]

    if len(new_releases) > 0:
        partitions_to_add = sorted(new_releases, key=semver_tuple)
        context.log.info(f"Requesting to add partitions: {partitions_to_add}")

        # We only launch a run for the latest release, to avoid unexpected large numbers of runs the
        # first time the sensor turns on. This means that you might need to manually backfill earlier
        # releases.
        return SensorResult(
            run_requests=[RunRequest(partition_key=new_releases[-1])],
            cursor=new_releases[-1],
            dynamic_partitions_requests=[
                assets.releases_partitions_def.build_add_request(partitions_to_add)
            ],
        )
    else:
        return SkipReason("No new releases")
