from collections import namedtuple
from enum import Enum
import imp
import importlib
import os
import sys

import click

from dagster import PipelineDefinition, RepositoryDefinition, check

from dagster.utils import load_yaml_from_path


class RepositoryContainer(object):
    '''
    This class solely exists to implement reloading semantics. We need to have a single object
    that the graphql server has access that stays the same object between reload. This container
    object allows the RepositoryInfo to be written in an immutable fashion.
    '''

    def __init__(self, repository_target_info=None, repository=None):
        self.repo_error = None
        if repository_target_info is not None:
            self.repository_target_info = repository_target_info
            try:
                self.repo = check.inst(
                    load_repository_from_target_info(repository_target_info), RepositoryDefinition
                )
            except:  # pylint: disable=W0702
                self.repo_error = sys.exc_info()
        elif repository is not None:
            self.repository_target_info = None
            self.repo = repository

    @property
    def repository(self):
        return self.repo

    @property
    def error(self):
        return self.repo_error

    @property
    def repository_info(self):
        return self.repository_target_info


INFO_FIELDS = set(['repository_yaml', 'pipeline_name', 'python_file', 'fn_name', 'module_name'])

PipelineTargetInfo = namedtuple(
    'PipelineTargetInfo', 'repository_yaml pipeline_name python_file fn_name module_name'
)


RepositoryTargetInfo = namedtuple(
    'RepositoryTargetInfo', 'repository_yaml module_name python_file fn_name'
)


class PipelineTargetMode(Enum):
    PIPELINE = 1
    REPOSITORY = 2


RepositoryData = namedtuple('RepositoryData', 'entrypoint pipeline_name')

PipelineLoadingModeData = namedtuple('PipelineLoadingModeData', 'mode data')


class InvalidPipelineLoadingComboError(Exception):
    pass


class InvalidRepositoryLoadingComboError(Exception):
    pass


def check_info_fields(pipeline_target_info, *fields):
    check.inst_param(pipeline_target_info, 'pipeline_target_info', PipelineTargetInfo)
    check.tuple_param(fields, 'fields')

    pipeline_target_dict = pipeline_target_info._asdict()
    for field in fields:
        if pipeline_target_dict[field] is None:
            return False

    for none_field in INFO_FIELDS.difference(set(fields)):
        if pipeline_target_dict[none_field] is not None:
            raise InvalidPipelineLoadingComboError(
                (
                    'field: {none_field} with value {value} should not be set if'
                    '{fields} were provided'
                ).format(
                    value=repr(pipeline_target_dict[none_field]),
                    none_field=none_field,
                    fields=repr(fields),
                )
            )

    return True


def repo_load_invariant(condition):
    if not condition:
        raise InvalidRepositoryLoadingComboError()


def entrypoint_from_repo_target_info(repo_target_info):
    check.inst_param(repo_target_info, 'repo_target_info', RepositoryTargetInfo)

    if repo_target_info.repository_yaml:
        repo_load_invariant(repo_target_info.module_name is None)
        repo_load_invariant(repo_target_info.python_file is None)
        repo_load_invariant(repo_target_info.fn_name is None)
        return entrypoint_from_yaml(repo_target_info.repository_yaml)
    elif repo_target_info.module_name and repo_target_info.fn_name:
        repo_load_invariant(repo_target_info.repository_yaml is None)
        repo_load_invariant(repo_target_info.python_file is None)
        return entrypoint_from_module_target(
            module_name=repo_target_info.module_name, fn_name=repo_target_info.fn_name
        )
    elif repo_target_info.python_file and repo_target_info.fn_name:
        repo_load_invariant(repo_target_info.repository_yaml is None)
        repo_load_invariant(repo_target_info.module_name is None)
        return entrypoint_from_file_target(
            python_file=repo_target_info.python_file, fn_name=repo_target_info.fn_name
        )
    else:
        raise InvalidRepositoryLoadingComboError()


def create_pipeline_loading_mode_data(pipeline_target_info):
    check.inst_param(pipeline_target_info, 'pipeline_target_info', PipelineTargetInfo)

    if check_info_fields(pipeline_target_info, 'python_file', 'fn_name', 'pipeline_name'):
        return PipelineLoadingModeData(
            mode=PipelineTargetMode.REPOSITORY,
            data=RepositoryData(
                entrypoint=entrypoint_from_file_target(
                    python_file=pipeline_target_info.python_file,
                    fn_name=pipeline_target_info.fn_name,
                ),
                pipeline_name=pipeline_target_info.pipeline_name,
            ),
        )
    elif check_info_fields(pipeline_target_info, 'module_name', 'fn_name', 'pipeline_name'):
        return PipelineLoadingModeData(
            mode=PipelineTargetMode.REPOSITORY,
            data=RepositoryData(
                entrypoint=entrypoint_from_module_target(
                    module_name=pipeline_target_info.module_name,
                    fn_name=pipeline_target_info.fn_name,
                ),
                pipeline_name=pipeline_target_info.pipeline_name,
            ),
        )
    elif check_info_fields(pipeline_target_info, 'python_file', 'fn_name'):
        return PipelineLoadingModeData(
            mode=PipelineTargetMode.PIPELINE,
            data=entrypoint_from_file_target(
                python_file=pipeline_target_info.python_file, fn_name=pipeline_target_info.fn_name
            ),
        )
    elif check_info_fields(pipeline_target_info, 'module_name', 'fn_name'):
        return PipelineLoadingModeData(
            mode=PipelineTargetMode.PIPELINE,
            data=entrypoint_from_module_target(
                module_name=pipeline_target_info.module_name, fn_name=pipeline_target_info.fn_name
            ),
        )
    elif pipeline_target_info.pipeline_name:
        for none_field in ['python_file', 'fn_name', 'module_name']:
            if getattr(pipeline_target_info, none_field) is not None:
                raise InvalidPipelineLoadingComboError(
                    '{none_field} is not None. Got {value}'.format(
                        none_field=none_field, value=getattr(pipeline_target_info, none_field)
                    )
                )

        check.invariant(pipeline_target_info.repository_yaml is not None)

        return PipelineLoadingModeData(
            mode=PipelineTargetMode.REPOSITORY,
            data=RepositoryData(
                entrypoint=entrypoint_from_yaml(pipeline_target_info.repository_yaml),
                pipeline_name=pipeline_target_info.pipeline_name,
            ),
        )
    else:
        raise InvalidPipelineLoadingComboError()


LoaderEntrypoint = namedtuple('LoaderEntrypoint', 'module module_name fn_name kwargs')


def perform_load(entry):
    fn = getattr(entry.module, entry.fn_name)
    check.is_callable(fn)
    return fn(**entry.kwargs)


def entrypoint_from_file_target(python_file, fn_name, kwargs=None):
    kwargs = check.opt_dict_param(kwargs, 'kwargs')
    module_name = os.path.splitext(os.path.basename(python_file))[0]
    module = imp.load_source(module_name, python_file)
    return LoaderEntrypoint(module, module_name, fn_name, kwargs)


def entrypoint_from_module_target(module_name, fn_name, kwargs=None):
    kwargs = check.opt_dict_param(kwargs, 'kwargs')
    module = importlib.import_module(module_name)
    return LoaderEntrypoint(module, module_name, fn_name, kwargs)


EMPHERMAL_NAME = '<<unnamed>>'


def load_repository_from_target_info(repo_target_info):
    check.inst_param(repo_target_info, 'repo_target_info', RepositoryTargetInfo)
    entrypoint = entrypoint_from_repo_target_info(repo_target_info)
    obj = perform_load(entrypoint)

    if isinstance(obj, RepositoryDefinition):
        return obj
    elif isinstance(obj, PipelineDefinition):
        return RepositoryDefinition(name=EMPHERMAL_NAME, pipeline_dict={obj.name: lambda: obj})
    else:
        raise InvalidPipelineLoadingComboError('entry point must return a repository or pipeline')


def load_pipeline_from_target_info(pipeline_target_info):
    check.inst_param(pipeline_target_info, 'pipeline_target_info', PipelineTargetInfo)

    mode_data = create_pipeline_loading_mode_data(pipeline_target_info)

    if mode_data.mode == PipelineTargetMode.REPOSITORY:
        repository = check.inst(perform_load(mode_data.data.entrypoint), RepositoryDefinition)
        return repository.get_pipeline(mode_data.data.pipeline_name)
    elif mode_data.mode == PipelineTargetMode.PIPELINE:
        return check.inst(perform_load(mode_data.data), PipelineDefinition)
    else:
        check.failed('Should never reach')


def entrypoint_from_yaml(file_path):
    check.str_param(file_path, 'file_path')

    config = load_yaml_from_path(file_path)
    repository_config = check.dict_elem(config, 'repository')
    module_name = check.opt_str_elem(repository_config, 'module')
    file_name = check.opt_str_elem(repository_config, 'file')
    fn_name = check.str_elem(repository_config, 'fn')
    kwargs = check.opt_dict_elem(repository_config, 'kwargs')

    if module_name:
        return entrypoint_from_module_target(module_name, fn_name, kwargs)
    else:
        # rebase file in config off of the path in the config file
        file_name = os.path.join(os.path.dirname(os.path.abspath(file_path)), file_name)
        return entrypoint_from_file_target(file_name, fn_name, kwargs)


def apply_click_params(command, *click_params):
    for click_param in click_params:
        command = click_param(command)
    return command


def repository_target_argument(f):
    return apply_click_params(
        f,
        click.option(
            '--repository-yaml',
            '-y',
            type=click.STRING,
            help=(
                'Path to config file. Defaults to ./repository.yml. if --python-file '
                'and --module-name are not specified'
            ),
        ),
        click.option(
            '--python-file',
            '-f',
            help='Specify python file where repository or pipeline function lives.',
        ),
        click.option(
            '--module-name', '-m', help='Specify module where repository or pipeline function lives'
        ),
        click.option('--fn-name', '-n', help='Function that returns either repository or pipeline'),
    )


def pipeline_target_command(f):
    # f = repository_config_argument(f)
    # nargs=-1 is used right now to make this argument optional
    # it can only handle 0 or 1 pipeline names
    # see .pipeline.create_pipeline_from_cli_args
    return apply_click_params(
        f,
        click.option(
            '--repository-yaml',
            '-y',
            type=click.STRING,
            help=(
                'Path to config file. Defaults to ./repository.yml. if --python-file '
                'and --module-name are not specified'
            ),
        ),
        click.argument('pipeline_name', nargs=-1),
        click.option('--python-file', '-f'),
        click.option('--module-name', '-m'),
        click.option('--fn-name', '-n'),
    )


def all_none(kwargs):
    for value in kwargs.values():
        if value is not None:
            return False
    return True


def load_target_info_from_cli_args(cli_args):
    check.dict_param(cli_args, 'cli_args')

    if all_none(cli_args):
        cli_args['repository_yaml'] = 'repository.yml'

    return RepositoryTargetInfo(**cli_args)
