from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open("dagster_graphql/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    ver = get_version()
    # dont pin dev installs to avoid pip dep resolver issues
    pin = "" if ver == "0+dev" else f"=={ver}"
    setup(
        name="dagster-graphql",
        version=ver,
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="The GraphQL frontend to python dagster.",
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/dagster-graphql",
        classifiers=[
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["dagster_graphql_tests*"]),
        install_requires=[
            "dagster==1.0.13",
            "graphene>=2.1.3,<3",  # compatability with graphql-ws in dagit
            "graphql-core>=2.1,<3",  # compatability with graphql-ws in dagit
            "requests",
            "gql<3",  # compatibility with graphql-core pin above
        ],
        entry_points={"console_scripts": ["dagster-graphql = dagster_graphql.cli:main"]},
    )
