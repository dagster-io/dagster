from setuptools import find_packages, setup

setup(
    name="use_case_repository",
    packages=find_packages(exclude=["use_case_repository_tests"]),
    install_requires=[
        "dagster",
        "dagster-aws",
        "dagster-sling",
        "dagster-pipes",
        "dagster-snowflake",
        "flask",
        "markdown",
        "polars",
        "pymdown-extensions",
        "python-frontmatter",
        "sling",
    ],
    extras_require={
        "dev": [
            "dagster-webserver",
            "pytest",
            "ruff",
        ]
    },
)
