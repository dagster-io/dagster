from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open("dagster_wandb/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    setup(
        name="dagster-wandb",
        version=get_version(),
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="Package for wandb Dagster components.",
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-wandb",
        classifiers=[
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["dagster_wandb_tests*"]),
        install_requires=[
            "dagster",
            "wandb>=0.13.5",
        ],
        extras_require={"dev": ["cloudpickle", "joblib", "callee"]},
        zip_safe=False,
    )
