from pathlib import Path
from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_aws/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-aws",
    version=ver,
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Package for AWS-specific Dagster framework solid and resource components.",
    url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-aws",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_aws_tests*"]),
    include_package_data=True,
    install_requires=[
        "boto3",
        "dagster==1.5.2",
        "packaging",
        "requests",
    ],
    extras_require={
        "redshift": ["psycopg2-binary"],
        "pyspark": ["dagster-pyspark"],
        "test": [
            "botocore",
            "moto[s3,server]>=2.2.8",
            "requests-mock",
            "xmltodict==0.12.0",  # pinned until moto>=3.1.9 (https://github.com/spulec/moto/issues/5112)
        ],
    },
    zip_safe=False,
)
