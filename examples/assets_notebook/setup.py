from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="assets_notebook",
        packages=find_packages(exclude=["assets_notebook_tests"]),
        install_requires=[
            "dagster",
            # TODO replace with completed integration lib
            "papermill-origami @ git+https://github.com/noteable-io/papermill-origami.git@9fa10d0f53d24a7d0759fd96237225024010d792#egg=papermill-origami",
            "pandas",
            "numpy",
            "scikit-learn"

        ],
        extras_require={"dev": ["dagit", "pytest"]},
    )
