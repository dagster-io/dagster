from setuptools import find_packages, setup

if __name__ == '__main__':
    setup(
        name='test-pipelines',
        author='Elementl',
        author_email='hello@elementl.com',
        license='Apache-2.0',
        description='Dagster is an opinionated programming model for data pipelines.',
        url='https://github.com/dagster-io/dagster',
        packages=find_packages(),
        install_requires=[],
        entry_points={'console_scripts': ['dagster = dagster.cli:main']},
    )
