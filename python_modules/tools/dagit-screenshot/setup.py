from setuptools import find_packages, setup

setup(
    name="dagit-screenshot",
    version="0+dev",
    author_email="hello@elementl.com",
    packages=find_packages(exclude=["dagit_screenshot_tests*"]),  # same as name
    author="Elementl",
    license="Apache-2.0",
    description="Utility for taking automated screenshots from dagit",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    install_requires=["click>=6", "selenium", "pyyaml", "typing-extensions>=4"],  # external packages as dependencies
    extras_require={
        "test": ["dagster[test]"],
    },
    entry_points={
        "console_scripts": [
            "dagit-screenshot = dagit_screenshot.cli:main",
        ]
    }
)
