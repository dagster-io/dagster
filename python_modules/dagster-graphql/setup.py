from typing import Dict

from setuptools import find_packages, setup  # type: ignore


def get_version() -> str:
    version: Dict[str, str] = {}
    with open("dagster_graphql/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    setup(
        name="dagster-graphql",
        version=get_version(),
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="The GraphQL frontend to python dagster.",
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/dagster-graphql",
        classifiers=[
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["test"]),
        install_requires=[
            "graphene>=2.1.3",
            "gevent-websocket>=0.10.1",
            "gevent",
            "requests",
        ],
        entry_points={"console_scripts": ["dagster-graphql = dagster_graphql.cli:main"]},
    )
