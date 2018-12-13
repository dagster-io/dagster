import contextlib
import os
import re
import subprocess

import click
import packaging.version

from itertools import groupby

PUBLISH_COMMAND = '''rm -rf dist/ && {additional_steps}\\
python setup.py sdist bdist_wheel && \\
twine upload dist/*
'''

DAGIT_ADDITIONAL_STEPS = '''pushd ./dagit/webapp; \\
yarn install && \\
yarn build; \\
popd
'''

MODULE_NAMES = ['dagster', 'dagit', 'dagstermill']


def all_equal(iterable):
    g = groupby(iterable)
    return next(g, True) and not next(g, False)


def path_to_module(module_name):
    relative_path = 'python_modules/{module_name}'.format(
        module_name=module_name)
    return os.path.abspath(relative_path)


@contextlib.contextmanager
def pushd_module(module_name):
    old_cwd = os.getcwd()
    new_cwd = path_to_module(module_name)
    os.chdir(new_cwd)
    try:
        yield new_cwd
    finally:
        os.chdir(old_cwd)


def publish_dagster():
    with pushd_module('dagster') as cwd:
        subprocess.check_output(
            PUBLISH_COMMAND.format(additional_steps=''),
            stderr=subprocess.STDOUT,
            cwd=cwd,
            shell=True)


def publish_dagit():
    with pushd_module('dagit') as cwd:
        subprocess.check_output(
            PUBLISH_COMMAND.format(additional_steps=DAGIT_ADDITIONAL_STEPS),
            stderr=subprocess.STDOUT,
            cwd=cwd,
            shell=True)


def publish_dagstermill():
    with pushd_module('dagstermill') as cwd:
        subprocess.check_output(
            PUBLISH_COMMAND.format(additional_steps=''),
            stderr=subprocess.STDOUT,
            cwd=cwd,
            shell=True)


def publish_all():
    try:
        publish_dagster()
        publish_dagit()
        publish_dagstermill()
    except subprocess.CalledProcessError as exc_info:
        raise Exception(str(exc_info.output))


def get_most_recent_git_tag():
    try:
        git_tag = str(
            subprocess.check_output(
                ['git', 'describe', '--abbrev=0'],
                stderr=subprocess.STDOUT)).strip('\'b\\n')
    except subprocess.CalledProcessError as exc_info:
        raise Exception(str(exc_info.output))
    return git_tag


def get_git_tag():
    try:
        git_tag = str(
            subprocess.check_output(
                ['git', 'describe', '--exact-match', '--abbrev=0'],
                stderr=subprocess.STDOUT)).strip('\'b\\n')
    except subprocess.CalledProcessError as exc_info:
        match = re.search(
            'fatal: no tag exactly matches \'(?P<commit>[a-z0-9]+)\'',
            str(exc_info.output))
        if match:
            raise Exception(
                'Bailing: there is no git tag for the current commit, {commit}'.
                format(commit=match.group('commit')))
        raise Exception(str(exc_info.output))

    return git_tag


def set_git_tag(tag, signed=False):
    try:
        if signed:
            subprocess.check_output(
                ['git', 'tag', '-s', '-m', tag, tag], stderr=subprocess.STDOUT)
        else:
            subprocess.check_output(
                ['git', 'tag', '-a', '-m', tag, tag], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc_info:
        match = re.search('error: gpg failed to sign the data',
                          str(exc_info.output))
        if match:
            raise Exception(
                'Bailing: cannot sign tag. You may find '
                'https://stackoverflow.com/q/39494631/324449 helpful. Original error '
                'output:\n{output}'.format(output=str(exc_info.output)))

        match = re.search('fatal: tag \'(?P<tag>[\.a-z0-9]+)\' already exists',
                          str(exc_info.output))
        if match:
            raise Exception(
                'Bailing: cannot release version tag {tag}: already exists'.
                format(tag=match.group('tag')))
        raise Exception(str(exc_info.output))


def format_module_versions(module_versions):
    return '\n'.join([
        '    {module_name}: {module_version}'.format(
            module_name=module_name, module_version=module_version)
        for module_name, module_version in module_versions.items()
    ])


def get_versions(modules=MODULE_NAMES):
    module_versions = {}
    for module_name in MODULE_NAMES:
        with pushd_module(module_name):
            version = {}
            with open('{module_name}/version.py'.format(
                    module_name=module_name)) as fp:
                exec(fp.read(), version)  # pylint: disable=W0122
            module_versions[module_name] = version['__version__']
    return module_versions


def check_versions_equal():
    module_versions = get_versions()
    assert all_equal(module_versions.values()), \
        'Module versions must be in lockstep to release. Found:\n{versions}'.format(
            versions=format_module_versions(module_versions)
        )
    return module_versions[MODULE_NAMES[0]]


def check_versions():
    version = check_versions_equal()
    git_tag = get_git_tag()

    assert version == git_tag, \
        'Version {version} does not match expected git tag {git_tag}'.format(
            version=version, git_tag=git_tag
        )


def set_new_version(version):
    for module_name in MODULE_NAMES:
        with pushd_module(module_name):
            with open(
                    os.path.abspath('{module_name}/version.py'.format(
                        module_name=module_name)),
                    'w') as fd:
                fd.write(
                    '__version__ = \'{version}\'\n'.format(version=version))


def commit_new_version(version):
    try:
        for module_name in MODULE_NAMES:
            subprocess.check_output(
                [
                    'git', 'add',
                    os.path.join(
                        path_to_module(module_name), module_name, 'version.py')
                ],
                stderr=subprocess.STDOUT)
        subprocess.check_output(
            [
                'git',
                'commit',
                '--no-verify',
                '-m',
                '\'{version}\''.format(version=version),
            ],
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc_info:
        raise Exception(exc_info.output)


def check_new_version(version):
    parsed_version = packaging.version.parse(version)
    module_versions = get_versions()
    if not all_equal(module_versions.values()):
        print(
            'Warning! Found repository in a bad state. Existing package versions were not '
            'equal:\n{versions}'.format(
                versions=format_module_versions(module_versions)))
    errors = {}
    for module_name, module_version in module_versions.items():
        if packaging.version.parse(module_version) >= parsed_version:
            errors[module_name] = module_version
    if errors:
        raise Exception(
            'Found modules with existing versions greater than or equal to the new version '
            '{version}:\n{versions}'.format(
                version=version,
                versions=format_module_versions(module_versions)))
    return True


@click.group()
def cli():
    pass


@cli.command()
def publish():
    print(
        '''WARNING: This will fail (or hang forever) unless you have credentials available to
PyPI, preferably in the form of a ~/.pypirc file as follows:

    [distutils]
    index-servers =
    pypi

    [pypi]
    repository: https://upload.pypi.org/legacy/
    username: <username>
    password: <password>
''')
    print(
        'Checking that module versions are in lockstep and match git tag on most recent commit...'
    )
    check_versions()
    print('Publishing packages to PyPI...')
    publish_all()


@cli.command()
@click.argument('version')
def release(version):
    check_new_version(version)
    set_new_version(version)
    commit_new_version(version)
    set_git_tag(version)


@cli.command()
def version():
    print(get_most_recent_git_tag())


cli = click.CommandCollection(sources=[cli])

if __name__ == '__main__':
    cli()
