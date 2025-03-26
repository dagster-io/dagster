import warnings
from collections.abc import Mapping

import packaging.version

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


def parse_package_version(version_str: str) -> packaging.version.Version:
    parsed_version = packaging.version.parse(version_str)
    assert isinstance(parsed_version, packaging.version.Version)
    return parsed_version


def check_dagster_package_version(library_name: str, library_version: str) -> None:
    # This import must be internal in order for this function to be testable
    from dagster_shared.version import __version__

    parsed_lib_version = parse_package_version(library_version)
    if parsed_lib_version.release[0] < 1:
        if library_version != __version__:
            message = (
                f"Found version mismatch between `dagster-shared` ({__version__}) "
                f"and `{library_name}` ({library_version})"
            )
            warnings.warn(message)
    else:
        expected_version = core_version_from_library_version(__version__)
        if library_version != expected_version:
            message = (
                f"Found version mismatch between `dagster-shared` ({__version__}) "
                f"expected library version ({expected_version}) "
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
    if release[0] < 1:
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
