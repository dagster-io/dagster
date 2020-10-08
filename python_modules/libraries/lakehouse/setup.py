from setuptools import setup

if __name__ == "__main__":
    setup(
        name="lakehouse",
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        install_requires=["dagster"],
        entry_points={"console_scripts": ["house = lakehouse.cli:main"]},
    )
