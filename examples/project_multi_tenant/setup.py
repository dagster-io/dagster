from setuptools import find_packages, setup


setup(
    name="project_multi_tenant",
    version="1!0+dev",
    packages=find_packages(
        include=[
            "shared",
            "shared.*",
            "harbor_outfitters",
            "harbor_outfitters.*",
            "summit_financial",
            "summit_financial.*",
            "beacon_hq",
            "beacon_hq.*",
            "tests",
        ]
    ),
)
