from setuptools import find_packages, setup


def get_version():
    version = {}
    with open("dagster_mysql/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    setup(
        name="dagster-mysql",
        version=get_version(),
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="A Dagster integration for MySQL",
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-mysql",
        classifiers=[
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["test"]),
        package_data={
            "dagster-mysql": [
                "dagster_mysql/alembic/*",
            ]
        },
        include_package_data=True,
        install_requires=["dagster", "mysql-connector-python"],
        zip_safe=False,
    )
