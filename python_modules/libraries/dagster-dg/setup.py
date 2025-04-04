from pathlib import Path

from setuptools import find_packages, setup


def get_version() -> str:
    version: dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_dg/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-dg",
    version=get_version(),
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="",  # TODO - fill out description
    url=("https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-dg"),
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_dg_tests*"]),
    install_requires=[
        "Jinja2",
        "tomlkit",
        "click>=8",
        "typing_extensions>=4.4.0,<5",
        "gql[requests]",
        "markdown",
        "jsonschema",
        "PyYAML>=5.1",
        "rich",
        "watchdog",
        "yaspin",
        "python-dotenv",
        # We use some private APIs of typer so we hard-pin here. This shouldn't need to be
        # frequently updated since is designed to be used from an isolated environment.
        "typer==0.15.1",
        "dagster-shared==0.26.9",
    ],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "dg = dagster_dg.cli:main",
        ]
    },
    extras_require={
        "test": [
            "click",
            "dagster",
            "psutil",
            "pydantic",
            "pytest",
        ],
    },
)
