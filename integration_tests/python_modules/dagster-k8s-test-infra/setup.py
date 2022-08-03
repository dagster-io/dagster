from setuptools import find_packages, setup  # type: ignore

if __name__ == "__main__":
    setup(
        name="dagster-k8s-test-infra",
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="A Dagster integration for k8s-test-infra",
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-k8s-test-infra",
        classifiers=[
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["test"]),
        install_requires=["dagster", "docker", "boto3"],
        extras_require={
            "test": ["dagster[test]"],
        },
        zip_safe=False,
    )
