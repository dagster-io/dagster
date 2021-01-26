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
    namedtuple("_ReconstructableRepository", "pointer container_image")
):
    def __new__(
        cls,
        pointer,
        container_image=None,
    ):
        return super(ReconstructableRepository, cls).__new__(
            cls,
            pointer=check.inst_param(pointer, "pointer", CodePointer),
            container_image=check.opt_str_param(container_image, "container_image"),
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
            executable_path=sys.executable,
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
    function that returns a :py:class:`~dagster.PipelineDefinition`, or a function decorated with
    :py:func:`@pipeline <dagster.pipeline>`

    When your pipeline must cross process boundaries, e.g., for execution on multiple nodes or
    in different systems (like ``dagstermill``), Dagster must know how to reconstruct the pipeline
    on the other side of the process boundary.

    This function implements a very conservative strategy for reconstructing pipelines, so that
    its behavior is easy to predict, but as a consequence it is not able to reconstruct certain
    kinds of pipelines, such as those defined by lambdas, in nested scopes (e.g., dynamically
    within a method call), or in interactive environments such as the Python REPL or Jupyter
    notebooks.

    If you need to reconstruct pipelines constructed in these ways, you should use
    :py:func:`~dagster.core.definitions.reconstructable.build_reconstructable_pipeline` instead,
    which allows you to specify your own strategy for reconstructing a pipeline.

    Examples:

    .. code-block:: python

        from dagster import PipelineDefinition, pipeline, reconstructable

        @pipeline
        def foo_pipeline():
            ...

        reconstructable_foo_pipeline = reconstructable(foo_pipeline)


        def make_bar_pipeline():
            return PipelineDefinition(...)

        reconstructable_bar_pipeline = reconstructable(bar_pipeline)
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
            "decorated function defined at module scope instead, or use "
            "build_reconstructable_pipeline."
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
    except:  # pylint: disable=bare-except
        pass

    python_file = get_python_file_from_target(target)
    if not python_file:
        raise DagsterInvariantViolationError(
            "reconstructable() can not reconstruct pipelines defined in interactive environments "
            "like <stdin>, IPython, or Jupyter notebooks. "
            "Use a pipeline defined in a module or file instead, or "
            "use build_reconstructable_pipeline."
        )

    pointer = FileCodePointer(
        python_file=python_file, fn_name=target.__name__, working_directory=os.getcwd()
    )

    return bootstrap_standalone_recon_pipeline(pointer)


@experimental
def build_reconstructable_pipeline(
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

    from .pipeline import PipelineDefinition
    from .repository import RepositoryDefinition

    if isinstance(target, (PipelineDefinition, RepositoryDefinition)) or not callable(target):
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
