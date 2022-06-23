from setuptools import find_packages, setup

setup(
    name="dbt_python_assets",
    version="0+dev",
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
    package_data={"dbt_python_assets": ["dbt_project/*"]},
    install_requires=[
        "dagster",
        "dagit",
        "dagster-dbt",
        "pandas",
        "numpy",
        "scipy",
        "dbt-core",
        "dbt-duckdb",
    ],
    extras_require={"tests": ["mypy", "pylint", "pytest"]},
)
