import packaging.version
import pytest
import requests
from dagster_k8s.version import __version__


def test_version():
    assert __version__


from dagster_k8s.kubernetes_version import KUBERNETES_VERSION_UPPER_BOUND


def parse_package_version(version_str: str) -> packaging.version.Version:
    parsed_version = packaging.version.parse(version_str)
    assert isinstance(
        parsed_version, packaging.version.Version
    ), f"Found LegacyVersion: {version_str}"
    return parsed_version


def _get_latest_published_k8s_version() -> packaging.version.Version:
    res = requests.get("https://pypi.org/pypi/kubernetes/json")
    module_json = res.json()
    releases = module_json["releases"]
    release_versions = [
        parse_package_version(version)
        for version, files in releases.items()
        if not any(file.get("yanked") for file in files)
    ]
    for release_version in reversed(sorted(release_versions)):
        if not release_version.is_prerelease:
            return release_version

    raise Exception("Could not find any latest published kubernetes version")


@pytest.mark.nightly
def test_latest_version_pin():
    latest_version = _get_latest_published_k8s_version()
    assert latest_version.major < packaging.version.parse(KUBERNETES_VERSION_UPPER_BOUND).major, (
        f"A new version {latest_version} of kubernetes has been released to pypi that exceeds our pin. "
        "Increase the pinned version in kubernetes_version.py and verify that it still passes tests "
        "and that our PatchedApiClient class is still compatible with the real Kubernetes ApiClient object."
    )
