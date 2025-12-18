from pathlib import Path

from setuptools import find_packages, setup


def get_version() -> str:
    version: dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_dg_cli/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-dg-cli",
    version=get_version(),
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="",  # TODO - fill out description
    url=(
        "https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-dg-cli"
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
    packages=find_packages(exclude=["dagster_dg_cli_tests*"]),
    include_package_data=True,
    install_requires=[
        "dagster-dg-core==1.12.7",
        "dagster==1.12.7",
        "dagster-cloud-cli==1.12.7",
        "typer",
    ],
    extras_require={
        "test": ["syrupy>=4.0.0"],
        "ai": [
            "anthropic; python_version>='3.10'",
            "claude-code-sdk>=0.0.19; python_version>='3.10'",
            "mcp; python_version>='3.10'",
        ],
    },
    entry_points={
        "console_scripts": [
            "dg = dagster_dg_cli.cli:main",
        ]
    },
    zip_safe=False,
)
