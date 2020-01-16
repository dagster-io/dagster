import os
import subprocess
import uuid

import click
from celery.utils.nodenames import default_nodename, host_format

from dagster import check
from dagster.config.validate import validate_config
from dagster.core.instance import DagsterInstance
from dagster.utils import load_yaml_from_path, mkdir_p
from dagster.utils.indenting_printer import IndentingPrinter

from .config import CeleryConfig
from .executor import celery_executor
from .tasks import make_app


def create_worker_cli_group():
    group = click.Group(name='worker')
    group.add_command(worker_start_command)
    group.add_command(worker_terminate_command)
    group.add_command(worker_list_command)
    return group


def get_config_value_from_yaml(yaml_path):
    if yaml_path is None:
        return {}
    parsed_yaml = load_yaml_from_path(yaml_path) or {}
    # Would be better not to hardcode this path
    return parsed_yaml.get('execution', {}).get('celery', {}) or {}


def get_app(config_yaml=None):
    if config_yaml:
        celery_config = CeleryConfig(**get_config_value_from_yaml(config_yaml))
    else:
        celery_config = CeleryConfig()

    app = make_app(celery_config)

    return app


def get_worker_name(name=None):
    return (
        name + '@%h'
        if name is not None
        else 'dagster-{uniq}@%h'.format(uniq=str(uuid.uuid4())[-6:])
    )


def get_config_dir(config_yaml=None):
    instance = DagsterInstance.get()
    config_type = celery_executor.config_field.config_type
    config_value = get_config_value_from_yaml(config_yaml)

    config_module_name = 'dagster_celery_config'

    config_dir = os.path.join(
        instance.root_directory, 'dagster_celery', 'config', str(uuid.uuid4())
    )
    mkdir_p(config_dir)
    config_path = os.path.join(
        config_dir, '{config_module_name}.py'.format(config_module_name=config_module_name)
    )
    validated_config = validate_config(config_type, config_value).value
    with open(config_path, 'w') as fd:
        printer = IndentingPrinter(printer=fd.write)
        if 'broker' in validated_config:
            printer.line(
                'broker_url = \'{broker_url}\''.format(broker_url=str(validated_config['broker']))
            )
        if 'backend' in validated_config:
            printer.line(
                'result_backend = \'{result_backend}\''.format(
                    result_backend=str(validated_config['backend'])
                )
            )
        if 'config_source' in validated_config:
            for key, value in validated_config['config_source'].items():
                printer.line('{key} = {value}'.format(key=key, value=repr(value)))
    # n.b. right now we don't attempt to clean up this cache, but it might make sense to delete
    # any files older than some time if there are more than some number of files present, etc.
    return config_dir


def launch_background_worker(subprocess_args, env):
    return subprocess.Popen(
        subprocess_args + ['--detach', '--pidfile='], stdout=None, stderr=None, env=env
    )


@click.command(name='start')
@click.option('--name', '-n', type=click.STRING, default=None)
@click.option('--config-yaml', '-y', type=click.Path(exists=True), default=None)
@click.option('--queue', '-q', type=click.STRING, multiple=True)
@click.option('--background', '-d', is_flag=True)
@click.option('--includes', '-i', type=click.STRING, multiple=True)
@click.option('--loglevel', '-l', type=click.STRING, default='INFO')
def worker_start_command(
    name=None, config_yaml=None, background=None, queue=None, includes=None, loglevel=None,
):
    '''dagster-celery start'''

    loglevel_args = ['--loglevel', loglevel]

    if len(queue) > 4:
        check.failed(
            'Can\'t start a dagster_celery worker that listens on more than four queues, due to a '
            'bug in Celery 4.'
        )
    queue_args = []
    for q in queue:
        queue_args += ['-Q', q]

    includes_args = ['-I', ','.join(includes)] if includes else []

    pythonpath = get_config_dir(config_yaml)
    subprocess_args = (
        ['celery', '-A', 'dagster_celery.tasks', 'worker', '--prefetch-multiplier=1']
        + loglevel_args
        + queue_args
        + includes_args
        + ['-n', get_worker_name(name)]
    )

    env = os.environ.copy()
    if pythonpath is not None:
        env['PYTHONPATH'] = '{existing_pythonpath}{pythonpath}:'.format(
            existing_pythonpath=env.get('PYTHONPATH', ''), pythonpath=pythonpath
        )

    if background:
        launch_background_worker(subprocess_args, env=env)
    else:
        return subprocess.check_call(subprocess_args, env=env)


@click.command(name='list')
@click.option('--config-yaml', '-y', type=click.Path(exists=True), default=None)
def worker_list_command(config_yaml=None):
    app = get_app(config_yaml)

    print(app.control.inspect(timeout=1).active())


@click.command(name='terminate')
@click.argument('name', default='dagster')
@click.option('--all', '-a', 'all_', is_flag=True)
@click.option('--config-yaml', '-y', type=click.Path(exists=True), default=None)
def worker_terminate_command(name='dagster', config_yaml=None, all_=False):
    app = get_app(config_yaml)

    if all_:
        app.control.broadcast('shutdown')
    else:
        app.control.broadcast(
            'shutdown', destination=[host_format(default_nodename(get_worker_name(name)))]
        )


worker_cli = create_worker_cli_group()


@click.group(commands={'worker': worker_cli})
def main():
    '''dagster-celery'''


if __name__ == '__main__':
    # pylint doesn't understand click
    main()  # pylint:disable=no-value-for-parameter
