import os
from collections import namedtuple

import six

from dagster import check, seven
from dagster.core.code_pointer import (
    CodePointer,
    FileCodePointer,
    ModuleCodePointer,
    get_python_file_from_previous_stack_frame,
)
from dagster.core.errors import DagsterInvariantViolationError
from dagster.serdes import pack_value, unpack_value, whitelist_for_serdes
from dagster.seven import lru_cache

from .executable import ExecutablePipeline

EPHEMERAL_NAME = '<<unnamed>>'


@whitelist_for_serdes
class ReconstructableRepository(namedtuple('_ReconstructableRepository', 'pointer yaml_path')):
    def __new__(
        cls, pointer, yaml_path=None,
    ):
        return super(ReconstructableRepository, cls).__new__(
            cls,
            pointer=check.inst_param(pointer, 'pointer', CodePointer),
            yaml_path=check.opt_str_param(yaml_path, 'yaml_path'),
        )

    @lru_cache(maxsize=1)
    def get_definition(self):
        return repository_def_from_pointer(self.pointer)

    def get_reconstructable_pipeline(self, name):
        return ReconstructablePipeline(self, name)

    @classmethod
    def for_file(cls, file, fn_name):
        return cls(FileCodePointer(file, fn_name))

    @classmethod
    def for_module(cls, module, fn_name):
        return cls(ModuleCodePointer(module, fn_name))

    def get_cli_args(self):
        return self.pointer.get_cli_args()

    @classmethod
    def from_legacy_repository_yaml(cls, file_path):
        check.str_param(file_path, 'file_path')
        absolute_file_path = os.path.abspath(os.path.expanduser(file_path))
        return cls(
            pointer=CodePointer.from_legacy_repository_yaml(absolute_file_path),
            yaml_path=absolute_file_path,
        )


@whitelist_for_serdes
class ReconstructablePipeline(
    namedtuple('_ReconstructablePipeline', 'repository pipeline_name frozen_solid_subset'),
    ExecutablePipeline,
):
    def __new__(cls, repository, pipeline_name, frozen_solid_subset=None):
        check.opt_inst_param(frozen_solid_subset, 'frozen_solid_subset', frozenset)
        return super(ReconstructablePipeline, cls).__new__(
            cls,
            repository=check.inst_param(repository, 'repository', ReconstructableRepository),
            pipeline_name=check.str_param(pipeline_name, 'pipeline_name'),
            frozen_solid_subset=frozen_solid_subset,
        )

    @property
    def solid_subset(self):
        return list(self.frozen_solid_subset) if self.frozen_solid_subset is not None else None

    @lru_cache(maxsize=1)
    def get_definition(self):
        return (
            self.repository.get_definition()
            .get_pipeline(self.pipeline_name)
            .get_pipeline_subset_def(self.solid_subset)
        )

    def get_reconstructable_repository(self):
        return self.repository

    def subset_for_execution(self, solid_subset):
        pipe = ReconstructablePipeline(
            self.repository,
            self.pipeline_name,
            frozenset(solid_subset) if solid_subset is not None else None,
        )
        pipe.get_definition()  # verify the subset is correct
        return pipe

    def describe(self):
        return '"{name}" in repository ({repo})'.format(
            repo=self.repository.pointer.describe, name=self.pipeline_name
        )

    @staticmethod
    def for_file(python_file, fn_name):
        return bootstrap_standalone_recon_pipeline(FileCodePointer(python_file, fn_name))

    @staticmethod
    def for_module(module, fn_name):
        return bootstrap_standalone_recon_pipeline(ModuleCodePointer(module, fn_name))

    def to_dict(self):
        return pack_value(self)

    @staticmethod
    def from_dict(val):
        check.dict_param(val, 'val')

        inst = unpack_value(val)
        check.invariant(
            isinstance(inst, ReconstructablePipeline),
            'Deserialized object is not instance of ReconstructablePipeline, got {type}'.format(
                type=type(inst)
            ),
        )
        return inst


def reconstructable(target):
    '''
    Create a ReconstructablePipeline from a function that returns a PipelineDefinition
    or a @pipeline decorated function.
    '''
    from dagster.core.definitions import PipelineDefinition

    if not seven.is_function_or_decorator_instance_of(target, PipelineDefinition):
        raise DagsterInvariantViolationError(
            'Reconstructable target should be a function or definition produced '
            'by a decorated function, got {type}.'.format(type=type(target)),
        )

    if seven.is_lambda(target):
        raise DagsterInvariantViolationError(
            'Reconstructable target can not be a lambda. Use a function or '
            'decorated function defined at module scope instead.'
        )

    if seven.qualname_differs(target):
        raise DagsterInvariantViolationError(
            'Reconstructable target "{target.__name__}" has a different '
            '__qualname__ "{target.__qualname__}" indicating it is not '
            'defined at module scope. Use a function or decorated function '
            'defined at module scope instead.'.format(target=target)
        )

    pointer = FileCodePointer(
        python_file=get_python_file_from_previous_stack_frame(), fn_name=target.__name__,
    )

    return bootstrap_standalone_recon_pipeline(pointer)


def bootstrap_standalone_recon_pipeline(pointer):
    # So this actually straps the the pipeline for the sole
    # purpose of getting the pipeline name. If we changed ReconstructablePipeline
    # to get the pipeline on demand in order to get name, we could avoid this.
    pipeline_def = pipeline_def_from_pointer(pointer)
    return ReconstructablePipeline(
        repository=ReconstructableRepository(pointer),  # creates ephemeral repo
        pipeline_name=pipeline_def.name,
    )


def def_from_pointer(pointer):
    target = pointer.load_target()

    if not callable(target):
        return target

    # if its a function invoke it - otherwise we are pointing to a
    # artifact in module scope, likely decorator output
    try:
        return target()
    except TypeError as t_e:
        six.raise_from(
            DagsterInvariantViolationError(
                'Error invoking function at {target} with no arguments. '
                'Reconstructable target must be callable with no arguments'.format(
                    target=pointer.describe()
                )
            ),
            t_e,
        )


def pipeline_def_from_pointer(pointer):
    from .pipeline import PipelineDefinition

    target = def_from_pointer(pointer)

    if isinstance(target, PipelineDefinition):
        return target

    raise DagsterInvariantViolationError(
        'CodePointer ({str}) must resolve to a PipelineDefinition. '
        'Received a {type}'.format(str=pointer.describe(), type=type(target))
    )


def repository_def_from_pointer(pointer):
    from .pipeline import PipelineDefinition
    from .repository import RepositoryData, RepositoryDefinition

    target = def_from_pointer(pointer)

    # special case - we can wrap a single pipeline in a repository
    if isinstance(target, PipelineDefinition):
        # consider including pipeline name in generated repo name
        repo_def = RepositoryDefinition(
            name=EPHEMERAL_NAME, repository_data=RepositoryData.from_list([target])
        )
    elif isinstance(target, RepositoryDefinition):
        repo_def = target
    else:
        raise DagsterInvariantViolationError(
            'CodePointer ({str}) must resolve to a '
            'RepositoryDefinition or a PipelineDefinition. '
            'Received a {type}'.format(str=pointer.describe(), type=type(target))
        )

    return repo_def
