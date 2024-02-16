from setuptools import find_packages, setup

setup(
    name="automation",
    version="0.0.1",
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Tools for infrastructure automation",
    url="https://github.com/dagster-io/dagster/tree/master/python_modules/automation",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["automation_tests*"]),
    extras_require={
        "buildkite": [
            "dagster",  # Support buildkite conditional running of tests
        ]
    },
)
