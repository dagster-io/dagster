from pathlib import Path

from setuptools import find_packages, setup


def get_version() -> str:
    version: dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_dg_core/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-dg-core",
    version=get_version(),
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="",  # TODO - fill out description
    url=(
        "https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-dg-core"
    ),
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_dg_core_tests*"]),
    install_requires=[
        "Jinja2",
        "tomlkit<0.13.3",  # bug in this version
        "click>=8,<9",
        "click-aliases",
        "typing_extensions>=4.4.0,<5",
        "gql[requests]",
        "markdown",
        "jsonschema",
        "PyYAML>=5.1",
        "rich",
        "watchdog",
        "yaspin",
        "setuptools",  # Needed to parse setup.cfg
        "packaging",
        "python-dotenv",
        "typer<0.17.0",
        "dagster-shared==1.12.7",
        "dagster-cloud-cli==1.12.7",
    ],
    include_package_data=True,
    zip_safe=False,
    entry_points={},
    extras_require={
        "test": [
            "click",
            "dagster==1.12.7",
            "freezegun",
            "psutil",
            "pydantic",
            "pytest",
            "dagster-graphql==1.12.7",
            f"create-dagster{pin}",
        ],
    },
)
