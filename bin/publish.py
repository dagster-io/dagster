#!/usr/bin/env python3

"""Tools to manage tagging and publishing releases of the Dagster projects.

Please follow the checklist in RELEASING.md at the root of this repository.

For detailed usage instructions, please consult the command line help,
available by running `python publish.py --help`.
"""
# distutils issue: https://github.com/PyCQA/pylint/issues/73

import contextlib
import datetime
import fnmatch
import inspect
import os
import subprocess
import sys
import tempfile
import urllib
from collections import defaultdict
from distutils import spawn  # pylint: disable=no-name-in-module
from itertools import groupby

import click
import packaging.version
import requests
import slackclient
import virtualenv

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, BASE_PATH)

from git_tag import get_git_tag, get_most_recent_git_tag, set_git_tag  # isort:skip
from pypirc import ConfigFileError, RCParser  # isort:skip


assert os.getenv('SLACK_RELEASE_BOT_TOKEN'), 'No SLACK_RELEASE_BOT_TOKEN env variable found.'
slack_client = slackclient.SlackClient(os.environ['SLACK_RELEASE_BOT_TOKEN'])


PYPIRC_EXCEPTION_MESSAGE = '''You must have credentials available to PyPI in the form of a
~/.pypirc file (see: https://docs.python.org/2/distutils/packageindex.html#pypirc):

    [distutils]
    index-servers =
        pypi

    [pypi]
    repository: https://upload.pypi.org/legacy/
    username: <username>
    password: <password>
'''


def check_output(cmd, dry_run=True):
    if dry_run:
        click.echo(
            click.style('Dry run; not running.', fg='red') + ' Would run: %s' % ' '.join(cmd)
        )
        return None
    else:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT)


def script_relative_path(file_path):
    scriptdir = inspect.stack()[1][1]
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(scriptdir)), file_path))


def which_(exe):
    '''Uses distutils to look for an executable, mimicking unix which'''
    # https://github.com/PyCQA/pylint/issues/73
    return spawn.find_executable(exe)


def construct_publish_comands(additional_steps=None, nightly=False):
    '''Get the shell commands we'll use to actually build and publish a package to PyPI.'''
    publish_commands = (
        ['rm -rf dist']
        + (additional_steps if additional_steps else [])
        + [
            'python setup.py sdist bdist_wheel{nightly}'.format(
                nightly=' --nightly' if nightly else ''
            ),
            'twine upload --verbose dist/*',
        ]
    )

    return publish_commands


# The root modules managed by this script
MODULE_NAMES = [
    'dagster',
    'dagit',
    'dagster-graphql',
    'dagstermill',
]

# Removed hard-coded list in favor of automatic scan of libraries folder
# List of subdirectories in directory: https://stackoverflow.com/a/973488
LIBRARY_MODULES = next(os.walk(os.path.join(BASE_PATH, '..', 'python_modules', 'libraries')))[1]

EXPECTED_PYTHON_MODULES = ['automation', 'libraries'] + MODULE_NAMES

EXPECTED_LIBRARIES = LIBRARY_MODULES


def normalize_module_name(name):
    '''Our package convention is to find the source for module foo_bar in foo-bar/foo_bar.'''
    return name.replace('-', '_')


def all_equal(iterable):
    g = groupby(iterable)
    return next(g, True) and not next(g, False)


def path_to_module(module_name, library=False):
    if library:
        return script_relative_path(
            '../python_modules/libraries/{module_name}'.format(module_name=module_name)
        )

    return script_relative_path('../python_modules/{module_name}'.format(module_name=module_name))


@contextlib.contextmanager
def pushd_module(module_name, library=False):
    old_cwd = os.getcwd()
    new_cwd = path_to_module(module_name, library)
    os.chdir(new_cwd)
    try:
        yield new_cwd
    finally:
        os.chdir(old_cwd)


def publish_module(module, nightly=False, library=False, additional_steps='', dry_run=True):
    with pushd_module(module, library) as cwd:
        for command in construct_publish_comands(
            additional_steps=additional_steps, nightly=nightly
        ):
            if dry_run:
                click.echo(
                    click.style('Dry run; not running.', fg='red')
                    + ' Would run {cwd}:$ {cmd}'.format(cmd=command, cwd=cwd)
                )
            else:
                click.echo('About to run command {cwd}:$ {cmd}'.format(cmd=command, cwd=cwd))
                process = subprocess.Popen(
                    command, stderr=subprocess.PIPE, cwd=cwd, shell=True, stdout=subprocess.PIPE
                )
                for line in iter(process.stdout.readline, b''):
                    click.echo(line.decode('utf-8'))

                process.wait()
                assert process.returncode == 0, (
                    'Something went wrong while attempting to publish module {module_name}! '
                    'Got code {code} from command "{command}" in cwd {cwd}'.format(
                        module_name=module, code=process.returncode, command=command, cwd=cwd
                    )
                )


def publish_all(nightly, dry_run=True):
    for module in MODULE_NAMES:
        if module == 'dagit':
            publish_module(module, nightly, additional_steps=['./build_js.sh'], dry_run=dry_run)
        else:
            publish_module(module, nightly, dry_run=dry_run)

    for module in LIBRARY_MODULES:
        publish_module(module, nightly, library=True, dry_run=dry_run)


def format_module_versions(module_versions):
    nightlies = defaultdict(list)
    versions = defaultdict(list)

    for module_name, module_version in module_versions.items():
        nightlies[module_version['__nightly__']].append(module_name)
        versions[module_version['__version__']].append(module_name)

    res = '\n'
    for key, libraries in nightlies.items():
        res += '%s:\n\t%s\n\n' % (key, '\n\t'.join(libraries))

    res += '\n'

    for key, libraries in versions.items():
        res += '%s:\n\t%s\n' % (key, '\n\t'.join(libraries))

    return res


def get_module_versions(module_name, library=False):
    with pushd_module(module_name, library):
        module_version = {}
        with open(
            '{module_name}/version.py'.format(module_name=normalize_module_name(module_name))
        ) as fp:
            exec(fp.read(), module_version)  # pylint: disable=W0122

        assert (
            '__version__' in module_version and '__nightly__' in module_version
        ), 'Bad version for module {module_name}'.format(module_name=module_name)
        return {
            '__version__': module_version['__version__'],
            '__nightly__': module_version['__nightly__'],
        }


def get_versions():
    module_versions = {}
    for module_name in MODULE_NAMES:
        module_versions[module_name] = get_module_versions(module_name)
    for library_module in LIBRARY_MODULES:
        module_versions[library_module] = get_module_versions(library_module, library=True)
    return module_versions


def check_versions_equal(nightly=False):
    module_versions = get_versions()

    source = '__nightly__' if nightly else '__version__'

    if not all_equal([module_version[source] for module_version in module_versions.values()]):
        click.echo(
            'Module versions must be in lockstep to release. Found:\n{versions}'.format(
                versions=format_module_versions(module_versions)
            )
        )
        sys.exit(1)

    return module_versions[MODULE_NAMES[0]]


def check_versions(nightly=False):
    module_version = check_versions_equal(nightly)
    if not nightly:
        git_tag = get_git_tag()
        assert (
            module_version['__version__'] == git_tag
        ), 'Version {version} does not match expected git tag {git_tag}'.format(
            version=module_version['__version__'], git_tag=git_tag
        )

    return module_version


def set_version(module_name, new_version, nightly, library=False, dry_run=True):
    with pushd_module(module_name, library):
        output = (
            '__version__ = \'{new_version}\'\n'
            '\n'
            '__nightly__ = \'{nightly}\'\n'.format(new_version=new_version, nightly=nightly)
        )

        filename = os.path.abspath(
            '{module_name}/version.py'.format(module_name=normalize_module_name(module_name))
        )

        if dry_run:
            click.echo(
                click.style('Dry run; not running.', fg='red')
                + ' Would write: %s to %s' % (output, filename)
            )
        else:
            with open(filename, 'w') as fd:
                fd.write(output)


def get_nightly_version():
    return datetime.datetime.utcnow().strftime('%Y.%m.%d')


def increment_nightly_version(module_name, module_version, library=False, dry_run=True):
    new_nightly = get_nightly_version()
    set_version(module_name, module_version['__version__'], new_nightly, library, dry_run=dry_run)
    return {'__version__': module_version['__version__'], '__nightly__': new_nightly}


def increment_nightly_versions(dry_run=True):
    versions = get_versions()
    for module_name in MODULE_NAMES:
        new_version = increment_nightly_version(module_name, versions[module_name], dry_run=dry_run)
    for library_module in LIBRARY_MODULES:
        new_version = increment_nightly_version(
            library_module, versions[module_name], library=True, dry_run=dry_run
        )
    return new_version


def set_new_version(new_version, dry_run=True):
    for module_name in MODULE_NAMES:
        set_version(module_name, new_version, get_nightly_version(), dry_run=dry_run)
    for library_module in LIBRARY_MODULES:
        set_version(
            library_module, new_version, get_nightly_version(), library=True, dry_run=dry_run,
        )


def commit_new_version(new_version, dry_run=True):
    try:
        for module_name in MODULE_NAMES:
            cmd = [
                'git',
                'add',
                os.path.join(
                    path_to_module(module_name), normalize_module_name(module_name), 'version.py'
                ),
            ]
            check_output(cmd, dry_run=dry_run)
        for library_module in LIBRARY_MODULES:
            cmd = [
                'git',
                'add',
                os.path.join(
                    path_to_module(library_module, library=True),
                    normalize_module_name(library_module),
                    'version.py',
                ),
            ]
            check_output(cmd, dry_run=dry_run)

        cmd = [
            'git',
            'commit',
            '--no-verify',
            '-m',
            '{new_version}'.format(new_version=new_version),
        ]
        check_output(cmd, dry_run=dry_run)

    except subprocess.CalledProcessError as exc_info:
        raise Exception(exc_info.output)


def check_existing_version():
    module_versions = get_versions()
    if not all_equal(module_versions.values()):
        click.echo(
            'Warning! Found repository in a bad state. Existing package versions were not '
            'equal:\n{versions}'.format(versions=format_module_versions(module_versions))
        )
    return module_versions


def check_new_version(new_version):
    parsed_version = packaging.version.parse(new_version)
    module_versions = check_existing_version()
    errors = {}
    last_version = None
    for module_name, module_version in module_versions.items():
        last_version = module_version
        if packaging.version.parse(module_version['__version__']) >= parsed_version:
            errors[module_name] = module_version['__version__']
    if errors:
        raise Exception(
            'Bailing: Found modules with existing versions greater than or equal to the new '
            'version {new_version}:\n{versions}'.format(
                new_version=new_version, versions=format_module_versions(module_versions)
            )
        )

    if not (
        parsed_version.is_prerelease
        or parsed_version.is_postrelease
        or parsed_version.is_devrelease
    ):
        parsed_previous_version = packaging.version.parse(last_version['__version__'])
        if not (parsed_previous_version.release == parsed_version.release):
            should_continue = input(
                'You appear to be releasing a new version, {new_version}, without having '
                'previously run a prerelease.\n(Last version found was {previous_version})\n'
                'Are you sure you know what you\'re doing? (N/!)'.format(
                    new_version=new_version, previous_version=last_version['__version__']
                )
            )
            if not should_continue == '!':
                raise Exception('Bailing! Run a pre-release before continuing.')
    return True


def check_git_status():
    changes = subprocess.check_output(['git', 'status', '--porcelain'])
    if changes != b'':
        raise Exception(
            'Bailing: Cannot publish with changes present in git repo:\n{changes}'.format(
                changes=changes
            )
        )


def check_for_cruft(autoclean):
    CRUFTY_DIRECTORIES = ['.tox', 'build', 'dist', '*.egg-info', '__pycache__', '.pytest_cache']
    found_cruft = []
    for module_name in MODULE_NAMES:
        for dir_ in os.listdir(path_to_module(module_name, library=False)):
            for potential_cruft in CRUFTY_DIRECTORIES:
                if fnmatch.fnmatch(dir_, potential_cruft):
                    found_cruft.append(
                        os.path.join(path_to_module(module_name, library=False), dir_)
                    )

    for library_module_name in LIBRARY_MODULES:
        for dir_ in os.listdir(path_to_module(library_module_name, library=True)):
            for potential_cruft in CRUFTY_DIRECTORIES:
                if fnmatch.fnmatch(dir_, potential_cruft):
                    found_cruft.append(
                        os.path.join(path_to_module(library_module_name, library=True), dir_)
                    )

    if found_cruft:
        if autoclean:
            wipeout = 'Y'
        else:
            wipeout = input(
                'Found potentially crufty directories:\n'
                '    {found_cruft}\n'
                '***We strongly recommend releasing from a fresh git clone!***\n'
                'Automatically remove these directories and continue? (N/!)'.format(
                    found_cruft='\n    '.join(found_cruft)
                )
            )
        if wipeout == '!':
            for cruft_dir in found_cruft:
                subprocess.check_output(['rm', '-rfv', cruft_dir])
        else:
            raise Exception(
                'Bailing: Cowardly refusing to publish with potentially crufty directories '
                'present! We strongly recommend releasing from a fresh git clone.'
            )

    found_pyc_files = []

    for root, dir_, files in os.walk(script_relative_path('..')):
        for file_ in files:
            if file_.endswith('.pyc'):
                found_pyc_files.append(os.path.join(root, file_))

    if found_pyc_files:
        if autoclean:
            wipeout = 'Y'
        else:
            wipeout = input(
                'Found {n_files} .pyc files.\n'
                'We strongly recommend releasing from a fresh git clone!\n'
                'Automatically remove these files and continue? (N/!)'.format(
                    n_files=len(found_pyc_files)
                )
            )
        if wipeout == '!':
            for file_ in found_pyc_files:
                os.unlink(file_)
        else:
            raise Exception(
                'Bailing: Cowardly refusing to publish with .pyc files present! '
                'We strongly recommend releasing from a fresh git clone.'
            )


def check_directory_structure():
    unexpected_modules = []
    expected_modules_not_found = []
    unexpected_libraries = []
    expected_libraries_not_found = []

    module_directories = [
        dir_
        for dir_ in os.scandir(script_relative_path(os.path.join('..', 'python_modules')))
        if dir_.is_dir() and not dir_.name.startswith('.')
    ]

    for module_dir in module_directories:
        if module_dir.name not in EXPECTED_PYTHON_MODULES:
            unexpected_modules.append(module_dir.path)

    for module_dir_name in EXPECTED_PYTHON_MODULES:
        if module_dir_name not in [module_dir.name for module_dir in module_directories]:
            expected_modules_not_found.append(module_dir_name)

    library_directories = [
        dir_
        for dir_ in os.scandir(
            script_relative_path(os.path.join('..', 'python_modules', 'libraries'))
        )
        if dir_.is_dir() and not dir_.name.startswith('.')
    ]

    for library_dir in library_directories:
        if library_dir.name not in EXPECTED_LIBRARIES:
            unexpected_libraries.append(library_dir.path)

    for library_dir_name in EXPECTED_LIBRARIES:
        if library_dir_name not in [library_dir.name for library_dir in library_directories]:
            expected_libraries_not_found.append(library_dir_name)

    if (
        unexpected_modules
        or unexpected_libraries
        or expected_modules_not_found
        or expected_libraries_not_found
    ):
        raise Exception(
            'Bailing: something looks wrong. We\'re either missing modules we expected or modules '
            'are present that we don\'t know about:\n'
            '{expected_modules_not_found_msg}'
            '{unexpected_modules_msg}'
            '{expected_libraries_not_found_msg}'
            '{unexpected_libraries_msg}'.format(
                expected_modules_not_found_msg=(
                    ('\nDidn\'t find expected modules:\n    {expected_modules_not_found}').format(
                        expected_modules_not_found='\n    '.join(sorted(expected_modules_not_found))
                    )
                    if expected_modules_not_found
                    else ''
                ),
                unexpected_modules_msg=(
                    '\nFound unexpected modules:\n    {unexpected_modules}'.format(
                        unexpected_modules='\n    '.join(sorted(unexpected_modules))
                    )
                    if unexpected_modules
                    else ''
                ),
                expected_libraries_not_found_msg=(
                    (
                        '\nDidn\'t find expected libraries:\n    {expected_libraries_not_found}'
                    ).format(
                        expected_libraries_not_found='\n    '.join(
                            sorted(expected_libraries_not_found)
                        )
                    )
                    if expected_libraries_not_found
                    else ''
                ),
                unexpected_libraries_msg=(
                    '\nFound unexpected libraries:\n    {unexpected_libraries}'.format(
                        unexpected_libraries='\n    '.join(sorted(unexpected_libraries))
                    )
                    if unexpected_libraries
                    else ''
                ),
            )
        )


def git_push(tag=None, dry_run=True):
    github_token = os.getenv('GITHUB_TOKEN')
    github_username = os.getenv('GITHUB_USERNAME')
    if github_token and github_username:
        if tag:
            check_output(
                [
                    'git',
                    'push',
                    'https://{github_username}:{github_token}@github.com/dagster-io/dagster.git'.format(
                        github_username=github_username, github_token=github_token
                    ),
                    tag,
                ],
                dry_run=dry_run,
            )
        check_output(
            [
                'git',
                'push',
                'https://{github_username}:{github_token}@github.com/dagster-io/dagster.git'.format(
                    github_username=github_username, github_token=github_token
                ),
            ],
            dry_run=dry_run,
        )
    else:
        if tag:
            check_output(['git', 'push', 'origin', tag], dry_run=dry_run)
        check_output(['git', 'push'], dry_run=dry_run)


CLI_HELP = '''Tools to help tag and publish releases of the Dagster projects.

By convention, these projects live in a single monorepo, and the submodules are versioned in
lockstep to avoid confusion, i.e., if dagster is at 0.3.0, dagit is also expected to be at
0.3.0.

Versions are tracked in the version.py files present in each submodule and in the git tags
applied to the repository as a whole. These tools help ensure that these versions do not drift.
'''


@click.group(help=CLI_HELP)
def cli():
    pass


@cli.command()
@click.option('--nightly', is_flag=True)
@click.option('--autoclean', is_flag=True)
@click.option('--dry-run', is_flag=True)
def publish(nightly, autoclean, dry_run):
    """Publishes (uploads) all submodules to PyPI.

    Appropriate credentials must be available to twine, e.g. in a ~/.pypirc file, and users must
    be permissioned as maintainers on the PyPI projects. Publishing will fail if versions (git
    tags and Python versions) are not in lockstep, if the current commit is not tagged, or if
    there are untracked changes.
    """

    try:
        RCParser.from_file()
    except ConfigFileError:
        raise ConfigFileError(PYPIRC_EXCEPTION_MESSAGE)

    assert '\nwheel' in subprocess.check_output(['pip', 'list']).decode('utf-8'), (
        'You must have wheel installed in order to build packages for release -- run '
        '`pip install wheel`.'
    )

    assert which_('twine'), (
        'You must have twine installed in order to upload packages to PyPI -- run '
        '`pip install twine`.'
    )

    assert which_('yarn'), (
        'You must have yarn installed in order to build dagit for release -- see '
        'https://yarnpkg.com/lang/en/docs/install/'
    )

    click.echo('Checking that module versions are in lockstep')
    checked_version = check_versions(nightly=nightly)
    if not nightly:
        click.echo('... and match git tag on most recent commit...')
        check_git_status()
    click.echo('... and that there is no cruft present...')
    check_for_cruft(autoclean)
    click.echo('... and that the directories look like we expect')
    check_directory_structure()

    click.echo('Publishing packages to PyPI...')

    if nightly:
        new_version = increment_nightly_versions(dry_run)
        commit_new_version(
            'nightly: {nightly}'.format(nightly=new_version['__nightly__']), dry_run=dry_run
        )
        tag = set_git_tag('nightly-{ver}'.format(ver=new_version['__nightly__']), dry_run=dry_run)
        git_push(dry_run=dry_run)
        git_push(tag, dry_run=dry_run)
    publish_all(nightly, dry_run=dry_run)
    git_user = (
        subprocess.check_output(['git', 'config', '--get', 'user.name']).decode('utf-8').strip()
    )
    if not nightly:
        parsed_version = packaging.version.parse(checked_version['__version__'])
        if not parsed_version.is_prerelease and not dry_run:
            slack_client.api_call(
                'chat.postMessage',
                channel='#general',
                text=('{git_user} just published a new version: {version}.').format(
                    git_user=git_user, version=checked_version['__version__']
                ),
            )


@cli.command()
@click.argument('ver')
@click.option('--dry-run', is_flag=True)
def release(ver, dry_run):
    """Tags all submodules for a new release.

    Ensures that git tags, as well as the version.py files in each submodule, agree and that the
    new version is strictly greater than the current version. Will fail if the new version
    is not an increment (following PEP 440). Creates a new git tag and commit.
    """
    check_new_version(ver)
    set_new_version(ver, dry_run=dry_run)
    commit_new_version(ver, dry_run=dry_run)
    set_git_tag(ver, dry_run=dry_run)
    click.echo(
        'Successfully set new version and created git tag {version}. You may continue with the '
        'release checklist.'.format(version=ver)
    )


@cli.command()
def version():
    """Gets the most recent tagged version."""
    module_versions = check_existing_version()
    git_tag = get_most_recent_git_tag()
    parsed_version = packaging.version.parse(git_tag)
    errors = {}
    for module_name, module_version in module_versions.items():
        if packaging.version.parse(module_version['__version__']) > parsed_version:
            errors[module_name] = module_version['__version__']
    if errors:
        click.echo(
            'Warning: Found modules with existing versions that did not match the most recent '
            'tagged version {git_tag}:\n{versions}'.format(
                git_tag=git_tag, versions=format_module_versions(module_versions)
            )
        )
    else:
        click.echo(
            'All modules in lockstep with most recent tagged version: {git_tag}'.format(
                git_tag=git_tag
            )
        )


@cli.command()
@click.argument('version')
def audit(version):  # pylint: disable=redefined-outer-name
    """Checks that the given version is installable from PyPI in a new virtualenv."""

    for module in MODULE_NAMES + LIBRARY_MODULES:
        res = requests.get(
            urllib.parse.urlunparse(
                ('https', 'pypi.org', '/'.join(['pypi', module, 'json']), None, None, None)
            )
        )
        module_json = res.json()
        assert (
            version in module_json['releases']
        ), 'Version not available for module {module_name}, expected {expected}, released version is {received}'.format(
            module_name=module, expected=version, received=module_json['info']['version']
        )

    bootstrap_text = '''
def after_install(options, home_dir):
    for module_name in [{module_names}]:
        subprocess.check_output([
            os.path.join(home_dir, 'bin', 'pip'), 'install', '{{module}}=={version}'.format(
                module=module_name
            )
        ])

'''.format(
        module_names=', '.join(
            [
                '\'{module_name}\''.format(module_name=module_name)
                for module_name in MODULE_NAMES + LIBRARY_MODULES
            ]
        ),
        version=version,
    )

    bootstrap_script = virtualenv.create_bootstrap_script(bootstrap_text)

    with tempfile.TemporaryDirectory() as venv_dir:
        with tempfile.NamedTemporaryFile('w') as bootstrap_script_file:
            bootstrap_script_file.write(bootstrap_script)

            args = ['python', bootstrap_script_file.name, venv_dir]

            click.echo(subprocess.check_output(args).decode('utf-8'))


cli = click.CommandCollection(sources=[cli], help=CLI_HELP)

if __name__ == '__main__':
    cli()
