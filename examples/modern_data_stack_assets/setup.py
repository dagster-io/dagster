from setuptools import find_packages, setup

setup(
    name="modern_data_stack_assets",
    version="dev",
    author="Elementl",
    author_email="hello@elementl.com",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["test"]),
    package_data={"modern_data_stack_assets": ["mds_dbt/*"]},
    install_requires=[
        "dagster",
        "dagster-airbyte",
        "dagster-dbt",
        "dbt-core",
        "dbt-postgres",
    ],
    extras_require={"tests": ["mypy", "pylint", "pytest"]},
)
