import importlib
import inspect
import os
import sys
import warnings
import weakref
from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.core.definitions.partition import RepositoryPartitionsHandle
from dagster.core.definitions.pipeline import PipelineDefinition
from dagster.core.definitions.repository import RepositoryDefinition
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.scheduler import SchedulerHandle
from dagster.seven import Path, import_module_from_path
from dagster.utils import load_yaml_from_path

EPHEMERAL_NAME = '<<unnamed>>'


def _handle_backcompat_loaders(config, file_path):
    check.dict_param(config, 'config')
    partitions = config.get('partitions')
    scheduler = config.get('scheduler')
    if not (partitions or scheduler):
        return None

    warnings.warn(
        '"scheduler" and "partitions" keys in repository.yaml are deprecated. '
        'Add definitions directly via RepositoryDefinition'
    )

    backcompat_loaders = {}
    if scheduler:
        module_name = check.opt_str_elem(scheduler, 'module')
        file_name = check.opt_str_elem(scheduler, 'file')
        fn_name = check.str_elem(scheduler, 'fn')

        if module_name:
            backcompat_loaders['scheduler'] = LoaderEntrypoint.from_module_target(
                module_name, fn_name
            )
        else:
            # rebase file in config off of the path in the config file
            file_name = os.path.join(os.path.dirname(os.path.abspath(file_path)), file_name)
            backcompat_loaders['scheduler'] = LoaderEntrypoint.from_file_target(file_name, fn_name)

    if partitions:
        module_name = check.opt_str_elem(partitions, 'module')
        file_name = check.opt_str_elem(partitions, 'file')
        fn_name = check.str_elem(partitions, 'fn')

        if module_name:
            return LoaderEntrypoint.from_module_target(module_name, fn_name)
        else:
            # rebase file in config off of the path in the config file
            file_name = os.path.join(os.path.dirname(os.path.abspath(file_path)), file_name)
            backcompat_loaders['partitions'] = LoaderEntrypoint.from_file_target(file_name, fn_name)

    return backcompat_loaders


class LoaderEntrypoint(
    namedtuple('_LoaderEntrypoint', 'module module_name fn_name from_handle backcompat_loaders')
):
    def __new__(cls, module, module_name, fn_name, from_handle=None, backcompat_loaders=None):
        return super(LoaderEntrypoint, cls).__new__(
            cls, module, module_name, fn_name, from_handle, backcompat_loaders
        )

    def perform_load(self):
        # in the decorator case the attribute will be the actual definition
        if not hasattr(self.module, self.fn_name):
            raise DagsterInvariantViolationError(
                '{name} not found in module {module}.'.format(name=self.fn_name, module=self.module)
            )

        fn_repo_or_pipeline = getattr(self.module, self.fn_name)

        # This is the @pipeline case
        if isinstance(fn_repo_or_pipeline, PipelineDefinition):
            inst = fn_repo_or_pipeline

        # This is the define_pipeline() or define_repo() case
        elif callable(fn_repo_or_pipeline):
            repo_or_pipeline = fn_repo_or_pipeline()

            if not isinstance(repo_or_pipeline, (RepositoryDefinition, PipelineDefinition)):
                raise DagsterInvariantViolationError(
                    '{fn_name} is a function but must return a PipelineDefinition '
                    'or a RepositoryDefinition, or be decorated with @pipeline.'.format(
                        fn_name=self.fn_name
                    )
                )

            inst = repo_or_pipeline

            if self.backcompat_loaders:
                check.invariant(
                    isinstance(inst, RepositoryDefinition),
                    'backcompat_loaders only for repository',
                )
                partitions_loader = self.backcompat_loaders.get('partitions')
                scheduler_loader = self.backcompat_loaders.get('scheduler')
                if partitions_loader:
                    partition_handle = partitions_loader.backcompat_load(RepositoryPartitionsHandle)
                    inst.backcompat_add_partition_set_defs(partition_handle.get_partition_sets())

                if scheduler_loader:
                    schedule_handle = scheduler_loader.backcompat_load(SchedulerHandle)
                    inst.backcompat_add_schedule_defs(schedule_handle.schedule_defs)

        else:
            raise DagsterInvariantViolationError(
                '{fn_name} must be a function that returns a PipelineDefinition '
                'or a RepositoryDefinition, or a function decorated with @pipeline.'.format(
                    fn_name=self.fn_name
                )
            )

        if self.from_handle:
            return ExecutionTargetHandle.cache_handle(inst, self.from_handle)

        return inst

    def backcompat_load(self, klass):
        if not hasattr(self.module, self.fn_name):
            raise DagsterInvariantViolationError(
                '{name} not found in module {module}.'.format(name=self.fn_name, module=self.module)
            )

        target = getattr(self.module, self.fn_name)

        if isinstance(target, klass):
            return target

        if callable(target):
            handle = target()
            if not isinstance(handle, klass):
                raise DagsterInvariantViolationError(
                    '{fn_name} is a function but must return a {klass.__name__}.'.format(
                        fn_name=self.fn_name, klass=klass
                    )
                )
            return handle

        raise DagsterInvariantViolationError(
            '{fn_name} must be a function that returns a {klass.__name__}.'.format(
                fn_name=self.fn_name, klass=klass
            )
        )

    @staticmethod
    def from_file_target(python_file, fn_name, from_handle=None, backcompat_loaders=None):
        file_directory = os.path.dirname(python_file)
        if file_directory not in sys.path:
            sys.path.append(file_directory)

        module_name = os.path.splitext(os.path.basename(python_file))[0]
        module = import_module_from_path(module_name, os.path.abspath(python_file))

        return LoaderEntrypoint(module, module_name, fn_name, from_handle, backcompat_loaders)

    @staticmethod
    def from_module_target(module_name, fn_name, from_handle=None, backcompat_loaders=None):
        module = importlib.import_module(module_name)
        return LoaderEntrypoint(module, module_name, fn_name, from_handle, backcompat_loaders)

    @staticmethod
    def from_yaml(file_path, from_handle=None):
        check.str_param(file_path, 'file_path')

        config = load_yaml_from_path(file_path)
        repository_config = check.dict_elem(config, 'repository')
        module_name = check.opt_str_elem(repository_config, 'module')
        file_name = check.opt_str_elem(repository_config, 'file')
        fn_name = check.str_elem(repository_config, 'fn')

        # Back compat
        backcompat_loaders = _handle_backcompat_loaders(config, file_path)

        if module_name:
            return LoaderEntrypoint.from_module_target(
                module_name, fn_name, from_handle, backcompat_loaders
            )
        else:
            # rebase file in config off of the path in the config file
            file_name = os.path.join(os.path.dirname(os.path.abspath(file_path)), file_name)
            return LoaderEntrypoint.from_file_target(
                file_name, fn_name, from_handle, backcompat_loaders
            )


class ExecutionTargetHandleCacheEntry(
    namedtuple('_ExecutionTargetHandleCacheEntry', 'handle solid_subset')
):
    def __new__(cls, handle, solid_subset=None):
        check.inst_param(handle, 'handle', ExecutionTargetHandle)
        check.opt_list_param(solid_subset, 'solid_subset', of_type=str)
        return super(ExecutionTargetHandleCacheEntry, cls).__new__(cls, handle, solid_subset)


class ExecutionTargetHandle(object):
    '''ExecutionTargetHandle represents an immutable, serializable reference to a Dagster
    RepositoryDefinition or PipelineDefinition, to support dynamically loading these in various
    contexts (e.g. across process boundaries).

    This class must remain pickle-serializable to ensure multiprocessing compatibility, and is the
    one of the primary reasons that we pass this around vs. an instantiated
    RepositoryDefinition/PipelineDefinition object.

    Creation:
    ExecutionTargetHandles can be created via the staticmethod constructors below.

        - for_repo_fn
        - for_repo_yaml
        - for_repo_python_file
        - for_repo_module
        - for_pipeline_fn
        - for_pipeline_python_file
        - for_pipeline_module

    Also, the following constructors are provided to support construction from CLI tools in
    dagster.cli.load_handle:

        - handle_for_repo_cli_args
        - handle_for_pipeline_cli_args

    Since an ExecutionTargetHandle can reference either a RepositoryDefinition or a fully-qualified
    pipeline, it provides a property `is_resolved_to_pipeline` which identifies whether it is fully-
    qualified to a pipeline reference.

    For repository-based handles, you can use the `with_pipeline_name(pipeline_name)` method on a
    repository handle to construct and return a new fully-qualified pipeline handle.

    Usage:
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

    __cache__ = weakref.WeakKeyDictionary()
    '''The cache is used to cache handles used to create PipelineDefinition and
    RepositoryDefinition objects, so the handles can be passed across serialization boundaries (as
    for dagstermill) by solid compute logic.'''

    @classmethod
    def get_handle(cls, repo_or_pipeline):
        '''Get the handle and, optionally, solid subset used to construct a repo or (sub-)pipeline.

        Returns: Union[ExecutionTargetHandleCacheEntry, (None, None)]
        '''
        check.inst_param(
            repo_or_pipeline, 'repo_or_pipeline', (RepositoryDefinition, PipelineDefinition)
        )
        return cls.__cache__.get(repo_or_pipeline) or (None, None)

    @classmethod
    def cache_handle(cls, repo_or_pipeline_def, handle=None, solid_names=None):
        '''Record a pipeline or repository in the cache.

        Args:
            repo_or_pipeline_def (Union[RepositoryDefinition, PipelineDefinition]): The repo or
                pipeline definition for which to cache the handle.

        Kwargs:
            handle (ExecutionTargetHandle): The handle to cache.
            solid_names (Optional[List[str]]): The solid names constituting the constructed
                sub-pipeline, if any; arg should be as for
                dagster.core.definitions.pipeline.build_sub_pipeline.
        '''
        check.inst_param(
            repo_or_pipeline_def, 'repo_or_pipeline_def', (RepositoryDefinition, PipelineDefinition)
        )
        check.inst_param(handle, 'handle', ExecutionTargetHandle)
        check.opt_list_param(solid_names, 'solid_names', of_type=str)
        cls.__cache__[repo_or_pipeline_def] = ExecutionTargetHandleCacheEntry(handle, solid_names)

        return repo_or_pipeline_def

    @staticmethod
    def for_pipeline_fn(fn):
        '''This builder is a bit magical, but it inspects its caller to determine how to build a
        ExecutionTargetHandle object via python_file and fn_name.

        This will work since fn_name is ensured to be in scope in the python_file caller's scope.
        '''
        check.callable_param(fn, 'fn')
        return ExecutionTargetHandle.for_pipeline_python_file(
            python_file=_get_python_file_from_previous_stack_frame(), fn_name=fn.__name__
        )

    @staticmethod
    def for_repo_fn(fn):
        '''This builder is a bit magical, but it inspects its caller to determine how to build a
        ExecutionTargetHandle object via python_file and fn_name.

        This will work since fn_name is ensured to be in scope in the python_file caller's scope.
        '''
        check.callable_param(fn, 'fn')
        return ExecutionTargetHandle.for_repo_python_file(
            python_file=_get_python_file_from_previous_stack_frame(), fn_name=fn.__name__
        )

    @staticmethod
    def for_repo_yaml(repository_yaml):
        '''Builds an ExecutionTargetHandle for a repository.yml file.
        '''
        return ExecutionTargetHandle(
            _ExecutionTargetHandleData(repository_yaml=os.path.abspath(repository_yaml)),
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
    def from_dict(handle_dict):
        return ExecutionTargetHandle(
            data=_ExecutionTargetHandleData(**handle_dict['data']),
            mode=getattr(_ExecutionTargetMode, handle_dict['mode']),
            is_resolved_to_pipeline=handle_dict['is_resolved_to_pipeline'],
        )

    def to_dict(self):
        return {
            'data': self.data._asdict(),
            'mode': self.mode.name,
            'is_resolved_to_pipeline': self.is_resolved_to_pipeline,
        }

    def with_pipeline_name(self, pipeline_name):
        '''Returns a new ExecutionTargetHandle that references the pipeline "pipeline_name" within
        the repository.
        '''
        if self.is_resolved_to_pipeline and self.data.pipeline_name == pipeline_name:
            return self

        check.invariant(
            not (self.is_resolved_to_pipeline and self.data.pipeline_name is not None),
            '''ExecutionTargetHandle already references a pipeline named {pipeline_name}, cannot
            change to {new_pipeline_name}.'''.format(
                pipeline_name=self.data.pipeline_name, new_pipeline_name=pipeline_name
            ),
        )
        data = self.data._replace(pipeline_name=pipeline_name)
        return ExecutionTargetHandle(data, mode=self.mode, is_resolved_to_pipeline=True)

    def build_repository_definition(self):
        '''Rehydrates a RepositoryDefinition from an ExecutionTargetHandle object.

        If this ExecutionTargetHandle points to a pipeline, we create an ephemeral repository to
        wrap the pipeline and return it.
        '''
        obj = self.entrypoint.perform_load()

        if isinstance(obj, PipelineDefinition):
            # User passed in a function that returns a pipeline definition, not a repository. See:
            # https://github.com/dagster-io/dagster/issues/1439
            return ExecutionTargetHandle.cache_handle(
                RepositoryDefinition(name=EPHEMERAL_NAME, pipeline_defs=[obj]),
                *ExecutionTargetHandle.get_handle(obj)
            )
        elif isinstance(obj, RepositoryDefinition):
            return ExecutionTargetHandle.cache_handle(obj, *ExecutionTargetHandle.get_handle(obj))
        else:
            check.failed('Loaded object is neither a PipelineDefinition nor a RepositoryDefinition')

    def build_pipeline_definition(self):
        '''Rehydrates a PipelineDefinition from an ExecutionTargetHandle object.
        '''
        if not self.is_resolved_to_pipeline:
            raise DagsterInvariantViolationError(
                'Cannot construct a pipeline from a repository-based ExecutionTargetHandle without'
                ' a pipeline name. Use with_pipeline_name() to construct a pipeline'
                ' ExecutionTargetHandle.'
            )
        else:
            obj = self.entrypoint.perform_load()
            if isinstance(obj, PipelineDefinition):
                return ExecutionTargetHandle.cache_handle(obj, self)
            else:
                return ExecutionTargetHandle.cache_handle(
                    obj.get_pipeline(self.data.pipeline_name), self
                )

    @property
    def entrypoint(self):
        if self.mode == _ExecutionTargetMode.REPOSITORY:
            return self.data.get_repository_entrypoint(from_handle=self)
        elif self.mode == _ExecutionTargetMode.PIPELINE:
            return self.data.get_pipeline_entrypoint(from_handle=self)
        else:
            check.failed('Unhandled mode {mode}'.format(mode=self.mode))

    def to_module_name_based_handle(self, package_dir):
        def _module_name(path):
            abs_path = os.path.abspath(path)
            abs_package_dir = os.path.abspath(package_dir)
            check.invariant(
                os.path.commonprefix([abs_path, abs_package_dir]) == abs_package_dir,
                'File {abs_path} is not underneath package dir {abs_package_dir}'.format(
                    abs_path=abs_path, abs_package_dir=abs_package_dir,
                ),
            )

            relative_path = os.path.relpath(abs_path, abs_package_dir)
            without_extension, _ = os.path.splitext(relative_path)
            return '.'.join(without_extension.split(os.sep))

        if self.mode == _ExecutionTargetMode.PIPELINE:
            entrypoint = self.data.get_pipeline_entrypoint()
            return ExecutionTargetHandle.for_pipeline_module(
                _module_name(entrypoint.module.__file__), entrypoint.fn_name,
            )
        elif self.mode == _ExecutionTargetMode.REPOSITORY:
            entrypoint = self.data.get_repository_entrypoint()
            handle = ExecutionTargetHandle.for_repo_module(
                _module_name(entrypoint.module.__file__), entrypoint.fn_name,
            )
            if self.is_resolved_to_pipeline:
                return handle.with_pipeline_name(self.data.pipeline_name)
            else:
                return handle
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
        check.inst(previous_stack_frame, inspect.FrameInfo)
    else:
        check.inst(previous_stack_frame, tuple)

    python_file = previous_stack_frame[1]
    return os.path.abspath(python_file)


class _ExecutionTargetMode(Enum):
    PIPELINE = 1  # The entrypoint is a pipeline
    REPOSITORY = 2  # The entrypoint is a repository


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

    def get_repository_entrypoint(self, from_handle=None):
        if self.repository_yaml:
            return LoaderEntrypoint.from_yaml(self.repository_yaml, from_handle=from_handle)
        elif self.module_name and self.fn_name:
            return LoaderEntrypoint.from_module_target(
                module_name=self.module_name, fn_name=self.fn_name, from_handle=from_handle
            )
        elif self.python_file and self.fn_name:
            return LoaderEntrypoint.from_file_target(
                python_file=self.python_file, fn_name=self.fn_name, from_handle=from_handle
            )
        else:
            raise DagsterInvariantViolationError(
                (
                    'You have attempted to load a repository with an invalid '
                    'combination of properties. repository_yaml {repository_yaml} '
                    'module_name {module_name} python_file {python_file} '
                    'fn_name {fn_name}.'
                ).format(
                    repository_yaml=self.repository_yaml,
                    module_name=self.module_name,
                    fn_name=self.fn_name,
                    python_file=self.python_file,
                )
            )

    def get_pipeline_entrypoint(self, from_handle=None):
        if self.python_file and self.fn_name:
            return LoaderEntrypoint.from_file_target(
                python_file=self.python_file, fn_name=self.fn_name, from_handle=from_handle
            )
        elif self.module_name and self.fn_name:
            return LoaderEntrypoint.from_module_target(
                module_name=self.module_name, fn_name=self.fn_name, from_handle=from_handle
            )
        elif self.pipeline_name:
            return self.get_repository_entrypoint(from_handle=from_handle)
        raise DagsterInvariantViolationError(
            (
                'You have attempted to directly load a pipeline with an invalid '
                'combination of properties module_name {module_name} python_file '
                '{python_file} fn_name {fn_name}.'
            ).format(
                module_name=self.module_name, fn_name=self.fn_name, python_file=self.python_file
            )
        )

    def _asdict(self):
        ddict = super(_ExecutionTargetHandleData, self)._asdict()

        # Normalize to Posix paths
        for key in ['repository_yaml', 'python_file']:
            if ddict[key]:
                ddict[key] = Path(ddict[key]).as_posix()
        return ddict
