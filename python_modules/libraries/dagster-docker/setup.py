from setuptools import find_packages, setup


def get_version():
    version = {}
    with open("dagster_docker/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    setup(
        name="dagster-docker",
        version=get_version(),
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="A Dagster integration for docker",
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-docker",
        classifiers=[
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["test"]),
        install_requires=["dagster", "docker"],
        tests_require=[],
        zip_safe=False,
    )
