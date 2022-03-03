from pathlib import Path
from typing import Dict

from setuptools import find_packages, setup  # type: ignore


def get_description() -> str:
    readme_path = Path(__file__).parent.parent.parent / "README.md"

    if not readme_path.exists():
        return """
        # Dagster

        The data orchestration platform built for productivity.
        """.strip()

    return readme_path.read_text()


def get_version() -> str:
    version: Dict[str, str] = {}
    with open("dagster/version.py") as fp:
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
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["dagster_tests"]),
        package_data={
            "dagster": [
                "dagster/core/storage/event_log/sqlite/alembic/*",
                "dagster/core/storage/runs/sqlite/alembic/*",
                "dagster/core/storage/schedules/sqlite/alembic/*",
                "dagster/generate/new_project/*",
                "dagster/grpc/protos/*",
            ]
        },
        include_package_data=True,
        install_requires=[
            # cli
            "click>=5.0",
            "coloredlogs>=6.1, <=14.0",
            "contextvars; python_version < '3.7'",
            # https://github.com/dagster-io/dagster/issues/4167
            "Jinja2<3.0",
            "markupsafe<=2.0.1",
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
            "pep562",
            "protobuf>=3.13.0",  # ensure version we require is >= that with which we generated the proto code (set in dev-requirements)
            "python-dateutil",
            "pytz",
            "requests",
            "rx>=1.6,<2",  # https://github.com/dagster-io/dagster/issues/4089
            "tabulate",
            "tqdm",
            "typing_compat",
            "sqlalchemy>=1.0",
            "toposort>=1.0",
            "watchdog>=0.8.3",
            'psutil >= 1.0; platform_system=="Windows"',
            # https://github.com/mhammond/pywin32/issues/1439
            'pywin32 != 226; platform_system=="Windows"',
            "docstring-parser",
        ],
        extras_require={
            "docker": ["docker"],
            "test": [
                "astroid>=2.3.3,<2.5",
                "coverage==5.3",
                "docker",
                "freezegun>=0.3.15",
                "grpcio-tools==1.32.0",
                "mock==3.0.5",
                "objgraph",
                "protobuf==3.13.0",  # without this, pip will install the most up-to-date protobuf
                "pytest-cov==2.10.1",
                "pytest-dependency==0.5.1",
                "pytest-mock==3.3.1",
                "pytest-rerunfailures==10.0",
                "pytest-runner==5.2",
                "pytest-xdist==2.1.0",
                "pytest==6.1.1",
                "responses==0.10.*",
                "snapshottest==0.6.0",
                "tox==3.14.2",
                "tox-pip-version==0.0.7",
                "tqdm==4.48.0",  # pylint crash 48.1+
                "yamllint",
                "flake8>=3.7.8",
                "pylint==2.6.0",
            ],
            "black": [
                "black[jupyter]==22.1.0",
            ],
            "isort": [
                "isort==5.10.1",
            ],
            "mypy": [
                "mypy==0.931",
                "types-croniter",  # version will be resolved against croniter
                "types-mock",  # version will be resolved against mock
                "types-pkg-resources",  # version will be resolved against setuptools (contains pkg_resources)
                "types-python-dateutil",  # version will be resolved against python-dateutil
                "types-PyYAML",  # version will be resolved against PyYAML
                "types-pytz",  # version will be resolved against pytz
                "types-requests",  # version will be resolved against requests
                "types-tabulate",  # version will be resolved against tabulate
            ],
        },
        entry_points={
            "console_scripts": [
                "dagster = dagster.cli:main",
                "dagster-daemon = dagster.daemon.cli:main",
            ]
        },
    )
