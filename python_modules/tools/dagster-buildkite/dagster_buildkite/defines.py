import os

import packaging.version
import requests

_dir = os.path.dirname(__file__)
while not os.path.exists(os.path.join(_dir, ".git")) or os.path.dirname(_dir) == _dir:
    _dir = os.path.dirname(_dir)
GIT_REPO_ROOT = os.path.abspath(_dir)


def _get_latest_dagster_release() -> str:
    res = requests.get("https://pypi.org/pypi/dagster/json")
    module_json = res.json()
    releases = module_json["releases"]
    release_versions = [packaging.version.parse(release) for release in releases.keys()]
    for release_version in reversed(sorted(release_versions)):
        if not release_version.is_prerelease:
            return str(release_version)
    assert False, "No releases found"


LATEST_DAGSTER_RELEASE = _get_latest_dagster_release()

# https://github.com/dagster-io/dagster/issues/1662
DO_COVERAGE = True

# GCP tests need appropriate credentials
GCP_CREDS_LOCAL_FILE = "/tmp/gcp-key-elementl-dev.json"
