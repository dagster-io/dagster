import sys

from setuptools import find_packages, setup

# pylint: disable=E0401, W0611
if sys.version_info[0] < 3:
    import __builtin__ as builtins
else:
    import builtins

version = {}
with open("dagster_framework/aws/version.py") as fp:
    exec(fp.read(), version)  # pylint: disable=W0122

setup(
    name='dagster_framework_aws',
    version=version['__version__'],
    author='Elementl',
    license='Apache-2.0',
    description='Package for AWS-specific Dagster framework solid and resource components.',
    url='https://github.com/dagster-io/dagster/tree/master/python_modules/dagster-framework/aws',
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    packages=find_packages(exclude=['test']),
    install_requires=['boto3==1.9.*', 'dagster'],
    zip_safe=False,
)
