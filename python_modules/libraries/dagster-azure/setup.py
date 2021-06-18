from typing import Dict

from setuptools import find_packages, setup  # type: ignore


def get_version() -> str:
    version: Dict[str, str] = {}
    with open("dagster_azure/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    ver = get_version()
    # dont pin dev installs to avoid pip dep resolver issues
    pin = "" if ver == "dev" else f"=={ver}"
    setup(
        name="dagster-azure",
        version=ver,
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="Package for Azure-specific Dagster framework solid and resource components.",
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-azure",
        classifiers=[
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["test"]),
        include_package_data=True,
        install_requires=[
            "azure-storage-blob~=12.3.0",
            "azure-storage-file-datalake~=12.0.1",
            f"dagster{pin}",
        ],
        entry_points={"console_scripts": ["dagster-azure = dagster_azure.cli.cli:main"]},
        zip_safe=False,
    )
