from setuptools import find_packages, setup

setup(
    name="dagster-ui-screenshot",
    version="1!0+dev",
    author_email="hello@dagsterlabs.com",
    packages=find_packages(exclude=["dagster_ui_screenshot_tests*"]),  # same as name
    install_requires=[
        "click>=6",
        "selenium",
        "pyyaml",
        "typing-extensions>=4",
    ],  # external packages as dependencies
    author="Dagster Labs",
    license="Apache-2.0",
    description="Utility for taking automated screenshots from the Dagster UI",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "dagster-ui-screenshot = dagster_ui_screenshot.cli:main",
        ]
    },
)
