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
        exec(fp.read(), version)

    return version["__version__"]


# grpcio 1.44.0 is the min version compatible with both protobuf 3 and 4
GRPC_VERSION_FLOOR = "1.44.0"

ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"

setup(
    name="dagster",
    version=get_version(),
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description=(
        "Dagster is an orchestration platform for the development, production, and observation of"
        " data assets."
    ),
    long_description=get_description(),
    long_description_content_type="text/markdown",
    project_urls={
        "Homepage": "https://dagster.io",
        "GitHub": "https://github.com/dagster-io/dagster",
        "Documentation": "https://docs.dagster.io",
        "Changelog": "https://github.com/dagster-io/dagster/releases",
        "Issue Tracker": "https://github.com/dagster-io/dagster/issues",
        "Twitter": "https://twitter.com/dagster",
        "YouTube": "https://www.youtube.com/@dagsterio",
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
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: System :: Monitoring",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_tests*"]),
    include_package_data=True,
    python_requires=">=3.8,<3.13",
    install_requires=[
        # cli
        "click>=5.0",
        "coloredlogs>=6.1,<=14.0",
        "Jinja2",
        "PyYAML>=5.1",
        # core (not explicitly expressed atm)
        # pin around issues in specific versions of alembic that broke our migrations
        "alembic>=1.2.1,!=1.6.3,!=1.7.0,!=1.11.0",
        "croniter>=0.3.34",
        f"grpcio>={GRPC_VERSION_FLOOR}",
        f"grpcio-health-checking>={GRPC_VERSION_FLOOR}",
        "packaging>=20.9",
        "pendulum>=3,<4; python_version>='3.12'",
        "pendulum>=0.7.0,<4; python_version>='3.9' and python_version<'3.12'",
        "pendulum>=0.7.0,<3; python_version<'3.9'",  # https://github.com/dagster-io/dagster/issues/19500
        "protobuf>=3.20.0,<5; python_version<'3.11'",  # min protobuf version to be compatible with both protobuf 3 and 4
        "protobuf>=4,<5; python_version>='3.11'",
        "python-dateutil",
        "python-dotenv",
        "pytz",
        "requests",
        "setuptools",
        "tabulate",
        "tomli<3",
        "tqdm<5",
        "typing_extensions>=4.4.0,<5",
        "structlog",
        "sqlalchemy>=1.0,<3",
        "toposort>=1.0",
        "watchdog>=0.8.3",
        'psutil>=1.0; platform_system=="Windows"',
        # https://github.com/mhammond/pywin32/issues/1439
        'pywin32!=226; platform_system=="Windows"',
        "docstring-parser",
        "universal_pathlib; python_version<'3.12'",
        "universal_pathlib>=0.2.0; python_version>='3.12'",
        # https://github.com/pydantic/pydantic/issues/5821
        "pydantic>1.10.0,!= 1.10.7,<3",
        "rich",
        "dagster-pipes==1.6.13",
    ],
    extras_require={
        "docker": ["docker"],
        "test": [
            "buildkite-test-collector ; python_version>='3.8'",
            "docker",
            f"grpcio-tools>={GRPC_VERSION_FLOOR}",
            "mock==3.0.5",
            "mypy-protobuf",
            "objgraph",
            "pytest-cov==2.10.1",
            "pytest-dependency==0.5.1",
            "pytest-mock==3.3.1",
            "pytest-rerunfailures==10.0",
            "pytest-runner==5.2",
            "pytest-xdist==3.3.1",
            "pytest>=7.0.1",
            "responses<=0.23.1",  # https://github.com/getsentry/responses/issues/654
            "syrupy>=4.0.0",
            "tox==3.25.0",
            "morefs[asynclocal]; python_version>='3.8'",
            "rapidfuzz",
        ],
        "mypy": ["mypy==1.8.0"],
        "pyright": [
            "pyright==1.1.349",
            ### Stub packages
            "pandas-stubs",  # version will be resolved against pandas
            "types-backports",  # version will be resolved against backports
            "types-certifi",  # version will be resolved against certifi
            "types-chardet",  # chardet is a 2+-order dependency of some Dagster libs
            "types-croniter",  # version will be resolved against croniter
            "types-cryptography",  # version will be resolved against cryptography
            "types-mock",  # version will be resolved against mock
            "types-paramiko",  # version will be resolved against paramiko
            "types-pkg-resources",  # version will be resolved against setuptools (contains pkg_resources)
            "types-pyOpenSSL",  # version will be resolved against pyOpenSSL
            "types-python-dateutil",  # version will be resolved against python-dateutil
            "types-PyYAML",  # version will be resolved against PyYAML
            "types-pytz",  # version will be resolved against pytz
            "types-requests",  # version will be resolved against requests
            "types-simplejson",  # version will be resolved against simplejson
            "types-six",  # needed but not specified by grpcio
            "types-sqlalchemy==1.4.53.34",  # later versions introduce odd errors
            "types-tabulate",  # version will be resolved against tabulate
            "types-tzlocal",  # version will be resolved against tzlocal
            "types-toml",  # version will be resolved against toml
        ],
        "ruff": [
            "ruff==0.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "dagster = dagster.cli:main",
            "dagster-daemon = dagster.daemon.cli:main",
        ]
    },
)
