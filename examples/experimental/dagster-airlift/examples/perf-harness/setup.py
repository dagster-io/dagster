from setuptools import find_packages, setup

setup(
    name="perf-harness",
    packages=find_packages(),
    install_requires=[
        "dagster",
        "dagster-webserver",
        "dagster-airlift[dbt,core,in-airflow]",
        "dbt-duckdb",
        "pandas",
    ],
    extras_require={"test": ["pytest"]},
    entry_points={
        "console_scripts": [
            "perf-harness=perf_harness.cli:main",
        ],
    },
)
