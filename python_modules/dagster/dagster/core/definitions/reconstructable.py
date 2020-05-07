import os
from collections import namedtuple

from dagster import check
from dagster.core.errors import DagsterInvariantViolationError
from dagster.serdes import whitelist_for_serdes
from dagster.seven import lru_cache
from dagster.utils import load_yaml_from_path

from .executable import InterProcessExecutablePipeline
from .pointer import (
    CodePointer,
    FileCodePointer,
    ModuleCodePointer,
    get_python_file_from_previous_stack_frame,
)

EPHEMERAL_NAME = '<<unnamed>>'


@whitelist_for_serdes
class ReconstructableRepository(namedtuple('_ReconstructableRepository', 'pointer yaml_path')):
    def __new__(cls, pointer, yaml_path=None):
        return super(ReconstructableRepository, cls).__new__(
            cls,
            pointer=check.inst_param(pointer, 'pointer', CodePointer),
            yaml_path=check.opt_str_param(yaml_path, 'yaml_path'),
        )

    @lru_cache(maxsize=1)
    def get_definition(self):
        return _load_repo(self.pointer)

    def get_reconstructable_pipeline(self, name):
        return ReconstructablePipelineFromRepo(self, name)

    def get_only_reconstructable_pipeline(self):
        name = self.get_definition().get_only_pipeline().name
        return self.get_reconstructable_pipeline(name)

    @classmethod
    def for_file(cls, file, fn_name):
        return cls(FileCodePointer(file, fn_name))

    @classmethod
    def for_module(cls, module, fn_name):
        return cls(ModuleCodePointer(module, fn_name))

    @classmethod
    def from_yaml(cls, file_path):
        check.str_param(file_path, 'file_path')

        config = load_yaml_from_path(file_path)
        repository_config = check.dict_elem(config, 'repository')
        module_name = check.opt_str_elem(repository_config, 'module')
        file_name = check.opt_str_elem(repository_config, 'file')
        fn_name = check.str_elem(repository_config, 'fn')

        if module_name:
            pointer = ModuleCodePointer(module_name, fn_name)
        else:
            # rebase file in config off of the path in the config file
            file_name = os.path.join(os.path.dirname(os.path.abspath(file_path)), file_name)
            pointer = FileCodePointer(file_name, fn_name)

        return cls(pointer=pointer, yaml_path=file_path)


@whitelist_for_serdes
class ReconstructablePipelineFromRepo(
    namedtuple('_ReconstructablePipelineFromRepo', 'repository pipeline_name frozen_solid_subset'),
    InterProcessExecutablePipeline,
):
    def __new__(cls, repository, pipeline_name, frozen_solid_subset=None):
        check.opt_inst_param(frozen_solid_subset, 'frozen_solid_subset', frozenset)
        return super(ReconstructablePipelineFromRepo, cls).__new__(
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
            .subset_for_execution(self.solid_subset)
        )

    def get_reconstructable_repository(self):
        return self.repository

    def subset_for_execution(self, solid_subset):
        pipe = ReconstructablePipelineFromRepo(
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


@whitelist_for_serdes
class ReconstructablePipeline(
    namedtuple('_ReconstructablePipeline', 'pointer frozen_solid_subset'),
    InterProcessExecutablePipeline,
):
    def __new__(cls, pointer, frozen_solid_subset=None):
        check.opt_inst_param(frozen_solid_subset, 'frozen_solid_subset', frozenset)
        return super(ReconstructablePipeline, cls).__new__(
            cls,
            pointer=check.inst_param(pointer, 'pointer', CodePointer),
            frozen_solid_subset=frozen_solid_subset,
        )

    @property
    def solid_subset(self):
        return list(self.frozen_solid_subset) if self.frozen_solid_subset is not None else None

    @lru_cache(maxsize=1)
    def get_definition(self):
        return _load_pipeline(self.pointer).subset_for_execution(self.solid_subset)

    def get_reconstructable_repository(self):
        return ReconstructableRepository(self.pointer)

    def subset_for_execution(self, solid_subset):
        return ReconstructablePipeline(
            self.pointer, frozenset(solid_subset) if solid_subset is not None else None
        )

    def describe(self):
        return self.pointer.describe

    @classmethod
    def for_file(cls, file, fn_name):
        return cls(FileCodePointer(file, fn_name))

    @classmethod
    def for_module(cls, module, fn_name):
        return cls(ModuleCodePointer(module, fn_name))


def reconstructable(fn):
    ''' Create a ReconstructablePipeline from a function that returns a PipelineDefinition '''
    check.callable_param(fn, 'fn')

    return ReconstructablePipeline(
        FileCodePointer(
            python_file=get_python_file_from_previous_stack_frame(), fn_name=fn.__name__,
        )
    )


def _load_pipeline(pointer):
    from .pipeline import PipelineDefinition

    target = pointer.load_target()

    # if its a function invoke it - otherwise we are pointing to a
    # artifact in module scope, likely decorator output
    if callable(target):
        target = target()

    if isinstance(target, PipelineDefinition):
        return target

    raise DagsterInvariantViolationError(
        'CodePointer ({str}) must resolve to a PipelineDefinition. '
        'Received a {type}'.format(str=pointer.describe(), type=type(target))
    )


def _load_repo(pointer):
    from .pipeline import PipelineDefinition
    from .repository import RepositoryDefinition

    target = pointer.load_target()

    # if its a function invoke it - otherwise we are pointing to a
    # artifact in module scope, likely decorator output
    if callable(target):
        target = target()

    # special case - we can wrap a single pipeline in a repository
    if isinstance(target, PipelineDefinition):
        # consider including pipeline name in generated repo name
        repo_def = RepositoryDefinition(name=EPHEMERAL_NAME, pipeline_defs=[target])
    elif isinstance(target, RepositoryDefinition):
        repo_def = target
    else:
        raise DagsterInvariantViolationError(
            'CodePointer ({str}) must resolve to a '
            'RepositoryDefinition or a PipelineDefinition. '
            'Received a {type}'.format(str=pointer.describe(), type=type(target))
        )

    return repo_def
