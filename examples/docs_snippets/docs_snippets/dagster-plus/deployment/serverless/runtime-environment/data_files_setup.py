from setuptools import find_packages, setup

setup(
    name="quickstart_etl",
    packages=find_packages(exclude=["quickstart_etl_tests"]),
    # highlight-start
    # Here "data/*" is relative to the quickstart_etl sub directory.
    package_data={"quickstart_etl": ["data/*"]},
    # highlight-end
    install_requires=["dagster"],
)
