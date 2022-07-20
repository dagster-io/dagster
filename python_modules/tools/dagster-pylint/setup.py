from setuptools import find_packages, setup

setup(
    name="dagster-pylint",
    version="0+dev",
    packages=find_packages(exclude="dagster_pylint_tests*"),
    install_requires=[
        "astroid",  # let pylint determine the version
        "pylint>=2",
    ],
    extras_require={
        "test": ["dagster[test]"],
    },
)
