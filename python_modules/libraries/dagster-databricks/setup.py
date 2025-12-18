from pathlib import Path

from setuptools import find_packages, setup


def get_version() -> str:
    version: dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_databricks/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" or "rc" in ver else f"=={ver}"
setup(
    name="dagster-databricks",
    version=ver,
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Package for Databricks-specific Dagster framework op and resource components.",
    url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-databricks",
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_databricks_tests*"]),
    include_package_data=True,
    python_requires=">=3.10,<3.15",
    install_requires=[
        "dagster==1.12.7",
        "dagster-pipes==1.12.7",
        "dagster-pyspark==0.28.7",
        "databricks-sdk>=0.41,<0.61.0",  # dbt-databricks is pinned to this version
    ],
    zip_safe=False,
)
