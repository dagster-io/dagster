from typing import Dict

from setuptools import find_packages, setup  # type: ignore


def get_version() -> str:
    version: Dict[str, str] = {}
    with open("dagster_dask/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    setup(
        name="dagster-dask",
        version=get_version(),
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="Package for using Dask as Dagster's execution engine.",
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-dask",
        classifiers=[
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["test"]),
        install_requires=[
            "bokeh",
            "dagster",
            "dask[dataframe]>=1.2.2",
            "distributed>=1.28.1",
            # resolve issue with aiohttp pin of chardet for aiohttp<=3.7.3, req'd by dask-kubernetes
            # https://github.com/dagster-io/dagster/issues/3539
            "chardet<4.0",
        ],
        extras_require={
            "yarn": ["dask-yarn"],
            "pbs": ["dask-jobqueue"],
            "kube": ["dask-kubernetes"],
            # we need `pyarrow` for testing read/write parquet files.
            "test": ["pyarrow; python_version < '3.9'"],
        },
        zip_safe=False,
    )
