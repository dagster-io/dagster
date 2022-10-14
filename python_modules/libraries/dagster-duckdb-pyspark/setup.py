from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open("dagster_duckdb_pyspark/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    ver = get_version()
    # dont pin dev installs to avoid pip dep resolver issues
    pin = "" if ver == "0+dev" else f"=={ver}"
    setup(
        name="dagster-duckdb-pyspark",
        version=ver,
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="Package for storing PySpark DataFrames in DuckDB.",
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-duckb-pyspark",
        classifiers=[
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["dagster_duckdb_pyspark_tests*"]),
        include_package_data=True,
        install_requires=[
            "dagster==1.0.13",
            "dagster-duckdb==0.16.13",
            # Pyspark 2.x is incompatible with Python 3.8+
            'pyspark>=3.0.0; python_version >= "3.8"',
            'pyspark>=2.0.2; python_version < "3.8"',
        ],
        zip_safe=False,
    )
