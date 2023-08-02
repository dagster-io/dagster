from setuptools import find_packages, setup

setup(
    name="with_wandb",
    packages=find_packages(exclude=["with_wandb_tests"]),
    install_requires=[
        "dagster",
        "dagster-wandb",
        "onnxruntime",
        "skl2onnx",
        "onnx>=1.13.0",  # Ensure a version is installed that is protobuf 4 compatible
        "joblib",
        "torch",
        "torchvision",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
