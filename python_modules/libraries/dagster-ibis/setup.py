from pathlib import Path

from setuptools import find_packages, setup


def get_version() -> str:
    version: dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_ibis/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-ibis",
    version=ver,
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Integration between Dagster and Ibis, providing an I/O manager for Ibis tables.",
    url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-ibis",
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_ibis_tests*"]),
    include_package_data=True,
    python_requires=">=3.9,<3.13",
    install_requires=[
        "ibis-framework>=3.0.0",
        f"dagster{pin}",
    ],
    extras_require={
        "test": [
            "ibis-framework[duckdb]",
            "pytest",
        ],
        "duckdb": [
            "ibis-framework[duckdb]",
        ],
    },
    zip_safe=False,
)
