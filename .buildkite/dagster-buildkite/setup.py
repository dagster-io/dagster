from setuptools import find_packages, setup

setup(
    name="dagster-buildkite",
    version="0.0.1",
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
        "tomli",
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
            "dagster-buildkite-prerelease-package = dagster_buildkite.cli:prerelease_package",
        ]
    },
)
