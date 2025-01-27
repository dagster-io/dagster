from pathlib import Path

from setuptools import find_packages, setup


def get_version() -> str:
    version: dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_components/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep renderer issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-components",
    version=get_version(),
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="",  # TODO - fill out description
    url=(
        "https://github.com/dagster-io/dagster/tree/master/examples/experimental/dagster-components/"
        "dagster-components"
    ),
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_components_tests*", "examples*"]),
    install_requires=["dagster>=1.9.5", "tomli", "typer"],
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "dagster-components = dagster_components.cli:main",
        ],
        "dagster.components": [
            "dagster_components = dagster_components.lib",
            "dagster_components.test = dagster_components.lib.test",
        ],
    },
    extras_require={
        "sling": ["dagster-sling"],
        "dbt": ["dagster-dbt"],
        "test": ["dbt-duckdb"],
    },
)
