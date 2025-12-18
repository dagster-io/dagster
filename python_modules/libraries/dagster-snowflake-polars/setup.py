from pathlib import Path

from setuptools import find_packages, setup


def get_version() -> str:
    version: dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_snowflake_polars/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-snowflake-polars",
    version=ver,
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Package for integrating Snowflake and Polars with Dagster.",
    url=(
        "https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/"
        "dagster-snowflake-polars"
    ),
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_snowflake_polars_tests*"]),
    include_package_data=True,
    python_requires=">=3.10,<3.15",
    install_requires=[
        "dagster==1.12.7",
        "dagster-snowflake==0.28.7",
        "polars>=1.0.0",
        "requests",
        "adbc-driver-snowflake>=1.6.0",
    ],
    extras_require={
        "test": [
            # https://status.snowflake.com/incidents/txclg2cyzq32
            "certifi==2025.1.31",
            "snowflake-connector-python[pandas]>=3.4.0",
        ]
    },
    zip_safe=False,
)
