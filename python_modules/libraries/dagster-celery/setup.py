from typing import Dict

from setuptools import find_packages, setup  # type: ignore


def get_version() -> str:
    version: Dict[str, str] = {}
    with open("dagster_celery/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    setup(
        name="dagster-celery",
        version=get_version(),
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="Package for using Celery as Dagster's execution engine.",
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-celery",
        classifiers=[
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["test"]),
        entry_points={"console_scripts": ["dagster-celery = dagster_celery.cli:main"]},
        install_requires=["dagster", "dagster_graphql", "celery>=4.3.0", "click>=5.0",],
        extras_require={
            "flower": ["flower"],
            "redis": ["redis"],
            "kubernetes": ["kubernetes"],
            "test": ["docker"],
        },
        zip_safe=False,
    )
