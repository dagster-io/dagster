from setuptools import find_packages, setup

setup(
    name="with_wandb",
    packages=find_packages(exclude=["with_wandb_tests"]),
    install_requires=[
        "dagster",
        "dagster-wandb",
        "onnxruntime",
        "skl2onnx",
        # Pin onnx with min version to ensure protobuf 4 compatability
        # Pin onnx with max version until https://github.com/onnx/onnx/issues/5202 is resolved
        "onnx>=1.13.0,<1.14.0",
        "joblib",
        "torch",
        "torchvision",
    ],
    extras_require={"dev": ["dagit", "pytest"]},
)
