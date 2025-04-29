import os
from enum import Enum
from typing import List

from dagster_buildkite.utils import is_release_branch, safe_getenv


class AvailablePythonVersion(Enum):
    # Ordering is important here, because some steps will take the highest/lowest available version.
    V3_9 = "3.9"
    V3_10 = "3.10"
    V3_11 = "3.11"
    V3_12 = "3.12"

    @classmethod
    def get_all(cls) -> List["AvailablePythonVersion"]:
        return list(cls)

    @classmethod
    def get_default(cls) -> "AvailablePythonVersion":
        return cls["V3_12"]

    # Useful for providing to `PackageSpec.unsupported_python_versions` when you only want to test
    # the default version.
    @classmethod
    def get_all_except_default(cls) -> List["AvailablePythonVersion"]:
        return [v for v in cls.get_all() if v != cls.get_default()]

    @classmethod
    def get_pytest_defaults(cls) -> List["AvailablePythonVersion"]:
        branch_name = safe_getenv("BUILDKITE_BRANCH")
        commit_message = safe_getenv("BUILDKITE_MESSAGE")
        if is_release_branch(branch_name):
            return cls.get_all()
        else:
            # environment variable-specified defaults
            # branch name or commit message-specified defaults
            test_pythons = os.environ.get("TEST_PYTHON_VERSIONS", "")

            env_vars = [branch_name, commit_message, test_pythons]

            specified_versions: List[AvailablePythonVersion] = []
            for version in cls.get_all():
                marker = f"test-{cls.to_tox_factor(version)}"
                if any(marker in v for v in env_vars):
                    specified_versions.append(version)
            if any("test-all" in v for v in env_vars):
                specified_versions += cls.get_all()

            return (
                list(set(specified_versions))
                if len(specified_versions) > 0
                else [cls.get_default()]
            )

    @classmethod
    def from_major_minor(cls, major: int, minor: int) -> "AvailablePythonVersion":
        key = f"V{major}_{minor}"
        return cls[key]

    @classmethod
    def to_tox_factor(cls, version: "AvailablePythonVersion") -> str:
        ver_parts = version.value.split(".")
        major, minor = ver_parts[0], ver_parts[1]
        return f"py{major}{minor}"
