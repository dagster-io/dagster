from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open("dagstermill/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    ver = get_version()
    # dont pin dev installs to avoid pip dep resolver issues
    pin = "" if ver == "0+dev" else f"=={ver}"
    setup(
        name="dagstermill",
        version=ver,
        description="run notebooks using the Dagster tools",
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        packages=find_packages(exclude=["dagstermill_tests*"]),
        classifiers=[
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        install_requires=[
            f"dagster{pin}",
            "ipykernel>=6.0.0",
            "packaging>=20.5",
            "papermill>=1.0.0",
            "scrapbook>=0.5.0",
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
