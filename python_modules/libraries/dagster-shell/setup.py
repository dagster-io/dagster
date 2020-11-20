from setuptools import find_packages, setup


def get_version():
    version = {}
    with open("dagster_shell/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    setup(
        name="dagster-shell",
        version=get_version(),
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="Package for Dagster shell solids.",
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-shell",
        classifiers=[
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["test"]),
        install_requires=["dagster"],
        zip_safe=False,
    )
