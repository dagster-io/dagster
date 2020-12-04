from setuptools import find_packages, setup


def get_version():
    version = {}
    with open('dagster_dynatrace/version.py') as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version['__version__']


parser = argparse.ArgumentParser()
parser.add_argument('--nightly', action='store_true')


if __name__ == '__main__':
    setup(
        name='dagster-dynatrace',
        version=get_version(),
        author='Elementl',
        author_email='hello@elementl.com',
        license='Apache-2.0',
        description='Package for dynatrace Dagster framework components.',
        url='https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-dynatrace',
        classifiers=[
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: OS Independent',
        ],
        packages=find_packages(exclude=['test']),
        install_requires=['dagster', 'dynatrace'],
        zip_safe=False,
    )
