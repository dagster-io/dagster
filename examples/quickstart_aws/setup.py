from setuptools import find_packages, setup

setup(
    name="quickstart_aws",
    packages=find_packages(exclude=["quickstart_aws_tests"]),
    install_requires=[
        "dagster",
        "dagster-aws",
        "dagster-cloud",
        "pandas",
        "matplotlib",
        "wordcloud",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
