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
    install_requires=[
        "dagster==1.10.9",
        "typer",
    ],
    zip_safe=False,
    entry_points={
        "dagster_dg.library": [
            "dagster-components-dagster = dagster_components.dagster",
            "dagster-components-dbt = dagster_components.dagster_dbt",
            "dagster-components-sling = dagster_components.dagster_sling",
        ],
    },
)
