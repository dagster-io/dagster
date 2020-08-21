import os
import sys
from collections import namedtuple

from dagster import check, seven
from dagster.core.code_pointer import (
    CodePointer,
    FileCodePointer,
    ModuleCodePointer,
    get_python_file_from_previous_stack_frame,
)
from dagster.core.errors import DagsterInvalidSubsetError, DagsterInvariantViolationError
from dagster.core.origin import PipelinePythonOrigin, RepositoryPythonOrigin, SchedulePythonOrigin
from dagster.core.selector import parse_solid_selection
from dagster.serdes import pack_value, unpack_value, whitelist_for_serdes
from dagster.seven import lru_cache

from .executable import ExecutablePipeline


def get_ephemeral_repository_name(pipeline_name):
    check.str_param(pipeline_name, "pipeline_name")
    return "<<pipeline:{pipeline_name}>>".format(pipeline_name=pipeline_name)


@whitelist_for_serdes
class ReconstructableRepository(namedtuple("_ReconstructableRepository", "pointer")):
    def __new__(
        cls, pointer,
    ):
        return super(ReconstructableRepository, cls).__new__(
            cls, pointer=check.inst_param(pointer, "pointer", CodePointer),
        )

    @lru_cache(maxsize=1)
    def get_definition(self):
        return repository_def_from_pointer(self.pointer)

    def get_reconstructable_pipeline(self, name):
        return ReconstructablePipeline(self, name)

    def get_reconstructable_schedule(self, name):
        return ReconstructableSchedule(self, name)

    @classmethod
    def for_file(cls, file, fn_name, working_directory=None):
        if not working_directory:
            working_directory = os.getcwd()
        return cls(FileCodePointer(file, fn_name, working_directory))

    @classmethod
    def for_module(cls, module, fn_name):
        return cls(ModuleCodePointer(module, fn_name))

    def get_cli_args(self):
        return self.pointer.get_cli_args()

    @classmethod
    def from_legacy_repository_yaml(cls, file_path):
        check.str_param(file_path, "file_path")
        absolute_file_path = os.path.abspath(os.path.expanduser(file_path))
        return cls(pointer=CodePointer.from_legacy_repository_yaml(absolute_file_path))

    def get_origin(self):
        return RepositoryPythonOrigin(executable_path=sys.executable, code_pointer=self.pointer)

    def get_origin_id(self):
        return self.get_origin().get_id()


@whitelist_for_serdes
class ReconstructablePipeline(
    namedtuple(
        "_ReconstructablePipeline",
        "repository pipeline_name solid_selection_str solids_to_execute",
    ),
    ExecutablePipeline,
):
    def __new__(
        cls, repository, pipeline_name, solid_selection_str=None, solids_to_execute=None,
    ):
        check.opt_set_param(solids_to_execute, "solids_to_execute", of_type=str)
        return super(ReconstructablePipeline, cls).__new__(
            cls,
            repository=check.inst_param(repository, "repository", ReconstructableRepository),
            pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
            solid_selection_str=check.opt_str_param(solid_selection_str, "solid_selection_str"),
            solids_to_execute=solids_to_execute,
        )

    @property
    def solid_selection(self):
        return seven.json.loads(self.solid_selection_str) if self.solid_selection_str else None

    @lru_cache(maxsize=1)
    def get_definition(self):
        return (
            self.repository.get_definition()
            .get_pipeline(self.pipeline_name)
            .get_pipeline_subset_def(self.solids_to_execute)
        )

    def _resolve_solid_selection(self, solid_selection):
        # resolve a list of solid selection queries to a frozenset of qualified solid names
        # e.g. ['foo_solid+'] to {'foo_solid', 'bar_solid'}
        check.list_param(solid_selection, "solid_selection", of_type=str)
        solids_to_execute = parse_solid_selection(self.get_definition(), solid_selection)
        if len(solids_to_execute) == 0:
            raise DagsterInvalidSubsetError(
                "No qualified solids to execute found for solid_selection={requested}".format(
                    requested=solid_selection
                )
            )
        return solids_to_execute

    def get_reconstructable_repository(self):
        return self.repository

    def _subset_for_execution(self, solids_to_execute, solid_selection=None):
        if solids_to_execute:
            pipe = ReconstructablePipeline(
                repository=self.repository,
                pipeline_name=self.pipeline_name,
                solid_selection_str=seven.json.dumps(solid_selection) if solid_selection else None,
                solids_to_execute=frozenset(solids_to_execute),
            )
        else:
            pipe = ReconstructablePipeline(
                repository=self.repository, pipeline_name=self.pipeline_name,
            )

        pipe.get_definition()  # verify the subset is correct
        return pipe

    def subset_for_execution(self, solid_selection):
        # take a list of solid queries and resolve the queries to names of solids to execute
        check.opt_list_param(solid_selection, "solid_selection", of_type=str)
        solids_to_execute = (
            self._resolve_solid_selection(solid_selection) if solid_selection else None
        )

        return self._subset_for_execution(solids_to_execute, solid_selection)

    def subset_for_execution_from_existing_pipeline(self, solids_to_execute):
        # take a frozenset of resolved solid names from an existing pipeline
        # so there's no need to parse the selection
        check.opt_set_param(solids_to_execute, "solids_to_execute", of_type=str)

        return self._subset_for_execution(solids_to_execute)

    def describe(self):
        return '"{name}" in repository ({repo})'.format(
            repo=self.repository.pointer.describe, name=self.pipeline_name
        )

    @staticmethod
    def for_file(python_file, fn_name):
        return bootstrap_standalone_recon_pipeline(
            FileCodePointer(python_file, fn_name, os.getcwd())
        )

    @staticmethod
    def for_module(module, fn_name):
        return bootstrap_standalone_recon_pipeline(ModuleCodePointer(module, fn_name))

    def to_dict(self):
        return pack_value(self)

    @staticmethod
    def from_dict(val):
        check.dict_param(val, "val")

        inst = unpack_value(val)
        check.invariant(
            isinstance(inst, ReconstructablePipeline),
            "Deserialized object is not instance of ReconstructablePipeline, got {type}".format(
                type=type(inst)
            ),
        )
        return inst

    def get_origin(self):
        return PipelinePythonOrigin(self.pipeline_name, self.repository.get_origin())

    def get_origin_id(self):
        return self.get_origin().get_id()


@whitelist_for_serdes
class ReconstructableSchedule(namedtuple("_ReconstructableSchedule", "repository schedule_name",)):
    def __new__(
        cls, repository, schedule_name,
    ):
        return super(ReconstructableSchedule, cls).__new__(
            cls,
            repository=check.inst_param(repository, "repository", ReconstructableRepository),
            schedule_name=check.str_param(schedule_name, "schedule_name"),
        )

    def get_origin(self):
        return SchedulePythonOrigin(self.schedule_name, self.repository.get_origin())

    def get_origin_id(self):
        return self.get_origin().get_id()

    @lru_cache(maxsize=1)
    def get_definition(self):
        return self.repository.get_definition().get_schedule_def(self.schedule_name)


def reconstructable(target):
    """
    Create a ReconstructablePipeline from a function that returns a PipelineDefinition
    or a @pipeline decorated function.
    """
    from dagster.core.definitions import PipelineDefinition

    if not seven.is_function_or_decorator_instance_of(target, PipelineDefinition):
        raise DagsterInvariantViolationError(
            "Reconstructable target should be a function or definition produced "
            "by a decorated function, got {type}.".format(type=type(target)),
        )

    if seven.is_lambda(target):
        raise DagsterInvariantViolationError(
            "Reconstructable target can not be a lambda. Use a function or "
            "decorated function defined at module scope instead."
        )

    if seven.qualname_differs(target):
        raise DagsterInvariantViolationError(
            'Reconstructable target "{target.__name__}" has a different '
            '__qualname__ "{target.__qualname__}" indicating it is not '
            "defined at module scope. Use a function or decorated function "
            "defined at module scope instead.".format(target=target)
        )

    python_file = get_python_file_from_previous_stack_frame()
    if python_file.endswith("<stdin>"):
        raise DagsterInvariantViolationError(
            "reconstructable() can not reconstruct pipelines from <stdin>, unable to target file {}. ".format(
                python_file
            )
        )
    pointer = FileCodePointer(
        python_file=python_file, fn_name=target.__name__, working_directory=os.getcwd()
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


def _check_is_loadable(definition):
    from .pipeline import PipelineDefinition
    from .repository import RepositoryDefinition

    if not isinstance(definition, (PipelineDefinition, RepositoryDefinition)):
        raise DagsterInvariantViolationError(
            (
                "Loadable attributes must be either a PipelineDefinition or a "
                "RepositoryDefinition. Got {definition}."
            ).format(definition=repr(definition))
        )
    return definition


def load_def_in_module(module_name, attribute):
    return def_from_pointer(CodePointer.from_module(module_name, attribute))


def load_def_in_package(package_name, attribute):
    return def_from_pointer(CodePointer.from_python_package(package_name, attribute))


def load_def_in_python_file(python_file, attribute, working_directory):
    return def_from_pointer(CodePointer.from_python_file(python_file, attribute, working_directory))


def def_from_pointer(pointer):
    target = pointer.load_target()

    if not callable(target):
        return _check_is_loadable(target)

    # if its a function invoke it - otherwise we are pointing to a
    # artifact in module scope, likely decorator output

    if seven.get_args(target):
        raise DagsterInvariantViolationError(
            "Error invoking function at {target} with no arguments. "
            "Reconstructable target must be callable with no arguments".format(
                target=pointer.describe()
            )
        )

    return _check_is_loadable(target())


def pipeline_def_from_pointer(pointer):
    from .pipeline import PipelineDefinition

    target = def_from_pointer(pointer)

    if isinstance(target, PipelineDefinition):
        return target

    raise DagsterInvariantViolationError(
        "CodePointer ({str}) must resolve to a PipelineDefinition. "
        "Received a {type}".format(str=pointer.describe(), type=type(target))
    )


def repository_def_from_target_def(target):
    from .pipeline import PipelineDefinition
    from .repository import RepositoryData, RepositoryDefinition

    # special case - we can wrap a single pipeline in a repository
    if isinstance(target, PipelineDefinition):
        # consider including pipeline name in generated repo name
        return RepositoryDefinition(
            name=get_ephemeral_repository_name(target.name),
            repository_data=RepositoryData.from_list([target]),
        )
    elif isinstance(target, RepositoryDefinition):
        return target
    else:
        return None


def repository_def_from_pointer(pointer):
    target = def_from_pointer(pointer)
    repo_def = repository_def_from_target_def(target)
    if not repo_def:
        raise DagsterInvariantViolationError(
            "CodePointer ({str}) must resolve to a "
            "RepositoryDefinition or a PipelineDefinition. "
            "Received a {type}".format(str=pointer.describe(), type=type(target))
        )
    return repo_def
