from setuptools import find_packages, setup

setup(
    name="project_atproto_dashboard",
    packages=find_packages(exclude=["project_atproto_dashboard_tests"]),
    install_requires=["dagster", "dagster-aws", "atproto", "tenacity"],
    extras_require={"dev": ["dagster-webserver", "pytest", "ruff"]},
)
