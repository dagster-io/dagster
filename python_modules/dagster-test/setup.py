from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="dagster-test",
        version="0+dev",
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="A Dagster integration for test",
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-test",
        classifiers=[
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["dagster_test_tests*"]),
        install_requires=[
            "dagster",
            "pyspark",
        ],
        extras_require={
            "test": ["dagster[test]"],
        },
        zip_safe=False,
    )
