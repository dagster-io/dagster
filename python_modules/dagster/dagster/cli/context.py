from collections import namedtuple
import importlib

import click
import yaml

from dagster import (
    check,
    RepositoryDefinition,
)


class RepositoryInfo(namedtuple('_RepositoryInfo', 'repository module fn module_name fn_name')):
    pass


def load_repository_from_file(file_path):
    check.str_param(file_path, 'file_path')
    with open(file_path, 'r') as ff:
        config = yaml.load(ff)
        repository_config = check.dict_elem(config, 'repository')
        module_name = check.str_elem(repository_config, 'module')
        fn_name = check.str_elem(repository_config, 'fn')

        module, fn, repository = load_repository(module_name, fn_name)

        return RepositoryInfo(
            repository=repository,
            module=module,
            fn=fn,
            module_name=module_name,
            fn_name=fn_name,
        )


def load_repository(module_name, fn_name):
    module = importlib.import_module(module_name)
    fn = getattr(module, fn_name)
    check.is_callable(fn)
    repository = check.inst(fn(), RepositoryDefinition)
    return (module, fn, repository)


def reload_repository_info(repository_info):
    check.inst_param(repository_info, 'repository_info', RepositoryInfo)

    module_name, fn_name = repository_info.module_name, repository_info.fn_name

    module = importlib.reload(repository_info.module)
    fn = getattr(module, fn_name)
    check.is_callable(fn)
    repository = check.inst(fn(), RepositoryDefinition)

    return RepositoryInfo(
        repository=repository,
        module=module,
        fn=fn,
        module_name=module_name,
        fn_name=fn_name,
    )


def repository_config_argument(f):
    return click.option(
        '--conf',
        '-c',
        type=click.Path(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
        default='repository.yml',
        help="Path to config file. Defaults to ./pipelines.yml."
    )(f)
