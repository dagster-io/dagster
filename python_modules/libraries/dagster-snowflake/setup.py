from pathlib import Path
from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_snowflake/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-snowflake",
    version=ver,
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Package for Snowflake Dagster framework components.",
    url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-snowflake",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_snowflake_tests*"]),
    install_requires=["dagster==1.5.2", "snowflake-connector-python>=2.1.0"],
    extras_require={
        "snowflake.sqlalchemy": [
            "sqlalchemy!=1.4.42",  # workaround for https://github.com/snowflakedb/snowflake-sqlalchemy/issues/350
            "snowflake-sqlalchemy",
        ],
        "pandas": ["pandas", "snowflake-connector-python[pandas]>=2.1.0"],
    },
    zip_safe=False,
)
