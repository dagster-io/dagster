from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="dagster-k8s-test-infra",
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="A Dagster integration for k8s-test-infra",
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-k8s-test-infra",
        classifiers=[
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["test"]),
        install_requires=["dagster"],
        tests_require=[],
        zip_safe=False,
    )
