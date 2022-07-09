from setuptools import find_packages, setup

setup(
    name="modern_data_stack_assets",
    version="0+dev",
    author="Elementl",
    author_email="hello@elementl.com",
    classifiers=[
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["test"]),
    package_data={"modern_data_stack_assets": ["mds_dbt/*"]},
    install_requires=[
        "dagster",
        "dagit",
        "dagster-airbyte",
        "dagster-dbt",
        "dagster-postgres",
        "pandas",
        "numpy",
        "scipy",
        "dbt-core",
        "dbt-postgres",
    ],
    extras_require={"tests": ["mypy", "pylint", "pytest"]},
    python_requires=">=3.6,<=3.10",
)
