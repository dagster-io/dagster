from setuptools import find_packages, setup

setup(
    name="project_dagster_modal_pipes",
    packages=find_packages(exclude=["project_dagster_modal_pipes_tests"]),
    install_requires=[
        "dagster",
        "dagster-aws",
        "dagster-modal>=0.0.2",
        "dagster-openai",
        "feedparser",
        "ffmpeg-python",
        "modal",
        "openai",
        "tiktoken",
        "yagmail",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest", "ruff"]},
)
