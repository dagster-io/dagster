from setuptools import find_packages, setup  # type: ignore

if __name__ == "__main__":
    setup(
        name="dagster-test",
        version="dev",
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="A Dagster integration for test",
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-test",
        classifiers=[
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["test"]),
        install_requires=["dagster", "pyspark",],
        zip_safe=False,
    )
