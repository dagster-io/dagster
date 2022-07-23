import os
from enum import Enum
from typing import List

from dagster_buildkite.utils import is_release_branch, safe_getenv


class AvailablePythonVersion(str, Enum):

    # Ordering is important here, because some steps will take the highest/lowest available version.
    V3_6 = "3.6.15"
    V3_7 = "3.7.13"
    V3_8 = "3.8.13"
    V3_9 = "3.9.13"
    V3_10 = "3.10.5"

    @classmethod
    def get_all(cls) -> List["AvailablePythonVersion"]:
        return list(cls)

    @classmethod
    def get_default(cls) -> "AvailablePythonVersion":
        return cls["V3_9"]

    @classmethod
    def get_pytest_defaults(cls) -> List["AvailablePythonVersion"]:

        branch_name = safe_getenv("BUILDKITE_BRANCH")
        commit_message = safe_getenv("BUILDKITE_MESSAGE")
        if branch_name == "master" or is_release_branch(branch_name):
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
        ver_parts = version.split(".")
        major, minor = ver_parts[0], ver_parts[1]
        return f"py{major}{minor}"
