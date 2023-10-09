from pathlib import Path
from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_databricks/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-databricks",
    version=ver,
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Package for Databricks-specific Dagster framework op and resource components.",
    url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-databricks",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_databricks_tests*"]),
    include_package_data=True,
    install_requires=[
        "dagster==1.5.2",
        "dagster-pipes==1.5.2",
        "dagster-pyspark==0.21.2",
        "databricks-cli~=0.17",  # TODO: Remove this dependency in the next minor release.
        "databricks_api",  # TODO: Remove this dependency in the next minor release.
        "databricks-sdk<0.9",  # Breaking changes occur in minor versions.
    ],
    zip_safe=False,
)
