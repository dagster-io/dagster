from setuptools import find_packages, setup

setup(
    name="project_atproto_dashboard",
    packages=find_packages(exclude=["project_atproto_dashboard_tests"]),
    install_requires=["dagster", "dagster-cloud", "dagster-aws", "atproto", "dagster-duckdb"],
    extras_require={"dev": ["dagster-webserver", "pytest", "ruff"]},
)
