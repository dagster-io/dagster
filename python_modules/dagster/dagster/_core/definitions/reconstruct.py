from __future__ import annotations

import inspect
import os
import sys
from functools import lru_cache
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    overload,
)

from typing_extensions import TypeAlias

import dagster._check as check
import dagster._seven as seven
from dagster._annotations import experimental
from dagster._core.code_pointer import (
    CodePointer,
    CustomPointer,
    FileCodePointer,
    ModuleCodePointer,
    get_python_file_from_target,
)
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.origin import (
    DEFAULT_DAGSTER_ENTRY_POINT,
    PipelinePythonOrigin,
    RepositoryPythonOrigin,
)
from dagster._core.selector import parse_solid_selection
from dagster._serdes import pack_value, unpack_value, whitelist_for_serdes
from dagster._utils import frozenlist, make_readonly_value

from .events import AssetKey
from .pipeline_base import IPipeline

if TYPE_CHECKING:
    from dagster._core.definitions.job_definition import JobDefinition
    from dagster._core.definitions.repository_definition import (
        PendingRepositoryDefinition,
        RepositoryLoadData,
    )

    from .asset_group import AssetGroup
    from .graph_definition import GraphDefinition
    from .pipeline_definition import PipelineDefinition
    from .repository_definition import RepositoryDefinition


def get_ephemeral_repository_name(pipeline_name: str) -> str:
    check.str_param(pipeline_name, "pipeline_name")
    return "__repository__{pipeline_name}".format(pipeline_name=pipeline_name)


@whitelist_for_serdes
class ReconstructableRepository(
    NamedTuple(
        "_ReconstructableRepository",
        [
            ("pointer", CodePointer),
            ("container_image", Optional[str]),
            ("executable_path", Optional[str]),
            ("entry_point", Sequence[str]),
            ("container_context", Optional[Mapping[str, Any]]),
            ("repository_load_data", Optional["RepositoryLoadData"]),
        ],
    )
):
    def __new__(
        cls,
        pointer: CodePointer,
        container_image: Optional[str] = None,
        executable_path: Optional[str] = None,
        entry_point: Optional[Sequence[str]] = None,
        container_context: Optional[Mapping[str, Any]] = None,
        repository_load_data: Optional[RepositoryLoadData] = None,
    ):
        from dagster._core.definitions.repository_definition import RepositoryLoadData

        return super(ReconstructableRepository, cls).__new__(
            cls,
            pointer=check.inst_param(pointer, "pointer", CodePointer),
            container_image=check.opt_str_param(container_image, "container_image"),
            executable_path=check.opt_str_param(executable_path, "executable_path"),
            entry_point=(
                frozenlist(check.sequence_param(entry_point, "entry_point", of_type=str))
                if entry_point is not None
                else DEFAULT_DAGSTER_ENTRY_POINT
            ),
            container_context=(
                make_readonly_value(check.mapping_param(container_context, "container_context"))
                if container_context is not None
                else None
            ),
            repository_load_data=check.opt_inst_param(
                repository_load_data, "repository_load_data", RepositoryLoadData
            ),
        )

    def with_repository_load_data(
        self, metadata: Optional["RepositoryLoadData"]
    ) -> "ReconstructableRepository":
        return self._replace(repository_load_data=metadata)

    def get_definition(self) -> "RepositoryDefinition":
        return repository_def_from_pointer(self.pointer, self.repository_load_data)

    def get_reconstructable_pipeline(self, name: str) -> ReconstructablePipeline:
        return ReconstructablePipeline(self, name)

    @classmethod
    def for_file(
        cls,
        file: str,
        fn_name: str,
        working_directory: Optional[str] = None,
        container_image: Optional[str] = None,
        container_context: Optional[Mapping[str, Any]] = None,
    ) -> ReconstructableRepository:
        if not working_directory:
            working_directory = os.getcwd()
        return cls(
            FileCodePointer(file, fn_name, working_directory),
            container_image=container_image,
            container_context=container_context,
        )

    @classmethod
    def for_module(
        cls,
        module: str,
        fn_name: str,
        working_directory: Optional[str] = None,
        container_image: Optional[str] = None,
        container_context: Optional[Mapping[str, Any]] = None,
    ) -> ReconstructableRepository:
        return cls(
            ModuleCodePointer(module, fn_name, working_directory),
            container_image=container_image,
            container_context=container_context,
        )

    def get_python_origin(self) -> RepositoryPythonOrigin:
        return RepositoryPythonOrigin(
            executable_path=self.executable_path if self.executable_path else sys.executable,
            code_pointer=self.pointer,
            container_image=self.container_image,
            entry_point=self.entry_point,
            container_context=self.container_context,
        )

    def get_python_origin_id(self) -> str:
        return self.get_python_origin().get_id()


@whitelist_for_serdes
class ReconstructablePipeline(
    NamedTuple(
        "_ReconstructablePipeline",
        [
            ("repository", ReconstructableRepository),
            ("pipeline_name", str),
            ("solid_selection_str", Optional[str]),
            ("solids_to_execute", Optional[AbstractSet[str]]),
            ("asset_selection", Optional[AbstractSet[AssetKey]]),
        ],
    ),
    IPipeline,
):
    """Defines a reconstructable pipeline. When your pipeline/job must cross process boundaries,
    Dagster must know how to reconstruct the pipeline/job on the other side of the process boundary.

    Args:
        repository (ReconstructableRepository): The reconstructable representation of the repository
            the pipeline/job belongs to.
        pipeline_name (str): The name of the pipeline/job.
        solid_selection_str (Optional[str]): The string value of a comma separated list of user-input
            solid/op selection. None if no selection is specified, i.e. the entire pipeline/job will
            be run.
        solids_to_execute (Optional[FrozenSet[str]]): A set of solid/op names to execute. None if no selection
            is specified, i.e. the entire pipeline/job will be run.
        asset_selection (Optional[FrozenSet[AssetKey]]) A set of assets to execute. None if no selection
            is specified, i.e. the entire job will be run.
    """

    def __new__(
        cls,
        repository: ReconstructableRepository,
        pipeline_name: str,
        solid_selection_str: Optional[str] = None,
        solids_to_execute: Optional[AbstractSet[str]] = None,
        asset_selection: Optional[AbstractSet[AssetKey]] = None,
    ):
        check.opt_set_param(solids_to_execute, "solids_to_execute", of_type=str)
        check.opt_set_param(asset_selection, "asset_selection", AssetKey)
        return super(ReconstructablePipeline, cls).__new__(
            cls,
            repository=check.inst_param(repository, "repository", ReconstructableRepository),
            pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
            solid_selection_str=check.opt_str_param(solid_selection_str, "solid_selection_str"),
            solids_to_execute=solids_to_execute,
            asset_selection=asset_selection,
        )

    def with_repository_load_data(
        self, metadata: Optional["RepositoryLoadData"]
    ) -> ReconstructablePipeline:
        return self._replace(repository=self.repository.with_repository_load_data(metadata))

    @property
    def solid_selection(self) -> Optional[Sequence[str]]:
        return seven.json.loads(self.solid_selection_str) if self.solid_selection_str else None

    # Keep the most recent 1 definition (globally since this is a NamedTuple method)
    # This allows repeated calls to get_definition in execution paths to not reload the job
    @lru_cache(maxsize=1)  # type: ignore
    def get_definition(self) -> Union[JobDefinition, "PipelineDefinition"]:
        return self.repository.get_definition().get_maybe_subset_job_def(
            self.pipeline_name,
            self.solid_selection,
            self.asset_selection,
            self.solids_to_execute,
        )

    def get_reconstructable_repository(self) -> ReconstructableRepository:
        return self.repository

    def _subset_for_execution(
        self,
        solids_to_execute: Optional[AbstractSet[str]],
        solid_selection: Optional[Sequence[str]],
        asset_selection: Optional[AbstractSet[AssetKey]],
    ) -> "ReconstructablePipeline":
        # no selection
        if solid_selection is None and solids_to_execute is None and asset_selection is None:
            return ReconstructablePipeline(
                repository=self.repository,
                pipeline_name=self.pipeline_name,
            )

        from dagster._core.definitions import JobDefinition, PipelineDefinition

        pipeline_def = self.get_definition()
        if isinstance(pipeline_def, JobDefinition):
            # jobs use pre-resolved selection
            # when subselecting a job
            # * job subselection depend on solid_selection rather than solids_to_execute
            # * we'll resolve the op selection later in the stack
            if solid_selection is None:
                # when the pre-resolution info is unavailable (e.g. subset from existing run),
                # we need to fill the solid_selection in order to pass the value down to deeper stack.
                solid_selection = list(solids_to_execute) if solids_to_execute else None
            return ReconstructablePipeline(
                repository=self.repository,
                pipeline_name=self.pipeline_name,
                solid_selection_str=seven.json.dumps(solid_selection) if solid_selection else None,
                solids_to_execute=None,
                asset_selection=asset_selection,
            )
        elif isinstance(pipeline_def, PipelineDefinition):  # type: ignore
            # when subselecting a pipeline
            # * pipeline subselection depend on solids_to_excute rather than solid_selection
            # * we resolve a list of solid selection queries to a frozenset of qualified solid names
            #   e.g. ['foo_solid+'] to {'foo_solid', 'bar_solid'}
            if solid_selection and solids_to_execute is None:
                # when post-resolution query is unavailable, resolve the query
                solids_to_execute = parse_solid_selection(pipeline_def, solid_selection)
            return ReconstructablePipeline(
                repository=self.repository,
                pipeline_name=self.pipeline_name,
                solid_selection_str=seven.json.dumps(solid_selection) if solid_selection else None,
                solids_to_execute=frozenset(solids_to_execute) if solids_to_execute else None,
            )
        else:
            raise Exception(f"Unexpected pipeline/job type {pipeline_def.__class__.__name__}")

    def subset_for_execution(
        self,
        solid_selection: Optional[Sequence[str]] = None,
        asset_selection: Optional[AbstractSet[AssetKey]] = None,
    ) -> "ReconstructablePipeline":
        # take a list of unresolved selection queries
        check.opt_sequence_param(solid_selection, "solid_selection", of_type=str)
        check.opt_set_param(asset_selection, "asset_selection", of_type=AssetKey)

        check.invariant(
            not (solid_selection and asset_selection),
            "solid_selection and asset_selection cannot both be provided as arguments",
        )

        return self._subset_for_execution(
            solids_to_execute=None, solid_selection=solid_selection, asset_selection=asset_selection
        )

    def subset_for_execution_from_existing_pipeline(
        self,
        solids_to_execute: Optional[AbstractSet[str]] = None,
        asset_selection: Optional[AbstractSet[AssetKey]] = None,
    ) -> ReconstructablePipeline:
        # take a frozenset of resolved solid names from an existing pipeline
        # so there's no need to parse the selection

        check.invariant(
            not (solids_to_execute and asset_selection),
            "solids_to_execute and asset_selection cannot both be provided as arguments",
        )

        check.opt_set_param(solids_to_execute, "solids_to_execute", of_type=str)
        check.opt_set_param(asset_selection, "asset_selection", of_type=AssetKey)

        return self._subset_for_execution(
            solids_to_execute=solids_to_execute,
            solid_selection=None,
            asset_selection=asset_selection,
        )

    def describe(self) -> str:
        return '"{name}" in repository ({repo})'.format(
            repo=self.repository.pointer.describe, name=self.pipeline_name
        )

    @staticmethod
    def for_file(python_file: str, fn_name: str) -> ReconstructablePipeline:
        return bootstrap_standalone_recon_pipeline(
            FileCodePointer(python_file, fn_name, os.getcwd())
        )

    @staticmethod
    def for_module(module: str, fn_name: str) -> ReconstructablePipeline:
        return bootstrap_standalone_recon_pipeline(ModuleCodePointer(module, fn_name, os.getcwd()))

    def to_dict(self) -> Mapping[str, object]:
        return pack_value(self)

    @staticmethod
    def from_dict(val: Mapping[str, object]) -> ReconstructablePipeline:
        check.mapping_param(val, "val")

        inst = unpack_value(val)
        check.invariant(
            isinstance(inst, ReconstructablePipeline),
            "Deserialized object is not instance of ReconstructablePipeline, got {type}".format(
                type=type(inst)
            ),
        )
        return inst

    def get_python_origin(self) -> PipelinePythonOrigin:
        return PipelinePythonOrigin(self.pipeline_name, self.repository.get_python_origin())

    def get_python_origin_id(self) -> str:
        return self.get_python_origin().get_id()

    def get_module(self) -> Optional[str]:
        """Return the module the pipeline is found in, the origin is a module code pointer."""
        pointer = self.get_python_origin().get_repo_pointer()
        if isinstance(pointer, ModuleCodePointer):
            return pointer.module

        return None


ReconstructableJob = ReconstructablePipeline


def reconstructable(target: Callable[..., "PipelineDefinition"]) -> ReconstructablePipeline:
    """
    Create a :py:class:`~dagster._core.definitions.reconstructable.ReconstructablePipeline` from a
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
    :py:func:`~dagster.reconstructable.build_reconstructable_job` instead, which allows you to
    specify your own reconstruction strategy.

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
    from dagster._core.definitions import JobDefinition, PipelineDefinition

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
            "build_reconstructable_job."
        )

    if seven.qualname_differs(target):
        raise DagsterInvariantViolationError(
            'Reconstructable target "{target.__name__}" has a different '
            '__qualname__ "{target.__qualname__}" indicating it is not '
            "defined at module scope. Use a function or decorated function "
            "defined at module scope instead, or use build_reconstructable_job.".format(
                target=target
            )
        )

    try:
        if (
            hasattr(target, "__module__")
            and hasattr(target, "__name__")
            and getattr(inspect.getmodule(target), "__name__", None) != "__main__"
        ):
            return ReconstructablePipeline.for_module(target.__module__, target.__name__)
    except:
        pass

    python_file = get_python_file_from_target(target)
    if not python_file:
        raise DagsterInvariantViolationError(
            "reconstructable() can not reconstruct jobs or pipelines defined in interactive "
            "environments like <stdin>, IPython, or Jupyter notebooks. "
            "Use a pipeline defined in a module or file instead, or use build_reconstructable_job."
        )

    pointer = FileCodePointer(
        python_file=python_file, fn_name=target.__name__, working_directory=os.getcwd()
    )

    return bootstrap_standalone_recon_pipeline(pointer)


@experimental
def build_reconstructable_job(
    reconstructor_module_name: str,
    reconstructor_function_name: str,
    reconstructable_args: Optional[Tuple[object]] = None,
    reconstructable_kwargs: Optional[Mapping[str, object]] = None,
    reconstructor_working_directory: Optional[str] = None,
) -> ReconstructablePipeline:
    """
    Create a :py:class:`dagster._core.definitions.reconstructable.ReconstructablePipeline`.

    When your job must cross process boundaries, e.g., for execution on multiple nodes or in
    different systems (like ``dagstermill``), Dagster must know how to reconstruct the job
    on the other side of the process boundary.

    This function allows you to use the strategy of your choice for reconstructing jobs, so
    that you can reconstruct certain kinds of jobs that are not supported by
    :py:func:`~dagster.reconstructable`, such as those defined by lambdas, in nested scopes (e.g.,
    dynamically within a method call), or in interactive environments such as the Python REPL or
    Jupyter notebooks.

    If you need to reconstruct jobs constructed in these ways, use this function instead of
    :py:func:`~dagster.reconstructable`.

    Args:
        reconstructor_module_name (str): The name of the module containing the function to use to
            reconstruct the job.
        reconstructor_function_name (str): The name of the function to use to reconstruct the
            job.
        reconstructable_args (Tuple): Args to the function to use to reconstruct the job.
            Values of the tuple must be JSON serializable.
        reconstructable_kwargs (Dict[str, Any]): Kwargs to the function to use to reconstruct the
            job. Values of the dict must be JSON serializable.

    Examples:
        .. code-block:: python

            # module: mymodule

            from dagster import JobDefinition, job, build_reconstructable_job

            class JobFactory:
                def make_job(*args, **kwargs):

                    @job
                    def _job(...):
                        ...

                    return _job

            def reconstruct_job(*args):
                factory = JobFactory()
                return factory.make_job(*args)

            factory = JobFactory()

            foo_job_args = (...,...)

            foo_job_kwargs = {...:...}

            foo_job = factory.make_job(*foo_job_args, **foo_job_kwargs)

            reconstructable_foo_job = build_reconstructable_job(
                'mymodule',
                'reconstruct_job',
                foo_job_args,
                foo_job_kwargs,
            )
    """
    check.str_param(reconstructor_module_name, "reconstructor_module_name")
    check.str_param(reconstructor_function_name, "reconstructor_function_name")
    check.opt_str_param(
        reconstructor_working_directory, "reconstructor_working_directory", os.getcwd()
    )

    _reconstructable_args: List[object] = list(
        check.opt_tuple_param(reconstructable_args, "reconstructable_args")
    )
    _reconstructable_kwargs: List[List[Union[str, object]]] = list(
        (
            [key, value]
            for key, value in check.opt_mapping_param(
                reconstructable_kwargs, "reconstructable_kwargs", key_type=str
            ).items()
        )
    )

    reconstructor_pointer = ModuleCodePointer(
        reconstructor_module_name,
        reconstructor_function_name,
        working_directory=reconstructor_working_directory,
    )

    pointer = CustomPointer(reconstructor_pointer, _reconstructable_args, _reconstructable_kwargs)

    pipeline_def = pipeline_def_from_pointer(pointer)

    return ReconstructablePipeline(
        repository=ReconstructableRepository(pointer),  # creates ephemeral repo
        pipeline_name=pipeline_def.name,
    )


# back compat, in case users have imported these directly
build_reconstructable_pipeline = build_reconstructable_job
build_reconstructable_target = build_reconstructable_job


def bootstrap_standalone_recon_pipeline(pointer: CodePointer) -> ReconstructablePipeline:
    # So this actually straps the the pipeline for the sole
    # purpose of getting the pipeline name. If we changed ReconstructablePipeline
    # to get the pipeline on demand in order to get name, we could avoid this.
    pipeline_def = pipeline_def_from_pointer(pointer)
    return ReconstructablePipeline(
        repository=ReconstructableRepository(pointer),  # creates ephemeral repo
        pipeline_name=pipeline_def.name,
    )


LoadableDefinition: TypeAlias = Union[
    "PipelineDefinition",
    "RepositoryDefinition",
    "PendingRepositoryDefinition",
    "GraphDefinition",
    "AssetGroup",
]

T_LoadableDefinition = TypeVar("T_LoadableDefinition", bound=LoadableDefinition)


def _check_is_loadable(definition: T_LoadableDefinition) -> T_LoadableDefinition:
    from dagster._core.definitions import AssetGroup

    from .definitions_class import Definitions
    from .graph_definition import GraphDefinition
    from .pipeline_definition import PipelineDefinition
    from .repository_definition import PendingRepositoryDefinition, RepositoryDefinition

    if not isinstance(
        definition,
        (
            PipelineDefinition,
            RepositoryDefinition,
            PendingRepositoryDefinition,
            GraphDefinition,
            AssetGroup,
            Definitions,
        ),
    ):
        raise DagsterInvariantViolationError(
            "Loadable attributes must be either a JobDefinition, GraphDefinition, "
            f"PipelineDefinition, AssetGroup, or RepositoryDefinition. Got {repr(definition)}."
        )
    return definition  # type: ignore


def load_def_in_module(
    module_name: str, attribute: str, working_directory: Optional[str]
) -> LoadableDefinition:
    return def_from_pointer(CodePointer.from_module(module_name, attribute, working_directory))


def load_def_in_package(
    package_name: str, attribute: str, working_directory: Optional[str]
) -> LoadableDefinition:
    return def_from_pointer(
        CodePointer.from_python_package(package_name, attribute, working_directory)
    )


def load_def_in_python_file(
    python_file: str, attribute: str, working_directory: Optional[str]
) -> LoadableDefinition:
    return def_from_pointer(CodePointer.from_python_file(python_file, attribute, working_directory))


def def_from_pointer(
    pointer: CodePointer,
) -> LoadableDefinition:
    target = pointer.load_target()

    from dagster._core.definitions import AssetGroup

    from .graph_definition import GraphDefinition
    from .pipeline_definition import PipelineDefinition
    from .repository_definition import PendingRepositoryDefinition, RepositoryDefinition

    if isinstance(
        target,
        (
            AssetGroup,
            GraphDefinition,
            PipelineDefinition,
            PendingRepositoryDefinition,
            RepositoryDefinition,
        ),
    ) or not callable(target):
        return _check_is_loadable(target)  # type: ignore

    # if its a function invoke it - otherwise we are pointing to a
    # artifact in module scope, likely decorator output

    if seven.get_arg_names(target):
        raise DagsterInvariantViolationError(
            "Error invoking function at {target} with no arguments. "
            "Reconstructable target must be callable with no arguments".format(
                target=pointer.describe()
            )
        )

    return _check_is_loadable(target())  # type: ignore


def pipeline_def_from_pointer(pointer: CodePointer) -> "PipelineDefinition":
    from .pipeline_definition import PipelineDefinition

    target = def_from_pointer(pointer)

    if isinstance(target, PipelineDefinition):
        return target

    raise DagsterInvariantViolationError(
        "CodePointer ({str}) must resolve to a JobDefinition (or PipelineDefinition for legacy"
        " code). Received a {type}".format(str=pointer.describe(), type=type(target))
    )


@overload
# NOTE: mypy can't handle these overloads but pyright can
def repository_def_from_target_def(  # type: ignore
    target: Union["RepositoryDefinition", "PipelineDefinition", "GraphDefinition", "AssetGroup"],
    repository_load_data: Optional["RepositoryLoadData"] = None,
) -> "RepositoryDefinition":
    ...


@overload
def repository_def_from_target_def(
    target: object, repository_load_data: Optional["RepositoryLoadData"] = None
) -> None:
    ...


def repository_def_from_target_def(
    target: object, repository_load_data: Optional["RepositoryLoadData"] = None
) -> Optional["RepositoryDefinition"]:
    from dagster._core.definitions import AssetGroup

    from .definitions_class import Definitions
    from .graph_definition import GraphDefinition
    from .pipeline_definition import PipelineDefinition
    from .repository_definition import (
        SINGLETON_REPOSITORY_NAME,
        CachingRepositoryData,
        PendingRepositoryDefinition,
        RepositoryDefinition,
    )

    if isinstance(target, Definitions):
        # reassign to handle both repository and pending repo case
        target = target.get_inner_repository_for_loading_process()

    # special case - we can wrap a single pipeline in a repository
    if isinstance(target, (PipelineDefinition, GraphDefinition)):
        # consider including pipeline name in generated repo name
        return RepositoryDefinition(
            name=get_ephemeral_repository_name(target.name),
            repository_data=CachingRepositoryData.from_list([target]),
        )
    elif isinstance(target, AssetGroup):
        return RepositoryDefinition(
            name=SINGLETON_REPOSITORY_NAME,
            repository_data=CachingRepositoryData.from_list([target]),
        )
    elif isinstance(target, RepositoryDefinition):
        return target
    elif isinstance(target, PendingRepositoryDefinition):
        # must load repository from scratch
        if repository_load_data is None:
            return target.compute_repository_definition()
        # can use the cached data to more efficiently load data
        return target.reconstruct_repository_definition(repository_load_data)
    else:
        return None


def repository_def_from_pointer(
    pointer: CodePointer, repository_load_data: Optional["RepositoryLoadData"] = None
) -> "RepositoryDefinition":
    target = def_from_pointer(pointer)
    repo_def = repository_def_from_target_def(target, repository_load_data)
    if not repo_def:
        raise DagsterInvariantViolationError(
            "CodePointer ({str}) must resolve to a "
            "RepositoryDefinition, JobDefinition, or PipelineDefinition. "
            "Received a {type}".format(str=pointer.describe(), type=type(target))
        )
    return repo_def
