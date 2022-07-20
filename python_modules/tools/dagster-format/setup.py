from setuptools import find_packages, setup

setup(
    name="dagster-format",
    version="0+dev",
    packages=find_packages(exclude="dagster_format_tests*"),
    install_requires=[
        "click>=5",
    ],
    extras_require={
        "test": ["dagster[test]"],
    },
    entry_points={
        "console_scripts": [
            "dagster-format = dagster_format.cli:main",
        ]
    },
)
