from setuptools import setup, find_packages

setup(
    name='bollinger',
    version='dev',
    packages=find_packages(),    
    install_requires=[
        'pandera',
        'seaborn',
        'jupyterlab',
        'pandas',
    ]
)
