import json
import socket
import warnings
from collections.abc import Mapping
from typing import Any

from packaging.version import Version

from dagster_shared import check
from dagster_shared.version import __version__


class DagsterLibraryRegistry:
    _libraries: dict[str, str] = {"dagster-shared": __version__}

    @classmethod
    def register(cls, name: str, version: str, *, is_dagster_package: bool = True):
        if is_dagster_package:
            check_dagster_package_version(name, version)

        cls._libraries[name] = version

    @classmethod
    def get(cls) -> Mapping[str, str]:
        return cls._libraries.copy()


def parse_package_version(version_str: str) -> Version:
    parsed_version = Version(version_str)
    assert isinstance(parsed_version, Version)
    return parsed_version


def increment_micro_version(v: Version, interval: int) -> Version:
    major, minor, micro = v.major, v.minor, v.micro
    new_micro = micro + interval
    if new_micro < 0:
        raise ValueError(f"Micro version cannot be negative: {new_micro}")
    return Version(f"{major}.{minor}.{new_micro}")


def check_dagster_package_version(library_name: str, library_version: str) -> None:
    # This import must be internal in order for this function to be testable
    from dagster_shared.version import __version__

    parsed_lib_version = parse_package_version(library_version)
    if parsed_lib_version.release[0] >= 1:
        if library_version != __version__:
            message = (
                f"Found version mismatch between `dagster-shared` ({__version__})"
                f"and `{library_name}` ({library_version})"
            )
            warnings.warn(message)
    else:
        target_version = library_version_from_core_version(__version__)
        if library_version != target_version:
            message = (
                f"Found version mismatch between `dagster-shared` ({__version__}) "
                f"expected library version ({target_version}) "
                f"and `{library_name}` ({library_version})."
            )
            warnings.warn(message)


# Use this to get the "library version" (pre-1.0 version) from the "core version" (post 1.0
# version). 16 is from the 0.16.0 that library versions stayed on when core went to 1.0.0.
def library_version_from_core_version(core_version: str) -> str:
    parsed_version = parse_package_version(core_version)

    release = parsed_version.release
    if release[0] >= 1:
        library_version = ".".join(["0", str(16 + release[1]), str(release[2])])

        if parsed_version.is_prerelease:
            library_version = library_version + "".join(
                [str(pre) for pre in check.not_none(parsed_version.pre)]
            )

        if parsed_version.is_postrelease:
            library_version = library_version + "post" + str(parsed_version.post)

        return library_version
    else:
        return core_version


def core_version_from_library_version(library_version: str) -> str:
    parsed_version = parse_package_version(library_version)

    release = parsed_version.release
    if release[0] < 1 and len(release) > 1:
        core_version = ".".join(["1", str(release[1] - 16), str(release[2])])

        if parsed_version.is_prerelease:
            core_version = core_version + "".join(
                [str(pre) for pre in check.not_none(parsed_version.pre)]
            )

        if parsed_version.is_postrelease:
            core_version = core_version + "post" + str(parsed_version.post)

        return core_version
    else:
        return library_version


class DagsterPyPiAccessError(Exception):
    pass


def get_pypi_package_data(pkg_name: str, timeout: float = 5.0) -> dict[str, Any]:
    # defer for import performance
    import urllib.request
    from urllib.error import HTTPError, URLError

    url = f"https://pypi.org/pypi/{pkg_name}/json"

    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            if response.status != 200:
                raise DagsterPyPiAccessError(
                    f"Error: Received status code {response.status} for {pkg_name}"
                )
            return json.load(response)
    except (HTTPError, URLError, socket.timeout) as e:
        raise DagsterPyPiAccessError(f"Network error while checking {pkg_name}: {e}")
    except json.JSONDecodeError as e:
        raise DagsterPyPiAccessError(f"Invalid JSON response for {pkg_name}: {e}")


def get_published_pypi_versions(pkg_name: str, timeout: float = 5.0) -> list[Version]:
    package_data = get_pypi_package_data(pkg_name, timeout)
    return sorted(Version(k) for k in package_data["releases"].keys())
