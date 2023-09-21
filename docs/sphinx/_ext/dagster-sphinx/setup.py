from setuptools import find_packages, setup

setup(
    name="dagster-sphinx",
    version="0.0.1",
    author="Elementl",
    author_email="hello@elementl.com",
    license="Apache-2.0",
    description="Dagster-specific sphinx extension.",
    url="https://github.com/dagster-io/dagster",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_sphinx_tests*"]),
    install_requires=[
        "sphinx",
        "sphinx_toolbox",
    ],
)
