from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="assets_reconciliation",
        packages=find_packages(exclude=["assets_reconciliation_tests*"]),
        install_requires=[
            "dagster",
            "dagit",
            "dagster-pandera",
            "pandera",
            "pandas",
        ],
        extras_require={"test": ["pytest"]},
    )
