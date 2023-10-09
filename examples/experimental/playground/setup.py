from setuptools import find_packages, setup

setup(
    name="playground",
    packages=find_packages(exclude=["playground"]),
    install_requires=["dagster"],
    license="Apache-2.0",
    description="A collection of examples to demonstrate Dagster features",
    url="https://github.com/dagster-io/dagster/tree/master/examples/experimental/playground",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
