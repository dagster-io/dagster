from collections import namedtuple
from enum import Enum

import click

from dagster import PipelineDefinition, RepositoryDefinition, RepositoryTargetInfo, check
from dagster.core.definitions import LoaderEntrypoint
from dagster.core.errors import InvalidPipelineLoadingComboError


INFO_FIELDS = set(['repository_yaml', 'pipeline_name', 'python_file', 'fn_name', 'module_name'])

PipelineTargetInfo = namedtuple(
    'PipelineTargetInfo', 'repository_yaml pipeline_name python_file fn_name module_name'
)


class PipelineTargetMode(Enum):
    PIPELINE = 1
    REPOSITORY = 2


RepositoryData = namedtuple('RepositoryData', 'entrypoint pipeline_name')

PipelineLoadingModeData = namedtuple('PipelineLoadingModeData', 'mode data')


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


def create_pipeline_loading_mode_data(pipeline_target_info):
    check.inst_param(pipeline_target_info, 'pipeline_target_info', PipelineTargetInfo)

    if check_info_fields(pipeline_target_info, 'python_file', 'fn_name', 'pipeline_name'):
        return PipelineLoadingModeData(
            mode=PipelineTargetMode.REPOSITORY,
            data=RepositoryData(
                entrypoint=LoaderEntrypoint.from_file_target(
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
                entrypoint=LoaderEntrypoint.from_module_target(
                    module_name=pipeline_target_info.module_name,
                    fn_name=pipeline_target_info.fn_name,
                ),
                pipeline_name=pipeline_target_info.pipeline_name,
            ),
        )
    elif check_info_fields(pipeline_target_info, 'python_file', 'fn_name'):
        return PipelineLoadingModeData(
            mode=PipelineTargetMode.PIPELINE,
            data=LoaderEntrypoint.from_file_target(
                python_file=pipeline_target_info.python_file, fn_name=pipeline_target_info.fn_name
            ),
        )
    elif check_info_fields(pipeline_target_info, 'module_name', 'fn_name'):
        return PipelineLoadingModeData(
            mode=PipelineTargetMode.PIPELINE,
            data=LoaderEntrypoint.from_module_target(
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
                entrypoint=LoaderEntrypoint.from_yaml(pipeline_target_info.repository_yaml),
                pipeline_name=pipeline_target_info.pipeline_name,
            ),
        )
    else:
        raise InvalidPipelineLoadingComboError()


def load_pipeline_from_target_info(pipeline_target_info):
    check.inst_param(pipeline_target_info, 'pipeline_target_info', PipelineTargetInfo)

    mode_data = create_pipeline_loading_mode_data(pipeline_target_info)

    if mode_data.mode == PipelineTargetMode.REPOSITORY:
        repository = check.inst(mode_data.data.entrypoint.perform_load(), RepositoryDefinition)
        return repository.get_pipeline(mode_data.data.pipeline_name)
    elif mode_data.mode == PipelineTargetMode.PIPELINE:
        return check.inst(mode_data.data.perform_load(), PipelineDefinition)
    else:
        check.failed('Should never reach')


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
