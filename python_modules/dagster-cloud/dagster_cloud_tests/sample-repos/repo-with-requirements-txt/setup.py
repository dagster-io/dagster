from setuptools import find_packages, setup

setup(
    name="repo-1",
    packages=find_packages(exclude=["repo_1_tests"]),
    install_requires=["dagster", "dagster-cloud"],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
