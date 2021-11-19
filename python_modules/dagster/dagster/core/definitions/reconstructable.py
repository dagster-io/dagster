import inspect
import os
import sys
from collections import namedtuple
from functools import lru_cache

from dagster import check, seven
from dagster.core.code_pointer import (
    CodePointer,
    CustomPointer,
    FileCodePointer,
    ModuleCodePointer,
    get_python_file_from_target,
)
from dagster.core.errors import DagsterInvalidSubsetError, DagsterInvariantViolationError
from dagster.core.origin import PipelinePythonOrigin, RepositoryPythonOrigin, SchedulePythonOrigin
from dagster.core.selector import parse_solid_selection
from dagster.serdes import pack_value, unpack_value, whitelist_for_serdes
from dagster.utils.backcompat import experimental

from .pipeline_base import IPipeline


def get_ephemeral_repository_name(pipeline_name):
    check.str_param(pipeline_name, "pipeline_name")
    return "__repository__{pipeline_name}".format(pipeline_name=pipeline_name)


@whitelist_for_serdes
class ReconstructableRepository(
    namedtuple("_ReconstructableRepository", "pointer container_image executable_path")
):
    def __new__(
        cls,
        pointer,
        container_image=None,
        executable_path=None,
    ):
        return super(ReconstructableRepository, cls).__new__(
            cls,
            pointer=check.inst_param(pointer, "pointer", CodePointer),
            container_image=check.opt_str_param(container_image, "container_image"),
            executable_path=check.opt_str_param(executable_path, "executable_path"),
        )

    @lru_cache(maxsize=1)
    def get_definition(self):
        return repository_def_from_pointer(self.pointer)

    def get_reconstructable_pipeline(self, name):
        return ReconstructablePipeline(self, name)

    def get_reconstructable_schedule(self, name):
        return ReconstructableSchedule(self, name)

    @classmethod
    def for_file(cls, file, fn_name, working_directory=None, container_image=None):
        if not working_directory:
            working_directory = os.getcwd()
        return cls(FileCodePointer(file, fn_name, working_directory), container_image)

    @classmethod
    def for_module(cls, module, fn_name, container_image=None):
        return cls(ModuleCodePointer(module, fn_name), container_image)

    def get_cli_args(self):
        return self.pointer.get_cli_args()

    def get_python_origin(self):
        return RepositoryPythonOrigin(
            executable_path=self.executable_path if self.executable_path else sys.executable,
            code_pointer=self.pointer,
            container_image=self.container_image,
        )

    def get_python_origin_id(self):
        return self.get_python_origin().get_id()


@whitelist_for_serdes
class ReconstructablePipeline(
    namedtuple(
        "_ReconstructablePipeline",
        "repository pipeline_name solid_selection_str solids_to_execute",
    ),
    IPipeline,
):
    def __new__(
        cls,
        repository,
        pipeline_name,
        solid_selection_str=None,
        solids_to_execute=None,
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
        from dagster.core.definitions.job_definition import JobDefinition

        defn = self.repository.get_definition().get_pipeline(self.pipeline_name)

        if isinstance(defn, JobDefinition):
            return (
                self.repository.get_definition()
                .get_pipeline(self.pipeline_name)
                .get_job_def_for_op_selection(
                    list(self.solids_to_execute) if self.solids_to_execute else None
                )
            )
        else:
            return (
                self.repository.get_definition()
                .get_pipeline(self.pipeline_name)
                .get_pipeline_subset_def(self.solids_to_execute)
            )

    def _resolve_solid_selection(self, solid_selection):
        # resolve a list of solid selection queries to a frozenset of qualified solid names
        # e.g. ['foo_solid+'] to {'foo_solid', 'bar_solid'}
        check.list_param(solid_selection, "solid_selection", of_type=str)
        pipeline_def = self.get_definition()
        solids_to_execute = parse_solid_selection(pipeline_def, solid_selection)
        if len(solids_to_execute) == 0:
            raise DagsterInvalidSubsetError(
                "No qualified {node_type} to execute found for {selection_type}={requested}".format(
                    requested=solid_selection,
                    node_type="ops" if pipeline_def.is_job else "solids",
                    selection_type="op_selection" if pipeline_def.is_job else "solid_selection",
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
                repository=self.repository,
                pipeline_name=self.pipeline_name,
            )

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

    def get_python_origin(self):
        return PipelinePythonOrigin(self.pipeline_name, self.repository.get_python_origin())

    def get_python_origin_id(self):
        return self.get_python_origin().get_id()


@whitelist_for_serdes
class ReconstructableSchedule(
    namedtuple(
        "_ReconstructableSchedule",
        "repository schedule_name",
    )
):
    def __new__(
        cls,
        repository,
        schedule_name,
    ):
        return super(ReconstructableSchedule, cls).__new__(
            cls,
            repository=check.inst_param(repository, "repository", ReconstructableRepository),
            schedule_name=check.str_param(schedule_name, "schedule_name"),
        )

    def get_python_origin(self):
        return SchedulePythonOrigin(self.schedule_name, self.repository.get_python_origin())

    def get_python_origin_id(self):
        return self.get_python_origin().get_id()

    @lru_cache(maxsize=1)
    def get_definition(self):
        return self.repository.get_definition().get_schedule_def(self.schedule_name)


def reconstructable(target):
    """
    Create a :py:class:`~dagster.core.definitions.reconstructable.ReconstructablePipeline` from a
    function that returns a :py:class:`~dagster.PipelineDefinition`/:py:class:`~dagster.JobDefinition`,
    or a function decorated with :py:func:`@pipeline <dagster.pipeline>`/:py:func:`@job <dagster.job>`.

    When your pipeline/job must cross process boundaries, e.g., for execution on multiple nodes or
    in different systems (like ``dagstermill``), Dagster must know how to reconstruct the pipeline/job
    on the other side of the process boundary.

    Passing a job created with ``~dagster.GraphDefinition.to_job`` to ``reconstructable()``,
    requires you to wrap that job's definition in a module-scoped function, and pass that function
    instead:

    .. code-block:: python

        from dagster import graph, reconstructable

        @graph
        def my_graph():
            ...

        def define_my_job():
            return my_graph.to_job()

        reconstructable(define_my_job)

    This function implements a very conservative strategy for reconstruction, so that its behavior
    is easy to predict, but as a consequence it is not able to reconstruct certain kinds of pipelines
    or jobs, such as those defined by lambdas, in nested scopes (e.g., dynamically within a method
    call), or in interactive environments such as the Python REPL or Jupyter notebooks.

    If you need to reconstruct objects constructed in these ways, you should use
    :py:func:`~dagster.core.definitions.reconstructable.build_reconstructable_pipeline` instead,
    which allows you to specify your own reconstruction strategy.

    Examples:

    .. code-block:: python

        from dagster import job, reconstructable

        @job
        def foo_job():
            ...

        reconstructable_foo_job = reconstructable(foo_job)


        @graph
        def foo():
            ...

        def make_bar_job():
            return foo.to_job()

        reconstructable_bar_job = reconstructable(make_bar_job)
    """
    from dagster.core.definitions import PipelineDefinition, JobDefinition

    if not seven.is_function_or_decorator_instance_of(target, PipelineDefinition):
        if isinstance(target, JobDefinition):
            raise DagsterInvariantViolationError(
                "Reconstructable target was not a function returning a job definition, or a job "
                "definition produced by a decorated function. If your job was constructed using "
                "``GraphDefinition.to_job``, you must wrap the ``to_job`` call in a function at "
                "module scope, ie not within any other functions. "
                "To learn more, check out the docs on ``reconstructable``: "
                "https://docs.dagster.io/_apidocs/execution#dagster.reconstructable"
            )
        raise DagsterInvariantViolationError(
            "Reconstructable target should be a function or definition produced "
            "by a decorated function, got {type}.".format(type=type(target)),
        )

    if seven.is_lambda(target):
        raise DagsterInvariantViolationError(
            "Reconstructable target can not be a lambda. Use a function or "
            "decorated function defined at module scope instead, or use "
            "build_reconstructable_target."
        )

    if seven.qualname_differs(target):
        raise DagsterInvariantViolationError(
            'Reconstructable target "{target.__name__}" has a different '
            '__qualname__ "{target.__qualname__}" indicating it is not '
            "defined at module scope. Use a function or decorated function "
            "defined at module scope instead, or use build_reconstructable_pipeline.".format(
                target=target
            )
        )

    try:
        if (
            hasattr(target, "__module__")
            and hasattr(target, "__name__")
            and inspect.getmodule(target).__name__ != "__main__"
        ):
            return ReconstructablePipeline.for_module(target.__module__, target.__name__)
    except:
        pass

    python_file = get_python_file_from_target(target)
    if not python_file:
        raise DagsterInvariantViolationError(
            "reconstructable() can not reconstruct jobs or pipelines defined in interactive environments "
            "like <stdin>, IPython, or Jupyter notebooks. "
            "Use a pipeline defined in a module or file instead, or "
            "use build_reconstructable_target."
        )

    pointer = FileCodePointer(
        python_file=python_file, fn_name=target.__name__, working_directory=os.getcwd()
    )

    return bootstrap_standalone_recon_pipeline(pointer)


@experimental
def build_reconstructable_target(
    reconstructor_module_name,
    reconstructor_function_name,
    reconstructable_args=None,
    reconstructable_kwargs=None,
):
    """
    Create a :py:class:`dagster.core.definitions.reconstructable.ReconstructablePipeline`.

    When your pipeline must cross process boundaries, e.g., for execution on multiple nodes or
    in different systems (like ``dagstermill``), Dagster must know how to reconstruct the pipeline
    on the other side of the process boundary.

    This function allows you to use the strategy of your choice for reconstructing pipelines, so
    that you can reconstruct certain kinds of pipelines that are not supported by
    :py:func:`~dagster.reconstructable`, such as those defined by lambdas, in nested scopes (e.g.,
    dynamically within a method call), or in interactive environments such as the Python REPL or
    Jupyter notebooks.

    If you need to reconstruct pipelines constructed in these ways, use this function instead of
    :py:func:`~dagster.reconstructable`.

    Args:
        reconstructor_module_name (str): The name of the module containing the function to use to
            reconstruct the pipeline.
        reconstructor_function_name (str): The name of the function to use to reconstruct the
            pipeline.
        reconstructable_args (Tuple): Args to the function to use to reconstruct the pipeline.
            Values of the tuple must be JSON serializable.
        reconstructable_kwargs (Dict[str, Any]): Kwargs to the function to use to reconstruct the
            pipeline. Values of the dict must be JSON serializable.

    Examples:

    .. code-block:: python

        # module: mymodule

        from dagster import PipelineDefinition, pipeline, build_reconstructable_pipeline

        class PipelineFactory:
            def make_pipeline(*args, **kwargs):

                @pipeline
                def _pipeline(...):
                    ...

                return _pipeline

        def reconstruct_pipeline(*args):
            factory = PipelineFactory()
            return factory.make_pipeline(*args)

        factory = PipelineFactory()

        foo_pipeline_args = (...,...)

        foo_pipeline_kwargs = {...:...}

        foo_pipeline = factory.make_pipeline(*foo_pipeline_args, **foo_pipeline_kwargs)

        reconstructable_foo_pipeline = build_reconstructable_pipeline(
            'mymodule',
            'reconstruct_pipeline',
            foo_pipeline_args,
            foo_pipeline_kwargs,
        )
    """
    check.str_param(reconstructor_module_name, "reconstructor_module_name")
    check.str_param(reconstructor_function_name, "reconstructor_function_name")

    reconstructable_args = list(check.opt_tuple_param(reconstructable_args, "reconstructable_args"))
    reconstructable_kwargs = list(
        (
            [key, value]
            for key, value in check.opt_dict_param(
                reconstructable_kwargs, "reconstructable_kwargs", key_type=str
            ).items()
        )
    )

    reconstructor_pointer = ModuleCodePointer(
        reconstructor_module_name, reconstructor_function_name
    )

    pointer = CustomPointer(reconstructor_pointer, reconstructable_args, reconstructable_kwargs)

    pipeline_def = pipeline_def_from_pointer(pointer)

    return ReconstructablePipeline(
        repository=ReconstructableRepository(pointer),  # creates ephemeral repo
        pipeline_name=pipeline_def.name,
    )


build_reconstructable_pipeline = build_reconstructable_target


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
    from .pipeline_definition import PipelineDefinition
    from .repository_definition import RepositoryDefinition
    from .graph_definition import GraphDefinition

    if not isinstance(definition, (PipelineDefinition, RepositoryDefinition, GraphDefinition)):
        raise DagsterInvariantViolationError(
            (
                "Loadable attributes must be either a JobDefinition, GraphDefinition, PipelineDefinition, or a "
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

    from .pipeline_definition import PipelineDefinition
    from .repository_definition import RepositoryDefinition
    from .graph_definition import GraphDefinition

    if isinstance(
        target, (PipelineDefinition, RepositoryDefinition, GraphDefinition)
    ) or not callable(target):
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
    from .pipeline_definition import PipelineDefinition

    target = def_from_pointer(pointer)

    if isinstance(target, PipelineDefinition):
        return target

    raise DagsterInvariantViolationError(
        "CodePointer ({str}) must resolve to a JobDefinition (or PipelineDefinition for legacy code). "
        "Received a {type}".format(str=pointer.describe(), type=type(target))
    )


def repository_def_from_target_def(target):
    from .pipeline_definition import PipelineDefinition
    from .graph_definition import GraphDefinition
    from .repository_definition import CachingRepositoryData, RepositoryDefinition

    # special case - we can wrap a single pipeline in a repository
    if isinstance(target, (PipelineDefinition, GraphDefinition)):
        # consider including pipeline name in generated repo name
        return RepositoryDefinition(
            name=get_ephemeral_repository_name(target.name),
            repository_data=CachingRepositoryData.from_list([target]),
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
            "RepositoryDefinition, JobDefinition, or PipelineDefinition. "
            "Received a {type}".format(str=pointer.describe(), type=type(target))
        )
    return repo_def
