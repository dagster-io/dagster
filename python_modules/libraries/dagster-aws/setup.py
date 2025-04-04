from pathlib import Path

from setuptools import find_packages, setup


def get_version() -> str:
    version: dict[str, str] = {}
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
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_aws_tests*"]),
    include_package_data=True,
    python_requires=">=3.9,<3.13",
    install_requires=[
        "boto3",
        "dagster==1.10.9",
        "packaging",
        "requests",
    ],
    extras_require={
        "redshift": ["psycopg2-binary"],
        "pyspark": ["dagster-pyspark"],
        "stubs": [
            "boto3-stubs-lite[s3,logs,ecs,glue,emr-serverless,emr,emr-containers]",
        ],
        "test": [
            "botocore!=1.32.1",
            "moto[s3,server,glue,emrserverless,logs,emrcontainers]>=2.2.8,<5.0",
            "requests-mock",
            "xmltodict==0.12.0",  # pinned until moto>=3.1.9 (https://github.com/spulec/moto/issues/5112)
            "flaky",
            "pytest-cases",
        ],
    },
    zip_safe=False,
)
