from setuptools import find_packages, setup

setup(
    name="with_wandb",
    packages=find_packages(exclude=["with_wandb_tests"]),
    install_requires=[
        "dagster",
        "dagster-wandb",
        "onnxruntime",
        "skl2onnx",
        "joblib",
        "torch",
    ],
    extras_require={"dev": ["dagit", "pytest"]},
)
