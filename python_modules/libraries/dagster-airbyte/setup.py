from pathlib import Path
from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_airbyte/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-airbyte",
    version=ver,
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Package for integrating Airbyte with Dagster.",
    url=(
        "https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-airbyte"
    ),
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_airbyte_tests*"]),
    install_requires=[
        "dagster==1.5.2",
        "requests",
    ],
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "dagster-airbyte = dagster_airbyte.cli:main",
        ]
    },
    extras_require={
        "test": [
            "requests-mock",
        ],
        "managed": [
            "dagster-managed-elements==0.21.2",
        ],
    },
)
