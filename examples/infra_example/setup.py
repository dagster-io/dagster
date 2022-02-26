import setuptools

setuptools.setup(
    name="infra_example",
    packages=setuptools.find_packages(exclude=["infra_example_tests"]),
    install_requires=[
        "dagster==dev",
        "dagit==dev",
        "pytest",
        "cdktf~=0.9.2",
        "cdktf-cdktf-provider-aws~=5.0.29",
    ],
)
