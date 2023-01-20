from pathlib import Path
from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_dask/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-dask",
    version=ver,
    author="Elementl",
    author_email="hello@elementl.com",
    license="Apache-2.0",
    description="Package for using Dask as Dagster's execution engine.",
    url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-dask",
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_dask_tests*"]),
    install_requires=[
        "bokeh",
        "dagster==1.1.13",
        "dask[dataframe]>=1.2.2",
        "distributed>=1.28.1",
    ],
    extras_require={
        "yarn": ["dask-yarn"],
        "pbs": ["dask-jobqueue"],
        "kube": ["dask-kubernetes<=2022.9.0"],
        # we need `pyarrow` for testing read/write parquet files.
        "test": ["pyarrow"],
    },
    zip_safe=False,
)
