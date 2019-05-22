import inspect
import os
import sys

from collections import namedtuple
from enum import Enum

import six

from dagster import check
from dagster.core.errors import InvalidPipelineLoadingComboError, InvalidRepositoryLoadingComboError
from dagster.utils import all_none

from .entrypoint import LoaderEntrypoint

EPHEMERAL_NAME = '<<unnamed>>'


class ExecutionTargetHandle:
    '''ExecutionTargetHandle represents an immutable, serializable reference to a Dagster
    RepositoryDefinition or PipelineDefinition, to support dynamically loading these in various
    contexts (e.g. across process boundaries).

    This class must remain pickle-serializable to ensure multiprocessing compatibility, and is the
    one of the primary reasons that we pass this around vs. an instantiated
    RepositoryDefinition/PipelineDefinition object.

    ### Creation
    ExecutionTargetHandles can be created via the staticmethod constructors below.

        - for_repo_fn
        - for_repo_yaml
        - for_repo_python_file
        - for_repo_module
        - for_pipeline_fn
        - for_pipeline_python_file
        - for_pipeline_module

    Also, the following constructors are provided to support construction from CLI tools:

        - for_repo_cli_args
        - for_pipeline_cli_args

    Since an ExecutionTargetHandle can reference either a RepositoryDefinition or a fully-qualified
    pipeline, it provides a property `is_resolved_to_pipeline` which identifies whether it is fully-
    qualified to a pipeline reference.

    For repository-based handles, you can use the `with_pipeline_name(pipeline_name)` method on a
    repository handle to construct and return a new fully-qualified pipeline handle.

    ### Usage
    Handle objects support the following methods to construct `*Definition` objects:

        - handle.build_repository_definition() => RepositoryDefinition
        - handle.build_pipeline_definition() => PipelineDefinition

    These are intended to support reconstructing definitions from their serialized representations
    provided by this object wherever needed during execution.

    The first is supported on all handles; the second requires a fully-qualified pipeline handle.
    For more advanced usage, you can also construct an entrypoint object yourself with:

        - handle.entrypoint() => LoaderEntrypoint

    This should not be necessary in common usage.
    '''

    @staticmethod
    def for_pipeline_fn(fn_name):  # pylint: disable=unused-argument
        '''This builder is a bit magical, but it inspects its caller to determine how to build a
        ExecutionTargetHandle object via python_file and fn_name.

        This will work since fn_name is ensured to be in scope in the python_file caller's scope.
        '''
        return ExecutionTargetHandle.for_pipeline_python_file(
            python_file=_get_python_file_from_previous_stack_frame(), fn_name=fn_name.__name__
        )

    @staticmethod
    def for_repo_fn(fn_name):  # pylint: disable=unused-argument
        '''This builder is a bit magical, but it inspects its caller to determine how to build a
        ExecutionTargetHandle object via python_file and fn_name.

        This will work since fn_name is ensured to be in scope in the python_file caller's scope.
        '''
        return ExecutionTargetHandle.for_repo_python_file(
            python_file=_get_python_file_from_previous_stack_frame(), fn_name=fn_name.__name__
        )

    @staticmethod
    def for_repo_yaml(repository_yaml):
        '''Builds an ExecutionTargetHandle for a repository.yml file.
        '''
        return ExecutionTargetHandle(
            _ExecutionTargetHandleData(repository_yaml=repository_yaml),
            _ExecutionTargetMode.REPOSITORY,
        )

    @staticmethod
    def for_repo_python_file(python_file, fn_name):
        '''Builds an ExecutionTargetHandle for a repository python file and function which is
        expected to return a RepositoryDefinition instance.
        '''
        return ExecutionTargetHandle(
            _ExecutionTargetHandleData(python_file=python_file, fn_name=fn_name),
            _ExecutionTargetMode.REPOSITORY,
        )

    @staticmethod
    def for_repo_module(module_name, fn_name):
        '''Builds an ExecutionTargetHandle for a repository module and function which is expected
        to return a RepositoryDefinition instance.
        '''
        return ExecutionTargetHandle(
            _ExecutionTargetHandleData(module_name=module_name, fn_name=fn_name),
            _ExecutionTargetMode.REPOSITORY,
        )

    @staticmethod
    def for_pipeline_python_file(python_file, fn_name):
        '''Builds an ExecutionTargetHandle for a pipeline python file and function which is expected
        to return a PipelineDefinition instance.
        '''
        return ExecutionTargetHandle(
            _ExecutionTargetHandleData(python_file=python_file, fn_name=fn_name),
            _ExecutionTargetMode.PIPELINE,
            is_resolved_to_pipeline=True,
        )

    @staticmethod
    def for_pipeline_module(module_name, fn_name):
        '''Builds an ExecutionTargetHandle for a pipeline python module and function which is
        expected to return a PipelineDefinition instance.
        '''
        return ExecutionTargetHandle(
            _ExecutionTargetHandleData(module_name=module_name, fn_name=fn_name),
            _ExecutionTargetMode.PIPELINE,
            is_resolved_to_pipeline=True,
        )

    @staticmethod
    def for_repo_cli_args(kwargs):
        '''Builds an ExecutionTargetHandle for CLI arguments, which can be any of the combinations
        for repo loading above.
        '''
        check.dict_param(kwargs, 'kwargs')

        def _repo_load_invariant(condition):
            if not condition:
                raise InvalidRepositoryLoadingComboError()

        _repo_load_invariant(kwargs.get('pipeline_name') is None)

        if kwargs.get('repository_yaml') or all_none(kwargs):
            _repo_load_invariant(kwargs.get('module_name') is None)
            _repo_load_invariant(kwargs.get('python_file') is None)
            _repo_load_invariant(kwargs.get('fn_name') is None)
            return ExecutionTargetHandle.for_repo_yaml(
                repository_yaml=kwargs.get('repository_yaml') or 'repository.yml'
            )
        elif kwargs.get('module_name') and kwargs.get('fn_name'):
            _repo_load_invariant(kwargs.get('repository_yaml') is None)
            _repo_load_invariant(kwargs.get('python_file') is None)
            return ExecutionTargetHandle.for_repo_module(
                module_name=kwargs['module_name'], fn_name=kwargs['fn_name']
            )
        elif kwargs.get('python_file') and kwargs.get('fn_name'):
            _repo_load_invariant(kwargs.get('repository_yaml') is None)
            _repo_load_invariant(kwargs.get('module_name') is None)
            return ExecutionTargetHandle.for_repo_python_file(
                python_file=kwargs['python_file'], fn_name=kwargs['fn_name']
            )
        else:
            raise InvalidRepositoryLoadingComboError()

    @staticmethod
    def for_pipeline_cli_args(kwargs):
        '''Builds an ExecutionTargetHandle for CLI arguments, which can be any of the combinations
        for repo/pipeline loading above.
        '''
        check.dict_param(kwargs, 'kwargs')

        def _pipeline_load_invariant(condition):
            if not condition:
                raise InvalidPipelineLoadingComboError()

        pipeline_name = kwargs.get('pipeline_name')

        if pipeline_name and not isinstance(pipeline_name, six.string_types):
            if len(pipeline_name) == 1:
                pipeline_name = pipeline_name[0]
            else:
                check.failed(
                    'Can only handle zero or one pipeline args. Got {pipeline_name}'.format(
                        pipeline_name=repr(pipeline_name)
                    )
                )

        # Pipeline from repository YAML and pipeline_name
        if (
            pipeline_name
            and kwargs.get('module_name') is None
            and kwargs.get('python_file') is None
        ):
            _pipeline_load_invariant(kwargs.get('fn_name') is None)
            return ExecutionTargetHandle.for_repo_yaml(
                repository_yaml=kwargs.get('repository_yaml') or 'repository.yml'
            ).with_pipeline_name(pipeline_name)

        # Pipeline from repository python file
        elif kwargs.get('python_file') and kwargs.get('fn_name') and pipeline_name:
            _pipeline_load_invariant(kwargs.get('repository_yaml') is None)
            _pipeline_load_invariant(kwargs.get('module_name') is None)
            return ExecutionTargetHandle.for_repo_python_file(
                python_file=kwargs['python_file'], fn_name=kwargs['fn_name']
            ).with_pipeline_name(pipeline_name)

        # Pipeline from repository module
        elif kwargs.get('module_name') and kwargs.get('fn_name') and pipeline_name:
            _pipeline_load_invariant(kwargs.get('repository_yaml') is None)
            _pipeline_load_invariant(kwargs.get('python_file') is None)
            return ExecutionTargetHandle.for_repo_module(
                module_name=kwargs['module_name'], fn_name=kwargs['fn_name']
            ).with_pipeline_name(pipeline_name)

        # Pipeline from pipeline python file
        elif kwargs.get('python_file') and kwargs.get('fn_name') and not pipeline_name:
            _pipeline_load_invariant(kwargs.get('repository_yaml') is None)
            _pipeline_load_invariant(kwargs.get('module_name') is None)
            return ExecutionTargetHandle.for_pipeline_python_file(
                python_file=kwargs['python_file'], fn_name=kwargs['fn_name']
            )

        # Pipeline from pipeline module
        elif kwargs.get('module_name') and kwargs.get('fn_name') and not pipeline_name:
            _pipeline_load_invariant(kwargs.get('repository_yaml') is None)
            _pipeline_load_invariant(kwargs.get('python_file') is None)
            return ExecutionTargetHandle.for_pipeline_module(
                module_name=kwargs['module_name'], fn_name=kwargs['fn_name']
            )
        else:
            raise InvalidPipelineLoadingComboError()

    def with_pipeline_name(self, pipeline_name):
        '''Returns a new ExecutionTargetHandle that references the pipeline "pipeline_name" within
        the repository.
        '''
        check.invariant(
            not self.is_resolved_to_pipeline,
            '''ExecutionTargetHandle already references a pipeline named {pipeline_name}, cannot
            change.'''.format(
                pipeline_name=self.data.pipeline_name
            ),
        )
        data = self.data._replace(pipeline_name=pipeline_name)
        return ExecutionTargetHandle(data, mode=self.mode, is_resolved_to_pipeline=True)

    def build_repository_definition(self):
        '''Rehydrates a RepositoryDefinition from an ExecutionTargetHandle object.

        If this ExecutionTargetHandle points to a pipeline, we create an ephemeral repository to
        wrap the pipeline and return it.
        '''
        from dagster import PipelineDefinition, RepositoryDefinition

        obj = self.entrypoint.perform_load()

        if self.mode == _ExecutionTargetMode.REPOSITORY:
            return check.inst(obj, RepositoryDefinition)
        elif self.mode == _ExecutionTargetMode.PIPELINE:
            check.inst(obj, PipelineDefinition)
            return RepositoryDefinition(name=EPHEMERAL_NAME, pipeline_dict={obj.name: lambda: obj})
        else:
            check.failed('Unhandled mode {mode}'.format(mode=self.mode))

    def build_pipeline_definition(self):
        '''Rehydrates a PipelineDefinition from an ExecutionTargetHandle object.
        '''
        from dagster import PipelineDefinition, RepositoryDefinition

        if self.mode == _ExecutionTargetMode.REPOSITORY:
            check.invariant(
                self.data.pipeline_name is not None,
                'Cannot construct a pipeline from a repository-based ExecutionTargetHandle without'
                ' a pipeline name. Use with_pipeline_name() to construct a pipeline'
                ' ExecutionTargetHandle.',
            )
            obj = self.entrypoint.perform_load()
            repository = check.inst(obj, RepositoryDefinition)
            return repository.get_pipeline(self.data.pipeline_name)
        elif self.mode == _ExecutionTargetMode.PIPELINE:
            obj = self.entrypoint.perform_load()
            return check.inst(obj, PipelineDefinition)
        else:
            check.failed('Unhandled mode {mode}'.format(mode=self.mode))

    @property
    def entrypoint(self):
        if self.mode == _ExecutionTargetMode.REPOSITORY:
            return self.data.get_repository_entrypoint()
        elif self.mode == _ExecutionTargetMode.PIPELINE:
            return self.data.get_pipeline_entrypoint()
        else:
            check.failed('Unhandled mode {mode}'.format(mode=self.mode))

    def __init__(self, data, mode, is_resolved_to_pipeline=False):
        '''Not intended to be invoked directly. Use one of the factory functions above.
        '''
        self.data = check.inst_param(data, 'data', _ExecutionTargetHandleData)
        self.mode = check.inst_param(mode, 'mode', _ExecutionTargetMode)

        # By default, this only resolves to a repository
        self.is_resolved_to_pipeline = is_resolved_to_pipeline


def _get_python_file_from_previous_stack_frame():
    '''inspect.stack() lets us introspect the call stack; inspect.stack()[1] is the previous
    stack frame.

    In Python < 3.5, this is just a tuple, of which the python file of the previous frame is the 1st
    element.

    In Python 3.5+, this is a FrameInfo namedtuple instance; the python file of the previous frame
    remains the 1st element.
    '''

    # Since this is now a function in this file, we need to go back two hops to find the
    # callsite file.
    previous_stack_frame = inspect.stack()[2]

    # See: https://docs.python.org/3/library/inspect.html
    if sys.version_info.major == 3 and sys.version_info.minor >= 5:
        from inspect import FrameInfo

        check.inst(previous_stack_frame, FrameInfo)
    else:
        check.inst(previous_stack_frame, tuple)

    python_file = previous_stack_frame[1]
    return os.path.abspath(python_file)


class _ExecutionTargetMode(Enum):
    PIPELINE = 1
    REPOSITORY = 2


class _ExecutionTargetHandleData(
    namedtuple(
        '_ExecutionTargetHandleData',
        'repository_yaml module_name python_file fn_name pipeline_name',
    )
):
    def __new__(
        cls,
        repository_yaml=None,
        module_name=None,
        python_file=None,
        fn_name=None,
        pipeline_name=None,
    ):
        return super(_ExecutionTargetHandleData, cls).__new__(
            cls,
            repository_yaml=check.opt_str_param(repository_yaml, 'repository_yaml'),
            module_name=check.opt_str_param(module_name, 'module_name'),
            python_file=check.opt_str_param(python_file, 'python_file'),
            fn_name=check.opt_str_param(fn_name, 'fn_name'),
            pipeline_name=check.opt_str_param(pipeline_name, 'pipeline_name'),
        )

    def get_repository_entrypoint(self):
        if self.repository_yaml:
            return LoaderEntrypoint.from_yaml(self.repository_yaml)
        elif self.module_name and self.fn_name:
            return LoaderEntrypoint.from_module_target(
                module_name=self.module_name, fn_name=self.fn_name
            )
        elif self.python_file and self.fn_name:
            return LoaderEntrypoint.from_file_target(
                python_file=self.python_file, fn_name=self.fn_name
            )
        else:
            raise InvalidRepositoryLoadingComboError()

    def get_pipeline_entrypoint(self):
        if self.python_file and self.fn_name:
            return LoaderEntrypoint.from_file_target(
                python_file=self.python_file, fn_name=self.fn_name
            )
        elif self.module_name and self.fn_name:
            return LoaderEntrypoint.from_module_target(
                module_name=self.module_name, fn_name=self.fn_name
            )
        raise InvalidPipelineLoadingComboError()
