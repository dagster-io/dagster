from pathlib import Path
from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_buildkite/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
setup(
    name="dagster-buildkite",
    version=get_version(),
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Tools for buildkite automation",
    url="https://github.com/dagster-io/dagster/tree/master/.buildkite/dagster-buildkite",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["test"]),
    install_requires=[
        "PyYAML",
        "packaging>=20.9",
        "requests",
        "typing_extensions>=4.2",
        "pathspec",
        # Need this until we have OpenSSL 1.1.1+ available in BK base image
        # Context: https://github.com/psf/requests/issues/6432
        "urllib3<2",
    ],
    entry_points={
        "console_scripts": [
            "dagster-buildkite = dagster_buildkite.cli:dagster",
            "dagster-buildkite-nightly = dagster_buildkite.cli:dagster_nightly",
        ]
    },
)
