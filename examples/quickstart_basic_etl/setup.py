from setuptools import find_packages, setup

setup(
    name="quickstart_basic_etl",
    packages=find_packages(exclude=["quickstart_basic_etl_tests"]),
    install_requires=[
        "dagster",
        "PyGithub",
        "pandas",
        "matplotlib",
        "textblob",
        "tweepy",
        "dagster-cloud",
        "wordcloud",
    ],
    extras_require={"dev": ["dagit", "pytest"]},
)
