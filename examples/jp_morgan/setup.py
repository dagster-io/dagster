from setuptools import setup, find_packages

setup(
    name='jp_morgan',
    version='dev',
    packages=find_packages(),    
    install_requires=[
        'pandera',
        'seaborn',
        'jupyterlab',
        'pandas',
    ]
)
