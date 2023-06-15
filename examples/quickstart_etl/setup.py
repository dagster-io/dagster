from setuptools import find_packages, setup

setup(
    name="quickstart_etl",
    packages=find_packages(exclude=["quickstart_etl_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud",
        "boto3",
        "pandas",
        "matplotlib",
        "textblob",
        "tweepy",
        "wordcloud",
        "croniter<1.4.0",  # https://github.com/dagster-io/dagster/pull/14811
    ],
    extras_require={"dev": ["dagit", "pytest"]},
)
