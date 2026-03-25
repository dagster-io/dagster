import os

import packaging.version
import requests
from buildkite_shared.context import INTERNAL_OSS_PREFIX
from buildkite_shared.utils import discover_git_repo_root, get_image_version

GIT_REPO_ROOT = discover_git_repo_root()

# When running inside the internal repo, OSS code lives under dagster-oss/.
# In the standalone OSS repo, they're the same.
_oss_subdir = os.path.join(GIT_REPO_ROOT, INTERNAL_OSS_PREFIX)
OSS_ROOT = _oss_subdir if os.path.isdir(_oss_subdir) else GIT_REPO_ROOT


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

GCP_CREDS_FILENAME = "gcp-key-elementl-dev.json"

# GCP tests need appropriate credentials
GCP_CREDS_LOCAL_FILE = f"/tmp/{GCP_CREDS_FILENAME}"

BUILDKITE_BUILD_TEST_PROJECT_IMAGE_IMAGE_VERSION: str = get_image_version(
    "buildkite-build-test-project-image"
)
TEST_PROJECT_BASE_IMAGE_VERSION: str = get_image_version("test-project-base")
