# pylint: disable=redefined-outer-name
import datetime
import logging
import os
import shutil
import subprocess
import sys
import tempfile

try:
    import airflow.plugins_manager
    import docker
    from airflow.models import TaskInstance
except ImportError:
    pass

import pytest

from dagster import check, seven
from dagster.core.execution import create_execution_plan
from dagster.utils import load_yaml_from_glob_list, mkdir_p, script_relative_path, pushd

try:
    from dagster_airflow import scaffold_airflow_dag
except ImportError:
    pass

from .utils import import_module_from_path


IMAGE = 'airline-demo-airflow'

CIRCLECI = os.getenv('CIRCLECI')

# py2 compat
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

<<<<<<< HEAD
# Spins up a database using docker-compose and tears it down after tests complete.
# We disable this on CircleCI when running the py37 tests -- airflow is not compatible with
# py37; as a consequence, on this build we use the Circle docker executor, rather than the
# machine executor, and spin the database up directly from circleci/postgres:9.6.2-alpine.
@pytest.fixture(scope='session')
def docker_compose_db():
    if sys.version_info.major == 3 and sys.version_info.minor == 7 and CIRCLECI:
        yield
        return
=======
>>>>>>> Cp

# TODO: Figure out a good way to inject run ids here -- the issue is that different pipelines have
# implicit dependencies on each other. Make those explicit! (Probably lose the "download" pipeline/
# collapse it into the ingest pipeline)


@pytest.fixture(scope='module')
def airflow_home():
    '''Check that AIRFLOW_HOME is set, and return it'''
    airflow_home_dir = os.getenv('AIRFLOW_HOME')
    assert airflow_home_dir, 'No AIRFLOW_HOME set -- is airflow installed?'
    airflow_home_dir = os.path.abspath(os.path.expanduser(airflow_home_dir))

    return airflow_home_dir


@pytest.fixture(scope='module')
def docker_client():
    '''Instantiate a Docker Python client.'''
    try:
        client = docker.from_env()
        client.info()
    except docker.errors.APIError:
        check.failed('Couldn\'t find docker at {url} -- is it running?'.format(url=client._url('')))
    return client


@pytest.fixture(scope='module')
def docker_image(docker_client):
    '''Check that the airflow image exists.
    
    This image is created by dagster_airflow_tests/test_project/build.sh -- we might want to move
    image build into a test fixture of its own.
    '''
    try:
        docker_client.images.get(IMAGE)
    except docker.errors.ImageNotFound:
        check.failed(
            'Couldn\'t find docker image {image} required for test: please run the script at '
            '{script_path}'.format(image=IMAGE, script_path=script_relative_path('../build.sh'))
        )

    return IMAGE


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
def host_tmp_dir():
    '''We don't clean this up / make it a context manager because it may already exist...'''
    mkdir_p('/tmp/results')
    yield '/tmp/results'


@pytest.fixture(scope='module')
def airflow_test(docker_image, dags_path, plugins_path, host_tmp_dir):
    '''Install the docker-airflow plugin & reload airflow.operators so the plugin is available.'''
    assert docker_image

    plugin_definition_filename = 'dagster_plugin.py'

    plugin_path = os.path.abspath(os.path.join(plugins_path, plugin_definition_filename))

    temporary_plugin_path = None

    created_init_py = False

    try:
        # If there is already a docker-airflow plugin installed, we set it aside for safekeeping
        if os.path.exists(plugin_path):
            temporary_plugin_file = tempfile.NamedTemporaryFile(delete=False)
            temporary_plugin_file.close()
            temporary_plugin_path = temporary_plugin_file.name
            shutil.copyfile(plugin_path, temporary_plugin_path)

        shutil.copyfile(
            script_relative_path(
                os.path.join(
                    '..', '..', 'dagster-airflow', 'dagster_airflow', plugin_definition_filename
                )
            ),
            plugin_path,
        )

        mkdir_p(os.path.abspath(dags_path))
        sys.path.append(os.path.abspath(dags_path))

        # Set up the DAGs directory if needed
        init_py_path = os.path.join(os.path.abspath(dags_path), '__init__.py')
        if not os.path.exists(init_py_path):
            with open(init_py_path, 'a'):
                pass
            created_init_py = True

        subprocess.check_output(['airflow', 'initdb'])

        # Necromancy; follows airflow.operators.__init__
        # This reloads airflow.operators so that the import statement below is possible
        seven.reload_module(airflow.plugins_manager)
        for operators_module in airflow.plugins_manager.operators_modules:
            sys.modules[operators_module.__name__] = operators_module
            globals()[operators_module._name] = operators_module  # pylint:disable=protected-access

        # Test that we can now actually import the DagsterOperator
        from airflow.operators.dagster_plugin import DagsterOperator  # pylint:disable=import-error

        # Clean up
        del DagsterOperator

        yield (docker_image, dags_path, host_tmp_dir)

    finally:
        if os.path.exists(plugin_path):
            os.remove(plugin_path)

        if temporary_plugin_path is not None:
            shutil.copyfile(temporary_plugin_path, plugin_path)
            os.remove(temporary_plugin_path)

        if created_init_py:
            os.remove(init_py_path)

        sys.path = sys.path[:-1]


@pytest.fixture(scope='class')
def scaffold_dag(request, airflow_test):
    '''Scaffolds an Airflow dag and installs it.'''
    docker_image, dags_path, _ = airflow_test
    pipeline = getattr(request.cls, 'pipeline')
    env_config = load_yaml_from_glob_list(getattr(request.cls, 'config'))

    tempdir = tempfile.gettempdir()

    static_path, editable_path = scaffold_airflow_dag(
        pipeline=pipeline,
        env_config=env_config,
        image=docker_image,
        output_path=tempdir,
        dag_kwargs={'default_args': {'start_date': datetime.datetime(1900, 1, 1)}},
        operator_kwargs={'network_mode': 'container:db'},
    )

    # Ensure that the scaffolded files parse correctly
    subprocess.check_output(['python', editable_path])

    shutil.copyfile(
        static_path, os.path.abspath(os.path.join(dags_path, os.path.basename(static_path)))
    )

    shutil.copyfile(
        editable_path, os.path.abspath(os.path.join(dags_path, os.path.basename(editable_path)))
    )

    os.remove(static_path)
    os.remove(editable_path)

    execution_date = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    pipeline_name = pipeline.name

    execution_plan = create_execution_plan(pipeline, env_config)

    yield (
        pipeline_name,
        execution_plan,
        execution_date,
        os.path.abspath(os.path.join(dags_path, os.path.basename(static_path))),
        os.path.abspath(os.path.join(dags_path, os.path.basename(editable_path))),
    )

    # Clean up the installed DAGs
    os.remove(os.path.abspath(os.path.join(dags_path, os.path.basename(static_path))))
    os.remove(os.path.abspath(os.path.join(dags_path, os.path.basename(editable_path))))

    # Including any bytecode cruft
    try:
        os.remove(
            os.path.abspath(os.path.join(dags_path, os.path.basename(static_path)[:-3] + '.pyc'))
        )
    except (FileNotFoundError, OSError):
        pass

    try:
        os.remove(
            os.path.abspath(os.path.join(dags_path, os.path.basename(editable_path)[:-3] + '.pyc'))
        )
    except (FileNotFoundError, OSError):
        pass


@pytest.fixture(scope='function')
def clean_results_dir():
    subprocess.check_output(['rm', '-rf', '/tmp/results/*'])
    yield '/tmp/results'
    subprocess.check_output(['rm', '-rf', '/tmp/results/*'])


@pytest.fixture(scope='session')
def docker_compose_db():
    if sys.version_info.major == 3 and sys.version_info.minor == 7 and CIRCLECI:
        yield
        return

    with pushd(script_relative_path('../')):
        subprocess.check_output(['docker-compose', 'up', '-d', 'db'])

    yield

    with pushd(script_relative_path('../')):
        subprocess.check_output(['docker-compose', 'stop', 'db'])
        subprocess.check_output(['docker-compose', 'rm', '-f', 'db'])

    return


@pytest.fixture(scope='class')
def in_memory_airflow_run(scaffold_dag, docker_compose_db):
    pipeline_name, _p, _d, static_path, editable_path = scaffold_dag

    execution_date = datetime.datetime.utcnow()

    import_module_from_path(
        '{pipeline_name}_static__scaffold'.format(pipeline_name=pipeline_name), static_path
    )
    demo_pipeline = import_module_from_path('demo_pipeline', editable_path)

    _dag, tasks = demo_pipeline.make_dag(
        dag_id=demo_pipeline.DAG_ID,
        dag_description=demo_pipeline.DAG_DESCRIPTION,
        dag_kwargs=dict(default_args=demo_pipeline.DEFAULT_ARGS, **demo_pipeline.DAG_KWARGS),
        operator_kwargs={
            's3_bucket_name': 'dagster-lambda-execution',
            'network_mode': 'container:db',
        },
    )

    results = []
    # These are in topo order already
    for task in tasks:
        ti = TaskInstance(task=task, execution_date=execution_date)
        context = ti.get_template_context()
        task._log = logging  # pylint: disable=protected-access
        results.append(task.execute(context))

    return results
