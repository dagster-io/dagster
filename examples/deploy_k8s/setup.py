from setuptools import find_packages, setup

setup(
    name="deploy_k8s",
    version="0+dev",
    author_email="hello@elementl.com",
    packages=find_packages(exclude=["deploy_k8s_tests*"]),
    include_package_data=True,
    install_requires=["dagster"],
    python_requires=">=3.6,<=3.10",
    author="Elementl",
    license="Apache-2.0",
    description="Example of deploying Dagster to Kubernetes.",
    url="https://github.com/dagster-io/dagster/tree/master/examples/deploy_k8s",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
