from setuptools import find_packages, setup


def get_version():
    version = {}
    with open("dagster_mssql/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    ver = get_version()
    # dont pin dev installs to avoid pip dep resolver issues
    pin = "" if ver == "dev" else f"=={ver}"
    setup(
        name="dagster-mssql",
        version=ver,
        license="Apache-2.0",
        description="A Dagster integration for MSSQL",
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-mssql",
        classifiers=[
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["test"]),
        package_data={
            "dagster-mssql": [
                "dagster_mssql/alembic/*",
            ]
        },
        include_package_data=True,
        install_requires=[f"dagster{pin}", "pyodbc"],
        zip_safe=False,
    )
