from setuptools import find_packages, setup


def get_version():
    version = {}
    with open("dagstermill/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    setup(
        name="dagstermill",
        version=get_version(),
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        packages=find_packages(exclude=["dagstermill_tests"]),
        classifiers=[
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        install_requires=[
            "dagster",
            "ipykernel>=4.9.0",
            "nteract-scrapbook>=0.2.0",
            "papermill>=1.0.0,<2.0.0",
            "six",
        ],
        entry_points={"console_scripts": ["dagstermill = dagstermill.cli:main"]},
    )
