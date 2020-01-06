'''Test fixtures for dagster-airflow.

These make very heavy use of fixture dependency and scope. If you're unfamiliar with pytest
fixtures, read: https://docs.pytest.org/en/latest/fixture.html.
'''
# pylint doesn't understand the way that pytest constructs fixture dependnecies
# pylint: disable=redefined-outer-name, unused-argument
import os
import shutil
import subprocess
import tempfile
import uuid

import docker
import pytest
import six

from dagster import check
from dagster.utils import load_yaml_from_path, mkdir_p, pushd, script_relative_path


@pytest.fixture(scope='session')
def git_repository_root():
    return six.ensure_str(subprocess.check_output(['git', 'rev-parse', '--show-toplevel']).strip())


@pytest.fixture(scope='session')
def test_repo_path(git_repository_root):  # pylint: disable=redefined-outer-name
    return script_relative_path(
        os.path.join(git_repository_root, '.buildkite', 'images', 'docker', 'test_project')
    )


@pytest.fixture(scope='session')
def environments_path(test_repo_path):  # pylint: disable=redefined-outer-name
    return os.path.join(test_repo_path, 'test_pipelines', 'environments')


@pytest.fixture(scope='module')
def airflow_home():
    '''Check that AIRFLOW_HOME is set, and return it'''
    airflow_home_dir = os.getenv('AIRFLOW_HOME')
    assert airflow_home_dir, 'No AIRFLOW_HOME set -- is airflow installed?'
    airflow_home_dir = os.path.abspath(os.path.expanduser(airflow_home_dir))

    return airflow_home_dir


@pytest.fixture(scope='module')
def temp_dir():
    '''Context manager for temporary directories.

    pytest implicitly wraps in try/except.
    '''
    dir_path = os.path.join('/tmp', str(uuid.uuid4()))
    mkdir_p(dir_path)
    yield dir_path
    shutil.rmtree(dir_path)


@pytest.fixture(scope='module')
def clean_airflow_home(airflow_home):
    '''Ensure that the existing contents of AIRFLOW_HOME do not interfere with test.'''

    airflow_dags_path = os.path.join(airflow_home, 'dags')

    # Ensure Airflow DAGs folder exists
    if not os.path.exists(airflow_dags_path):
        os.makedirs(airflow_dags_path)

    tempdir_path = tempfile.mkdtemp()

    # Move existing DAGs aside for test
    dags_files = os.listdir(airflow_dags_path)
    for dag_file in dags_files:
        shutil.move(os.path.join(airflow_dags_path, dag_file), tempdir_path)

    yield

    # Clean up DAGs produced by test
    shutil.rmtree(airflow_dags_path)
    os.makedirs(airflow_dags_path)

    # Move original DAGs back
    file_paths = os.listdir(tempdir_path)
    for file_path in file_paths:
        shutil.move(
            os.path.join(tempdir_path, file_path), os.path.join(airflow_dags_path, file_path)
        )

    shutil.rmtree(tempdir_path)


@pytest.fixture(scope='session')
def docker_client():
    '''Instantiate a Docker Python client.'''
    try:
        client = docker.from_env()
        client.info()
    except docker.errors.APIError:
        # pylint: disable=protected-access
        check.failed('Couldn\'t find docker at {url} -- is it running?'.format(url=client._url('')))
    return client


@pytest.fixture(scope='session')
def dagster_docker_image():
    assert (
        'DAGSTER_DOCKER_IMAGE' in os.environ
    ), 'DAGSTER_DOCKER_IMAGE must be set in your environment for these tests'

    # Will be set in environment by .buildkite/pipeline.py -> tox.ini to:
    # ${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com/dagster-docker-buildkite:${BUILDKITE_BUILD_ID}-${TOX_PY_VERSION}
    return os.environ['DAGSTER_DOCKER_IMAGE']


@pytest.fixture(scope='session')
def build_docker_image(test_repo_path, docker_client, dagster_docker_image):
    with pushd(test_repo_path):
        subprocess.check_output(['./build.sh'], shell=True)

    return dagster_docker_image


@pytest.fixture(scope='session')
def docker_image(docker_client, build_docker_image):
    '''Check that the airflow image exists.'''
    try:
        docker_client.images.get(build_docker_image)
    except docker.errors.ImageNotFound:
        check.failed(
            'Couldn\'t find docker image {image} required for test: please run the script at '
            '{script_path}'.format(
                image=build_docker_image, script_path=script_relative_path('test_project/build.sh')
            )
        )

    return build_docker_image


@pytest.fixture(scope='module')
def dags_path(airflow_home):
    '''Abspath to the magic Airflow DAGs folder.'''
    path = os.path.join(airflow_home, 'dags', '')
    mkdir_p(os.path.abspath(path))
    return path


@pytest.fixture(scope='module')
def plugins_path(airflow_home):
    '''Abspath to the magic Airflow plugins folder.'''
    path = os.path.join(airflow_home, 'plugins', '')
    mkdir_p(os.path.abspath(path))
    return path


@pytest.fixture(scope='module')
def environment_dict(s3_bucket, test_repo_path):
    env_dict = load_yaml_from_path(os.path.join(test_repo_path, 'env.yaml'))
    env_dict['storage'] = {'s3': {'s3_bucket': s3_bucket}}
    yield env_dict


@pytest.fixture(scope='session')
def s3_bucket():
    yield 'dagster-scratch-80542c2'


@pytest.fixture(scope='session')
def gcs_bucket():
    yield 'dagster-scratch-ccdfe1e'
