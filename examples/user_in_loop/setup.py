from setuptools import setup

setup(
    name="user_in_loop",
    version="0+dev",
    author_email="hello@elementl.com",
    packages=["user_in_loop"],
    include_package_data=True,
    install_requires=["dagster"],
    author="Elementl",
    license="Apache-2.0",
    description="Dagster example for how to write a user-in-the-loop pipeline.",
    url="https://github.com/dagster-io/dagster/tree/master/examples/user_in_loop",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
