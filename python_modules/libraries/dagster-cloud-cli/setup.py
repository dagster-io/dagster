from pathlib import Path

from setuptools import find_packages, setup


def get_version() -> str:
    version: dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_cloud_cli/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-cloud-cli",
    version=get_version(),
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="",  # TODO - fill out description
    url=(
        "https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-cloud-cli"
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
    packages=find_packages(exclude=["dagster_cloud_cli_tests*"]),
    install_requires=[
        "dagster-shared",
        "packaging>=20.9",
        "questionary",
        "requests",
        "typer>=0.4.1",
        "click",
        "PyYAML>=5.1",
        "github3.py",
        "Jinja2",
        "setuptools",
        'tomli>=1.1.0;python_version<"3.11"',
        "validators",
    ],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "dagster-cloud = dagster_cloud_cli.entrypoint:app",
            "dagster-plus = dagster_cloud_cli.entrypoint:app",
        ]
    },
    extras_require={
        "test": [
            "freezegun",
            "pytest>=8",
            "pytest-mock==3.14.0",
            "flaky",
            "pex>=2.1.132,<2.60.0",
        ],
    },
)
