from pathlib import Path
from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open(Path(__file__).parent / "version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-helm",
    version=get_version(),
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Tools for Dagster Helm schema",
    url="https://github.com/dagster-io/dagster/tree/master/helm/dagster/schema",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["schema_tests"]),
    install_requires=["click", "pydantic>=1.10.0,<2.0.0"],
    extras_require={
        "test": [
            # remove pin once minimum supported kubernetes version is 1.19
            "kubernetes<22.6.0",
            f"dagster{pin}",
            f"dagster-aws{pin}",
            f"dagster-azure{pin}",
            f"dagster-gcp{pin}",
            f"dagster-k8s{pin}",
        ]
    },
    entry_points={
        "console_scripts": [
            "dagster-helm = schema.cli:main",
        ]
    },
)
