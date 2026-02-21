from pathlib import Path

from setuptools import find_packages, setup


def get_version() -> str:
    version: dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_soda/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)
    return version["__version__"]


ver = get_version()
pin = "" if ver == "1!0+dev" else f"=={ver}"

setup(
    name="dagster-soda",
    version=ver,
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Package for running Soda Core data quality scans in Dagster.",
    url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-soda",
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_soda_tests*"]),
    include_package_data=True,
    python_requires=">=3.10,<3.15",
    install_requires=[
        f"dagster{pin}",
        "soda-core>=3.0,<4",
        "pyyaml",
    ],
    zip_safe=False,
    extras_require={
        "test": [
            "dagster-dg-cli",
        ],
    },
    entry_points={
        "dagster_dg_cli.registry_modules": [
            "dagster_soda = dagster_soda",
        ],
    },
)
