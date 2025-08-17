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
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_dg_cli_tests*"]),
    include_package_data=True,
    install_requires=[
        f"dagster-dg-core{pin}",
        f"dagster{pin}",
        "anthropic; python_version>='3.10'",  # anthropic not available for 3.9
        "claude-code-sdk>=0.0.19; python_version>='3.10'",  # claude-code-sdk not available for 3.9
        "mcp; python_version>='3.10'",  # mcp not available for 3.9
        "typer",
    ],
    entry_points={
        "console_scripts": [
            "dg = dagster_dg_cli.cli:main",
        ]
    },
    zip_safe=False,
)
