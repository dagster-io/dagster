import os

import packaging.version
import requests

GIT_REPO_ROOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."
)


def _get_latest_dagster_release() -> str:
    res = requests.get("https://pypi.org/pypi/dagster/json")
    module_json = res.json()
    releases = module_json["releases"]
    release_versions = [
        packaging.version.parse(version)
        for version, files in releases.items()
        if not any(file.get("yanked") for file in files)
    ]
    for release_version in reversed(sorted(release_versions)):
        if not release_version.is_prerelease:
            return str(release_version)
    assert False, "No releases found"


LATEST_DAGSTER_RELEASE = _get_latest_dagster_release()

# https://github.com/dagster-io/dagster/issues/1662
DO_COVERAGE = True

GCP_CREDS_FILENAME = "gcp-key-elementl-dev.json"

# GCP tests need appropriate credentials
GCP_CREDS_LOCAL_FILE = f"/tmp/{GCP_CREDS_FILENAME}"
