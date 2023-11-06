from setuptools import find_packages, setup

setup(
    name="assets_yaml_dsl",
    packages=find_packages(exclude=["assets_yaml_dsl_tests"]),
    install_requires=["dagster", "pandas", "dagster-pipes"],
    license="Apache-2.0",
    description="Dagster example of yaml dsl for building asset graphs",
    url="https://github.com/dagster-io/dagster/tree/master/examples/assets_yaml_dsl",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
