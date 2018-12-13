import contextlib
import os
import re
import subprocess

PUBLISH_COMMAND = '''rm -rf dist/ && {additional_steps}\\
python3 setup.py sdist bdist-wheel && \\
twine upload dist/*
'''

DAGIT_ADDITIONAL_STEPS = '''pushd ./dagit/webapp; \\
yarn install && \\
yarn build; \\
popd
'''


@contextlib.contextmanager
def pushd_module(module_name):
    relative_path = 'python_modules/{module_name}'.format(module_name)
    cwd = os.getcwd()
    os.chdir(os.path.abspath(relative_path))
    try:
        yield
    finally:
        os.chdir(cwd)


def publish_dagster():
    with pushd_module('dagster'):
        subprocess.run(PUBLISH_COMMAND.format(additional_steps=''))


def publish_dagit():
    with pushd_module('dagit'):
        subprocess.run(
            PUBLISH_COMMAND.format(additional_steps=DAGIT_ADDITIONAL_STEPS))


def publish_dagstermill():
    with pushd_module('dagstermill'):
        subprocess.run(PUBLISH_COMMAND.format(additional_steps=''))


def publish_all():
    publish_dagster()
    publish_dagit()
    publish_dagstermill()


def get_git_tag():
    try:
        git_tag = subprocess.check_output(
            ['git', 'describe', '--exact-match', '--abbrev=0'],
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc_info:
        match = re.match(
            'fatal: no tag exactly matches \'(?P<commit>[a-z0-9]+)\'',
            exc_info.output)
        if match:
            raise Exception(
                'Bailing: there is no git tag for the current commit, {commit}'.
                format(commit=match.group('commit'))
            )
        else:
            raise

    return git_tag


def check_versions():
    git_tag = get_git_tag()

    for module_name in ['dagster', 'dagit', 'dagstermill']:
        with pushd_module(module_name):
            version = {}
            with open('{module_name}/version.py'.format(
                    module_name=module_name)) as fp:
                exec(fp.read(), version)  # pylint: disable=W0122
            version = version['__version__']
            assert version == git_tag, \
                'Version {version} does not match expected git tag {git_tag}'.format(
                    version=version, git_tag=git_tag
                )


if __name__ == '__main__':
    check_versions()
