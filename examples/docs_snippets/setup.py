from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="docs_snippets",
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        url="https://github.com/dagster-io/dagster/tree/master/examples/docs_snippets",
        classifiers=[
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["test"]),
        install_requires=["dagster"],
        extras_require={"full": ["seaborn", "scikit-learn"]},
    )
