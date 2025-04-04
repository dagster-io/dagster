from pathlib import Path

from setuptools import find_packages, setup


def get_version() -> tuple[str, str]:
    version: dict[str, str] = {}
    dbt_core_version: dict[str, str] = {}

    with open(Path(__file__).parent / "dagster_dbt/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    with open(Path(__file__).parent / "dagster_dbt/dbt_core_version.py", encoding="utf8") as fp:
        exec(fp.read(), dbt_core_version)

    return version["__version__"], dbt_core_version["DBT_CORE_VERSION_UPPER_BOUND"]


dagster_dbt_version, DBT_CORE_VERSION_UPPER_BOUND = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if dagster_dbt_version == "1!0+dev" else f"=={dagster_dbt_version}"
setup(
    name="dagster-dbt",
    version=dagster_dbt_version,
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="A Dagster integration for dbt",
    url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-dbt",
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_dbt_tests*"]),
    include_package_data=True,
    python_requires=">=3.9,<3.13",
    install_requires=[
        "dagster==1.10.9",
        # Follow the version support constraints for dbt Core: https://docs.getdbt.com/docs/dbt-versions/core
        f"dbt-core>=1.7,<{DBT_CORE_VERSION_UPPER_BOUND}",
        "Jinja2",
        "networkx",
        "orjson",
        "requests",
        "rich",
        "sqlglot[rs]",
        "typer>=0.9.0",
        "packaging",
    ],
    extras_require={
        "test": [
            "pytest-rerunfailures",
            "pytest-order",
            "dbt-duckdb<1.9.2",  # concurrency issues
            "dagster-duckdb",
            "dagster-duckdb-pandas",
        ]
    },
    entry_points={
        "console_scripts": [
            "dagster-dbt-cloud = dagster_dbt.cloud.cli:app",
            "dagster-dbt = dagster_dbt.cli.app:app",
        ],
        "dagster_dg.library": [
            "dagster_dbt = dagster_dbt",
        ],
    },
    zip_safe=False,
)
