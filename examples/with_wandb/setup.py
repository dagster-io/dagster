from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="with_wandb",
        packages=find_packages(exclude=["with_wandb_tests"]),
        install_requires=[
            "dagster",
            "dagster-wandb",
            "onnxruntime",
            "skl2onnx",
            "joblib",
        ],
        extras_require={"test": ["dagit", "pytest"]},
    )
