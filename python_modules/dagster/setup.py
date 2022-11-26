from pathlib import Path
from typing import Dict

from setuptools import find_packages, setup


def get_description() -> str:
    readme_path = Path(__file__).parent / "README.md"

    if not readme_path.exists():
        return """
        # Dagster

        The data orchestration platform built for productivity.
        """.strip()

    return readme_path.read_text(encoding="utf-8")


def get_version() -> str:
    version: Dict[str, str] = {}
    with open(Path(__file__).parent / "dagster/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


setup(
    name="dagster",
    version=get_version(),
    author="Elementl",
    author_email="hello@elementl.com",
    license="Apache-2.0",
    description="The data orchestration platform built for productivity.",
    long_description=get_description(),
    long_description_content_type="text/markdown",
    project_urls={
        "Homepage": "https://dagster.io",
        "GitHub": "https://github.com/dagster-io/dagster",
        "Changelog": "https://github.com/dagster-io/dagster/releases",
        "Issue Tracker": "https://github.com/dagster-io/dagster/issues",
        "Twitter": "https://twitter.com/dagster",
        "YouTube": "https://www.youtube.com/channel/UCfLnv9X8jyHTe6gJ4hVBo9Q",
        "Slack": "https://dagster.io/slack",
        "Blog": "https://dagster.io/blog",
        "Newsletter": "https://dagster.io/newsletter-signup",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: System :: Monitoring",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_tests*"]),
    include_package_data=True,
    install_requires=[
        # cli
        "click>=5.0",
        "coloredlogs>=6.1, <=14.0",
        "contextvars; python_version < '3.7'",
        "Jinja2",
        "PyYAML>=5.1",
        # core (not explicitly expressed atm)
        # pin around issues in specific versions of alembic that broke our migrations
        "alembic>=1.2.1,!=1.6.3,!=1.7.0",
        "croniter>=0.3.34",
        # grpcio 1.48.1 has hanging/crashing issues: https://github.com/grpc/grpc/issues/30843
        # ensure version we require is >= that with which we generated the grpc code (set in dev-requirements)
        "grpcio>=1.32.0,<1.48.1",
        "grpcio-health-checking>=1.32.0,<1.44.0",
        "packaging>=20.9",
        "pendulum",
        "protobuf>=3.13.0,<4",  # ensure version we require is >= that with which we generated the proto code (set in dev-requirements)
        "python-dateutil",
        "python-dotenv",
        "pytz",
        "requests",
        "setuptools",
        "tabulate",
        "tomli",
        "tqdm",
        "typing_extensions>=4.0.1",
        "sqlalchemy>=1.0",
        "toposort>=1.0",
        "watchdog>=0.8.3",
        'psutil >= 1.0; platform_system=="Windows"',
        # https://github.com/mhammond/pywin32/issues/1439
        'pywin32 != 226; platform_system=="Windows"',
        "docstring-parser",
        "universal_pathlib",
    ],
    extras_require={
        "docker": ["docker"],
        "test": [
            "buildkite-test-collector ; python_version>='3.8'",
            "coverage==5.3",
            "docker",
            "grpcio-tools>=1.32.0,<1.44.0",  # related to above grpcio pins
            "mock==3.0.5",
            "objgraph",
            "protobuf==3.13.0",  # without this, pip will install the most up-to-date protobuf
            "pytest-cov==2.10.1",
            "pytest-dependency==0.5.1",
            "pytest-mock==3.3.1",
            "pytest-rerunfailures==10.0",
            "pytest-runner==5.2",
            "pytest-xdist==2.1.0",
            "pytest==7.0.1",  # last version supporting python 3.6
            "responses==0.10.*",
            "snapshottest==0.6.0",
            "tox==3.25.0",
            "yamllint",
            "astroid",  # let pylint determine the version
            "pylint==2.13.7",
        ],
        "black": [
            "black[jupyter]==22.3.0",
        ],
        "isort": [
            "isort==5.10.1",
        ],
        "mypy": [
            "mypy==0.991",
            "types-backports",  # version will be resolved against backports
            "types-certifi",  # version will be resolved against certifi
            "types-chardet",  # chardet is a 2+-order dependency of some Dagster libs
            "types-croniter",  # version will be resolved against croniter
            "types-cryptography",  # version will be resolved against cryptography
            "types-mock",  # version will be resolved against mock
            "types-paramiko",  # version will be resolved against paramiko
            "types-pkg-resources",  # version will be resolved against setuptools (contains pkg_resources)
            "types-protobuf<=3.19.21",  # version will be resolved against protobuf (3.19.22 introduced breaking change)
            "types-pyOpenSSL",  # version will be resolved against pyOpenSSL
            "types-python-dateutil",  # version will be resolved against python-dateutil
            "types-PyYAML",  # version will be resolved against PyYAML
            "types-pytz",  # version will be resolved against pytz
            "types-requests",  # version will be resolved against requests
            "types-simplejson",  # version will be resolved against simplejson
            "types-six",  # needed but not specified by grpcio
            "types-tabulate",  # version will be resolved against tabulate
            "types-tzlocal",  # version will be resolved against tzlocal
            "types-toml",  # version will be resolved against toml
        ],
    },
    entry_points={
        "console_scripts": [
            "dagster = dagster.cli:main",
            "dagster-daemon = dagster.daemon.cli:main",
        ]
    },
)
