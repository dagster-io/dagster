from setuptools import find_packages, setup


def get_version():
    version = {}
    with open("dagster_aws/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    setup(
        name="dagster-aws",
        version=get_version(),
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="Package for AWS-specific Dagster framework solid and resource components.",
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-aws",
        classifiers=[
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["test"]),
        include_package_data=True,
        install_requires=["boto3", "dagster", "packaging", "psycopg2-binary", "requests"],
        extras_require={"pyspark": ["dagster-pyspark"]},
        zip_safe=False,
    )
