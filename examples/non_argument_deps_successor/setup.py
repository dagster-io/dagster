from setuptools import find_packages, setup

setup(
    name="non_argument_deps_successor",
    packages=find_packages(exclude=["non_argument_deps_successor_tests"]),
    install_requires=["dagster", "dagster-cloud"],
    extras_require={"dev": ["dagit", "pytest"]},
)
