from pathlib import Path
from typing import Dict

from setuptools import find_packages, setup


def get_description() -> str:
    readme_path = Path(__file__).parent.parent.parent / "README.md"

    if not readme_path.exists():
        return """
        # Dagster

        The data orchestration platform built for productivity.
        """.strip()

    return readme_path.read_text(encoding="utf-8")


def get_version() -> str:
    version: Dict[str, str] = {}
    with open("dagster/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    setup(
        name="dagster",
        version=get_version(),
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="The data orchestration platform built for productivity.",
        long_description=get_description(),
        long_description_content_type="text/markdown",
        url="https://github.com/dagster-io/dagster",
        classifiers=[
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["dagster_tests*"]),
        package_data={
            "dagster": [
                "dagster/core/storage/event_log/sqlite/alembic/*",
                "dagster/core/storage/runs/sqlite/alembic/*",
                "dagster/core/storage/schedules/sqlite/alembic/*",
                "dagster/_generate/templates/*",
                "dagster/grpc/protos/*",
            ]
        },
        include_package_data=True,
        install_requires=[
            # cli
            "click>=5.0",
            "coloredlogs>=6.1, <=14.0",
            "contextvars; python_version < '3.7'",
            "Jinja2",
            "PyYAML>=5.1",
            # core (not explicitly expressed atm)
            # alembic 1.6.3 broke our migrations: https://github.com/sqlalchemy/alembic/issues/848
            # alembic 1.7.0 is a breaking change
            "alembic>=1.2.1,!=1.6.3,<1.7.0",
            "croniter>=0.3.34",
            "grpcio>=1.32.0",  # ensure version we require is >= that with which we generated the grpc code (set in dev-requirements)
            "grpcio-health-checking>=1.32.0,<1.44.0",
            "packaging>=20.9",
            "pendulum",
            "protobuf>=3.13.0,<4",  # ensure version we require is >= that with which we generated the proto code (set in dev-requirements)
            "python-dateutil",
            "pytz",
            "requests",
            "rx>=1.6,<2",  # https://github.com/dagster-io/dagster/issues/4089
            "setuptools",
            "tabulate",
            "tqdm",
            "typing_compat",
            "typing_extensions>=4.0.1",
            "sqlalchemy>=1.0",
            "toposort>=1.0",
            "watchdog>=0.8.3",
            'psutil >= 1.0; platform_system=="Windows"',
            # https://github.com/mhammond/pywin32/issues/1439
            'pywin32 != 226; platform_system=="Windows"',
            "docstring-parser",
        ],
        extras_require={
            "test": [
                "coverage==5.3",
                "docker",
                "freezegun>=0.3.15",
                "mock==3.0.5",
                "objgraph",
                "pytest==7.0.1",  # last version supporting python 3.6
                "pytest-cov==2.10.1",
                "pytest-dependency==0.5.1",
                "pytest-mock==3.3.1",
                "pytest-rerunfailures==10.0",
                "pytest-runner==5.2",
                "pytest-xdist==2.1.0",
                "responses==0.10.*",
                "snapshottest==0.6.0",
            ],
        },
        entry_points={
            "console_scripts": [
                "dagster = dagster.cli:main",
                "dagster-daemon = dagster.daemon.cli:main",
            ]
        },
    )
