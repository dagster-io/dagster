from setuptools import find_packages, setup

setup(
    name="airline_demo",
    version="0+dev",
    author_email="hello@elementl.com",
    packages=find_packages(exclude=["airline_demo_tests*"]),
    include_package_data=True,
    install_requires=["dagster"],
    python_requires=">=3.6,<=3.10",
    author="Elementl",
    license="Apache-2.0",
    description="A basic example of Dagster with airline.",
    url="https://github.com/dagster-io/dagster/tree/master/examples/airline_demo",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
