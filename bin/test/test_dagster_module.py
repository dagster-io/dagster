import os

from automation.git import git_repo_root

from ..dagster_module import DagsterModule, construct_publish_comands


def test_dagster_module(dagster_modules):
    dagster, dagster_k8s = dagster_modules
    git_root = git_repo_root()

    assert dagster.module_path == os.path.abspath(
        os.path.join(git_root, 'python_modules', 'dagster')
    )
    assert dagster_k8s.module_path == os.path.abspath(
        os.path.join(git_root, 'python_modules', 'libraries', 'dagster-k8s')
    )

    assert dagster.version_file_path == os.path.abspath(
        os.path.join(git_root, 'python_modules', 'dagster', 'dagster', 'version.py')
    )
    assert dagster_k8s.version_file_path == os.path.abspath(
        os.path.join(
            git_root, 'python_modules', 'libraries', 'dagster-k8s', 'dagster_k8s', 'version.py'
        )
    )


def test_normalized_module_name(dagster_modules):
    dagster, dagster_k8s = dagster_modules
    git_root = git_repo_root()

    assert dagster.normalized_module_name == 'dagster'
    assert dagster_k8s.normalized_module_name == 'dagster_k8s'

    with dagster.pushd_module():
        assert os.getcwd() == os.path.join(git_root, 'python_modules', 'dagster')

    with dagster_k8s.pushd_module():
        assert os.getcwd() == os.path.join(git_root, 'python_modules', 'libraries', 'dagster-k8s')


def test_find_cruft(dagster_modules):
    dagster, dagster_k8s = dagster_modules
    git_root = git_repo_root()

    dagster_foobar = os.path.join(git_root, 'python_modules', 'dagster', 'foobar.egg-info')
    open(dagster_foobar, 'a').close()
    assert dagster_foobar in dagster.find_cruft()
    os.unlink(dagster_foobar)

    dagster_k8s_foobar = os.path.join(
        git_root, 'python_modules', 'libraries', 'dagster-k8s', 'foobar.egg-info'
    )
    open(dagster_k8s_foobar, 'a').close()
    assert dagster_k8s_foobar in dagster_k8s.find_cruft()
    os.unlink(dagster_k8s_foobar)


def test_get_version_info(dagster_modules):
    dagster, dagster_k8s = dagster_modules

    dagster_version = dagster.get_version_info()
    assert set(dagster_version.keys()) == {'__nightly__', '__version__'}

    dagster_k8s_version = dagster_k8s.get_version_info()
    assert set(dagster_k8s_version.keys()) == {'__nightly__', '__version__'}


def test_set_version_info(dagster_modules):
    dagster, dagster_k8s = dagster_modules

    assert dagster.set_version_info('foo', '2020.01.01', dry_run=True) == {
        '__nightly__': '2020.01.01',
        '__version__': 'foo',
    }

    assert dagster_k8s.set_version_info('foo', '2020.01.01', dry_run=True) == {
        '__nightly__': '2020.01.01',
        '__version__': 'foo',
    }


def test_should_publish(dagster_modules):
    dagster, dagster_k8s = dagster_modules
    lakehouse = DagsterModule('lakehouse', is_library=True)

    assert dagster.should_publish
    assert dagster_k8s.should_publish
    assert not lakehouse.should_publish


def test_construct_publish_comands():
    pub = construct_publish_comands()
    assert pub == ['python setup.py sdist bdist_wheel', 'twine upload --verbose dist/*']

    pub2 = construct_publish_comands(additional_steps=['foo'], nightly=True)
    assert pub2 == [
        'foo',
        'python setup.py sdist bdist_wheel --nightly',
        'twine upload --verbose dist/*',
    ]
