from collections import namedtuple
from enum import Enum
import imp
import importlib
import os

import click

from dagster import (
    PipelineDefinition,
    RepositoryDefinition,
    check,
)

from dagster.utils import load_yaml_from_path

INFO_FIELDS = set([
    'repository_yaml',
    'pipeline_name',
    'python_file',
    'fn_name',
    'module_name',
])

PipelineTargetInfo = namedtuple(
    'PipelineTargetInfo',
    'repository_yaml pipeline_name python_file fn_name module_name',
)


class RepositoryTargetMode(Enum):
    YAML_FILE = 0
    MODULE = 1
    FILE = 2


RepositoryTargetInfo = namedtuple(
    'RepositoryTargetInfo',
    'repository_yaml module_name python_file fn_name',
)


class PipelineTargetMode(Enum):
    PIPELINE_PYTHON_FILE = 0
    PIPELINE_MODULE = 1
    REPOSITORY_PYTHON_FILE = 2
    REPOSITORY_MODULE = 3
    REPOSITORY_YAML_FILE = 4


FileTargetFunction = namedtuple('FileTargetFunction', 'python_file fn_name')
ModuleTargetFunction = namedtuple('ModuleTargetFunction', 'module_name fn_name')

RepositoryPythonFileData = namedtuple(
    'RepositoryPythonFileData',
    'file_target_function pipeline_name',
)

RepositoryModuleData = namedtuple(
    'RepositoryModuleData',
    'module_target_function pipeline_name',
)

RepositoryYamlData = namedtuple(
    'RepositoryYamlData',
    'repository_yaml pipeline_name',
)

PipelineLoadingModeData = namedtuple('PipelineLoadingModeData', 'mode data')

RepositoryLoadingModeData = namedtuple('RepositoryLoadingModeData', 'mode data')


class InvalidPipelineLoadingComboError(Exception):
    pass


class InvalidRepositoryLoadingComboError(Exception):
    pass


def check_info_fields(info, *fields):
    check.inst_param(info, 'info', PipelineTargetInfo)
    check.tuple_param(fields, 'fields')

    info_dict = info._asdict()
    for field in fields:
        if info_dict[field] is None:
            return False

    for none_field in INFO_FIELDS.difference(set(fields)):
        if info_dict[none_field] is not None:
            raise InvalidPipelineLoadingComboError(
                (
                    'field: {none_field} with value {value} should not be set if'
                    '{fields} were provided'
                ).format(
                    value=repr(info_dict[none_field]),
                    none_field=none_field,
                    fields=repr(fields),
                )
            )

    return True


def repo_load_invariant(condition):
    if not condition:
        raise InvalidRepositoryLoadingComboError()


def create_repository_loading_mode_data(info):
    check.inst_param(info, 'info', RepositoryTargetInfo)

    if info.repository_yaml:
        repo_load_invariant(info.module_name is None)
        repo_load_invariant(info.python_file is None)
        repo_load_invariant(info.fn_name is None)
        return RepositoryLoadingModeData(
            mode=RepositoryTargetMode.YAML_FILE,
            data=info.repository_yaml,
        )
    elif info.module_name and info.fn_name:
        repo_load_invariant(info.repository_yaml is None)
        repo_load_invariant(info.python_file is None)
        return RepositoryLoadingModeData(
            mode=RepositoryTargetMode.MODULE,
            data=ModuleTargetFunction(
                module_name=info.module_name,
                fn_name=info.fn_name,
            )
        )
    elif info.python_file and info.fn_name:
        repo_load_invariant(info.repository_yaml is None)
        repo_load_invariant(info.module_name is None)
        return RepositoryLoadingModeData(
            mode=RepositoryTargetMode.FILE,
            data=FileTargetFunction(
                python_file=info.python_file,
                fn_name=info.fn_name,
            )
        )
    else:
        raise InvalidRepositoryLoadingComboError()


def create_pipeline_loading_mode_data(info):
    check.inst_param(info, 'info', PipelineTargetInfo)

    if check_info_fields(info, 'python_file', 'fn_name', 'pipeline_name'):
        return PipelineLoadingModeData(
            mode=PipelineTargetMode.REPOSITORY_PYTHON_FILE,
            data=RepositoryPythonFileData(
                file_target_function=FileTargetFunction(
                    python_file=info.python_file,
                    fn_name=info.fn_name,
                ),
                pipeline_name=info.pipeline_name,
            )
        )
    elif check_info_fields(info, 'module_name', 'fn_name', 'pipeline_name'):
        return PipelineLoadingModeData(
            mode=PipelineTargetMode.REPOSITORY_MODULE,
            data=RepositoryModuleData(
                module_target_function=ModuleTargetFunction(
                    module_name=info.module_name,
                    fn_name=info.fn_name,
                ),
                pipeline_name=info.pipeline_name,
            )
        )
    elif check_info_fields(info, 'python_file', 'fn_name'):
        return PipelineLoadingModeData(
            mode=PipelineTargetMode.PIPELINE_PYTHON_FILE,
            data=FileTargetFunction(
                python_file=info.python_file,
                fn_name=info.fn_name,
            )
        )
    elif check_info_fields(info, 'module_name', 'fn_name'):
        return PipelineLoadingModeData(
            mode=PipelineTargetMode.PIPELINE_MODULE,
            data=ModuleTargetFunction(
                module_name=info.module_name,
                fn_name=info.fn_name,
            )
        )
    elif info.pipeline_name:
        for none_field in ['python_file', 'fn_name', 'module_name']:
            if getattr(info, none_field) is not None:
                raise InvalidPipelineLoadingComboError(
                    '{none_field} is not None. Got {value}'.format(
                        none_field=none_field,
                        value=getattr(info, none_field),
                    )
                )

        check.invariant(info.repository_yaml is not None)

        return PipelineLoadingModeData(
            mode=PipelineTargetMode.REPOSITORY_YAML_FILE,
            data=RepositoryYamlData(
                repository_yaml=info.repository_yaml,
                pipeline_name=info.pipeline_name,
            )
        )
    else:
        raise InvalidPipelineLoadingComboError()


DynamicObject = namedtuple('DynamicObject', 'module fn module_name fn_name object')


def load_file_target_function(file_target_function):
    check.inst_param(file_target_function, 'file_target_function', FileTargetFunction)
    module_name = os.path.splitext(os.path.basename(file_target_function.python_file))[0]
    module = imp.load_source(module_name, file_target_function.python_file)
    fn = getattr(module, file_target_function.fn_name)
    check.is_callable(fn)
    return DynamicObject(module, fn, module_name, file_target_function.fn_name, object=fn())


def load_module_target_function(module_target_function):
    check.inst_param(module_target_function, 'module_target_function', ModuleTargetFunction)
    module = importlib.import_module(module_target_function.module_name)
    fn = getattr(module, module_target_function.fn_name)
    check.is_callable(fn)
    return DynamicObject(
        module, fn, module_target_function.module_name, module_target_function.fn_name, object=fn()
    )


EMPHERMAL_NAME = '<<unnamed>>'


def load_repository_object_from_target_info(info):
    check.inst_param(info, 'info', RepositoryTargetInfo)

    mode_data = create_repository_loading_mode_data(info)

    if mode_data.mode == RepositoryTargetMode.YAML_FILE:
        return load_repository_from_file(mode_data.data)
    elif mode_data.mode == RepositoryTargetMode.MODULE:
        dynamic_obj = load_module_target_function(mode_data.data)
        return ensure_in_repo(dynamic_obj)
    elif mode_data.mode == RepositoryTargetMode.FILE:
        dynamic_obj = load_file_target_function(mode_data.data)
        return ensure_in_repo(dynamic_obj)
    else:
        check.failed('should not reach')


def ensure_in_repo(dynamic_obj):
    if isinstance(dynamic_obj.object, RepositoryDefinition):
        return dynamic_obj

    pipeline = dynamic_obj.object
    repo_fn = lambda: RepositoryDefinition(
        name=EMPHERMAL_NAME,
        pipeline_dict={pipeline.name: lambda: pipeline},
    )
    return DynamicObject(
        module=dynamic_obj.module,
        fn=repo_fn,
        module_name=dynamic_obj.module_name,
        fn_name=dynamic_obj.fn_name,
        object=repo_fn(),
    )


def load_repository_from_target_info(info):
    return check.inst(load_repository_object_from_target_info(info).fn(), RepositoryDefinition)


# Keeping this code around for a week. I might need to be able to
# coerce a single pipeline repo into a pipeline at some point while
# we work out the kinks in the command line tool.
#
# If this is still around in a week or two delete this -- schrockn (09/18/18)

# def _pipeline_from_dynamic_object(mode_data, dynamic_object):
#     check.inst_param(mode_data, 'mode_data', PipelineLoadingModeData)
#     check.inst_param(dynamic_object, 'dynamic_object', DynamicObject)

#     repository = check.inst(
#         ensure_in_repo(dynamic_object).object,
#         RepositoryDefinition,
#     )
#     if len(repository.pipeline_dict) == 1:
#         return repository.get_all_pipelines()[0]

#     return repository.get_pipeline(mode_data.data.pipeline_name)


def load_pipeline_from_target_info(info):
    check.inst_param(info, 'info', PipelineTargetInfo)

    mode_data = create_pipeline_loading_mode_data(info)

    if mode_data.mode == PipelineTargetMode.REPOSITORY_PYTHON_FILE:
        repository = check.inst(
            load_file_target_function(mode_data.data.file_target_function).object,
            RepositoryDefinition,
        )
        return repository.get_pipeline(mode_data.data.pipeline_name)
        # dynamic_object = load_file_target_function(mode_data.data.file_target_function)
        # return _pipeline_from_dynamic_object(mode_data, dynamic_object)
        # If this is still around in a week or two delete this -- schrockn (09/18/18)
    elif mode_data.mode == PipelineTargetMode.REPOSITORY_MODULE:
        repository = check.inst(
            load_module_target_function(mode_data.data.module_target_function).object,
            RepositoryDefinition,
        )
        return repository.get_pipeline(mode_data.data.pipeline_name)
        # dynamic_object = load_module_target_function(mode_data.data.module_target_function)
        # return _pipeline_from_dynamic_object(mode_data, dynamic_object)
        # If this is still around in a week or two delete this -- schrockn (09/18/18)
    elif mode_data.mode == PipelineTargetMode.PIPELINE_PYTHON_FILE:
        return check.inst(
            load_file_target_function(mode_data.data).object,
            PipelineDefinition,
        )
    elif mode_data.mode == PipelineTargetMode.PIPELINE_MODULE:
        return check.inst(
            load_module_target_function(mode_data.data).object,
            PipelineDefinition,
        )
    elif mode_data.mode == PipelineTargetMode.REPOSITORY_YAML_FILE:
        repository = check.inst(
            load_repository_from_file(mode_data.data.repository_yaml).object,
            RepositoryDefinition,
        )
        return repository.get_pipeline(mode_data.data.pipeline_name)
    else:
        check.failed('Should never reach')


def load_repository_from_file(file_path):
    check.str_param(file_path, 'file_path')

    config = load_yaml_from_path(file_path)
    repository_config = check.dict_elem(config, 'repository')
    module_name = check.opt_str_elem(repository_config, 'module')
    file_name = check.opt_str_elem(repository_config, 'file')
    fn_name = check.str_elem(repository_config, 'fn')

    if module_name:
        return load_module_target_function(ModuleTargetFunction(module_name, fn_name))
    else:
        # rebase file in config off of the path in the config file
        file_name = os.path.join(os.path.dirname(os.path.abspath(file_path)), file_name)
        return load_file_target_function(FileTargetFunction(file_name, fn_name))


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
            )
        ),
        click.option(
            '--python-file',
            '-f',
            help='Specify python file where repository or pipeline function lives.'
        ),
        click.option(
            '--module-name',
            '-m',
            help='Specify module where repository or pipeline function lives'
        ),
        click.option('--fn-name', '-n', help='Function that returns either repository or pipeline'),
    )


def pipeline_target_command(f):
    # f = repository_config_argument(f)
    # nargs=-1 is used right now to make this argument optional
    # it can only handle 0 or 1 pipeline names
    # see create_pipeline_from_cli_args
    return apply_click_params(
        f,
        click.option(
            '--repository-yaml',
            '-y',
            type=click.STRING,
            help=(
                'Path to config file. Defaults to ./repository.yml. if --python-file '
                'and --module-name are not specified'
            )
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


def reload_dynamic_object(dynamic_obj):
    check.inst_param(dynamic_obj, 'dynamic_obj', DynamicObject)

    module_name, fn_name = dynamic_obj.module_name, dynamic_obj.fn_name

    module = importlib.reload(dynamic_obj.module)
    fn = getattr(module, fn_name)
    check.is_callable(fn)

    return DynamicObject(
        object=fn(),
        module=module,
        fn=fn,
        module_name=module_name,
        fn_name=fn_name,
    )


def reload_pipeline_or_repo(dynamic_obj):
    return ensure_in_repo(reload_dynamic_object(dynamic_obj))