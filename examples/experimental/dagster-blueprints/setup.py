from pathlib import Path

from setuptools import find_packages, setup


def get_version() -> str:
    version: dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_blueprints/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = "1.9.13.post1"
setup(
    name="dagster-blueprints",
    version=get_version(),
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="dagster-blueprints is no longer supported. Please consider using Dagster Components instead: https://docs.dagster.io/guides/preview/components/",
    url=(
        "https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/"
        "dagster-blueprints"
    ),
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_blueprints_tests*", "examples*"]),
    install_requires=[
        "dagster==1.9.13",
        "dagster-databricks==1.9.13",
    ],
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "dagster-blueprints = dagster_blueprints.cli:main",
        ]
    },
)
