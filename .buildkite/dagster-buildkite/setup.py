from pathlib import Path

from setuptools import find_packages, setup

# Path to buildkite-shared package
_current_dir = Path(__file__).parent
_buildkite_shared_path = _current_dir.parent / "buildkite-shared"

setup(
    name="dagster-buildkite",
    version="0.0.1",
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Tools for buildkite automation",
    url="https://github.com/dagster-io/dagster/tree/master/.buildkite/dagster-buildkite",
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["test"]),
    install_requires=[
        f"buildkite-shared @ file://{_buildkite_shared_path.absolute()}",
        "PyYAML",
        "tomli",
        "packaging>=20.9",
        "requests",
        "typing_extensions>=4.2",
        "pathspec",
        # Need this until we have OpenSSL 1.1.1+ available in BK base image
        # Context: https://github.com/psf/requests/issues/6432
        "urllib3<2",
        "pytest",
    ],
    entry_points={
        "console_scripts": [
            "dagster-buildkite = dagster_buildkite.cli:dagster",
            "dagster-buildkite-nightly = dagster_buildkite.cli:dagster_nightly",
            "dagster-buildkite-prerelease-package = dagster_buildkite.cli:prerelease_package",
        ]
    },
)
