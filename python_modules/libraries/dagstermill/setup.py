from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open("dagstermill/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    setup(
        name="dagstermill",
        version=get_version(),
        description="run notebooks using the Dagster tools",
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        packages=find_packages(exclude=["dagstermill_tests"]),
        classifiers=[
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        install_requires=[
            "dagster",
            # ipykernel 5.4.0 and 5.4.1 broke papermill
            # see https://github.com/dagster-io/dagster/issues/3401,
            # https://github.com/nteract/papermill/issues/519,
            # https://github.com/ipython/ipykernel/issues/568
            "ipykernel>=4.9.0,!=5.4.0,!=5.4.1",
            "scrapbook>=0.5.0",
            "packaging>=20.5",
            "papermill>=1.0.0",
        ],
        extras_require={
            "test": [
                "matplotlib",
                "nbconvert",
                "scikit-learn>=0.19.0",
                "tqdm<=4.48",  # https://github.com/tqdm/tqdm/issues/1049
            ]
        },
        entry_points={"console_scripts": ["dagstermill = dagstermill.cli:main"]},
    )
