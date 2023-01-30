from setuptools import find_packages, setup

setup(
    name="script_to_assets_branching_io_manager",
    version="1!0+dev",
    author="Elementl",
    author_email="hello@elementl.com",
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["test"]),
    install_requires=[
        "dagster",
        "dagster-graphql",
        "dagit",
        "matplotlib",
        "pandas",
        "wordcloud",
    ],
    extras_require={"dev": ["dagit", "pytest"], "tests": ["mypy", "pylint", "pytest"]},
)
