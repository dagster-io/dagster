from setuptools import find_packages, setup

setup(
    name="quickstart_snowflake",
    packages=find_packages(exclude=["quickstart_snowflake_tests"]),
    install_requires=[
        "dagster",
        # snowflake-connector-python[pandas] is included by dagster-snowflake-pandas but it does
        # not get included during pex dependency resolution, so we directly add this dependency
        "snowflake-connector-python[pandas]",
        "dagster-snowflake-pandas",
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
