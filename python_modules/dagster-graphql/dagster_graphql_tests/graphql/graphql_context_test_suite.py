from abc import ABCMeta, abstractmethod
from contextlib import contextmanager

import pytest
import six
from dagster_graphql.implementation.context import (
    DagsterGraphQLContext,
    InProcessDagsterEnvironment,
)
from dagster_graphql.implementation.pipeline_execution_manager import (
    PipelineExecutionManager,
    SubprocessExecutionManager,
    SynchronousExecutionManager,
)

from dagster import check, file_relative_path, seven
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.storage.event_log import InMemoryEventLogStorage
from dagster.core.storage.local_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import InMemoryRunStorage


def get_main_recon_repo():
    return ReconstructableRepository.from_yaml(file_relative_path(__file__, 'repo.yaml'))


class GraphQLTestInstances:
    @staticmethod
    @contextmanager
    def in_memory_instance():
        with seven.TemporaryDirectory() as temp_dir:
            yield DagsterInstance(
                instance_type=InstanceType.EPHEMERAL,
                local_artifact_storage=LocalArtifactStorage(temp_dir),
                run_storage=InMemoryRunStorage(),
                event_storage=InMemoryEventLogStorage(),
                compute_log_manager=NoOpComputeLogManager(temp_dir),
            )

    @staticmethod
    @contextmanager
    def sqlite_instance():
        with seven.TemporaryDirectory() as temp_dir:
            instance = DagsterInstance.local_temp(
                temp_dir,
                overrides={
                    'scheduler': {
                        'module': 'dagster.utils.test',
                        'class': 'FilesystemTestScheduler',
                        'config': {'base_dir': temp_dir},
                    }
                },
            )
            yield instance


class GraphQLTestEnvironments:
    @staticmethod
    @contextmanager
    def user_code_in_host_process(recon_repo, execution_manager):
        check.inst_param(recon_repo, 'recon_repo', ReconstructableRepository)
        check.inst_param(execution_manager, 'execution_manager', PipelineExecutionManager)
        yield InProcessDagsterEnvironment(
            recon_repo=recon_repo, execution_manager=execution_manager
        )


class GraphQLTestExecutionManagers:
    @staticmethod
    @contextmanager
    def sync_execution_manager(instance):
        check.inst_param(instance, 'instance', DagsterInstance)
        yield SynchronousExecutionManager()

    @staticmethod
    @contextmanager
    def subprocess_execution_manager(instance):
        check.inst_param(instance, 'instance', DagsterInstance)
        subprocess_em = SubprocessExecutionManager(instance)
        try:
            yield subprocess_em
        finally:
            subprocess_em.join()


class Marks:
    # Instance type makes
    in_memory_instance = pytest.mark.in_memory_instance
    sqlite_instance = pytest.mark.sqlite_instance

    # Environment marks
    hosted_user_process_env = pytest.mark.hosted_user_process_env

    # Execution Manager marks (to be deleted post migration)
    in_process_start = pytest.mark.in_process_start
    subprocess_start = pytest.mark.subprocess_start

    # Common mark to all test suite tests
    graphql_context_test_suite = pytest.mark.graphql_context_test_suite


MARK_MAP = {
    GraphQLTestInstances.in_memory_instance: [Marks.in_memory_instance],
    GraphQLTestInstances.sqlite_instance: [Marks.sqlite_instance],
    GraphQLTestEnvironments.user_code_in_host_process: [Marks.hosted_user_process_env],
    GraphQLTestExecutionManagers.sync_execution_manager: [Marks.in_process_start],
    GraphQLTestExecutionManagers.subprocess_execution_manager: [Marks.subprocess_start],
}


def make_marks(mgrs):
    marks = []
    for mgr in mgrs:
        marks.extend(MARK_MAP.get(mgr, []))
    return marks


class GraphQLContextVariant:
    '''
    An instance of this class represents a context variant that will be run
    against *every* method in the test class, defined as a class
    created by inheriting from make_graphql_context_test_suite.

    It comes with a number of static methods with prebuilt context variants.
    e.g. in_memory_in_process_start

    One can also make bespoke context variants, provided you configure it properly
    with context managers that produce its members.

    Args:

    instance_mgr (Callable): This callable must be a contextmanager It takes
    zero arguments and yields a DagsterInstance

    See GraphQLTestInstances for examples

    environment_mgr (Callable): This callable must be a context manager. It
    takes a ReconstructableRepo and a PipelineExecutionManager and yields
    a DagsterEnvironment.

    See GraphQLTestEnvironments for examples

    em_mgr (Callable): This callable must be a context manager. It takes
    a DagsterInstance and must yield a PipelineExecutionManager

    See GraphQLTestExecutionManagers for examples

    test_id [Optional] (str): This assigns a test_id to test parameterized with this variant.
    This is highly convenient for running a particular variant across
    the entire test suite, without running all the other variants.

    e.g.
    pytest python_modules/dagster-graphql/dagster_graphql_tests/ -s -k in_memory_in_process_start

    Will run all tests that use the in_memory_in_process_start, which will get a lot
    of code coverage while being very fast to run.

    marks [Optional] (List[pytest.mark]): Marks assigned to this variant.

    Typically these are not specified on a per-variant basis and will be autoassigned
    if resources are used from GraphQLTestInstances, GraphQLTestEnvironments,
    and GraphQLTestExecutionManagers.

    See the MARK_MAP to see the assignments

    So, for example, if one wanted to run all the tests in the test suite against the
    sqlite Dagster Instance:

    pytest python_modules/dagster-graphql/dagster_graphql_tests/ -m sqlite

    Users can also override this automatic assignment of marks by providing them
    directly to the GraphQLContextVariant.

    All tests managed by this system are marked with "graphql_context_test_suite".
    '''

    def __init__(self, instance_mgr, environment_mgr, em_mgr, test_id=None, marks=None):
        self.instance_mgr = check.callable_param(instance_mgr, 'instance_mgr')
        self.environment_mgr = check.callable_param(environment_mgr, 'environment_mgr')
        self.em_mgr = check.callable_param(em_mgr, 'em_mgr')
        self.test_id = check.opt_str_param(test_id, 'test_id')
        self.marks = (
            make_marks([instance_mgr, environment_mgr, em_mgr])
            if marks is None
            else check.list_param(marks, 'marks')
        )

    @staticmethod
    def in_memory_in_process_start():
        return GraphQLContextVariant(
            GraphQLTestInstances.in_memory_instance,
            GraphQLTestEnvironments.user_code_in_host_process,
            GraphQLTestExecutionManagers.sync_execution_manager,
            test_id='in_memory_in_process_start',
        )

    @staticmethod
    def sqlite_in_process_start():
        return GraphQLContextVariant(
            GraphQLTestInstances.sqlite_instance,
            GraphQLTestEnvironments.user_code_in_host_process,
            GraphQLTestExecutionManagers.sync_execution_manager,
            test_id='sqlite_in_process_start',
        )

    @staticmethod
    def sqlite_subprocess_start():
        return GraphQLContextVariant(
            GraphQLTestInstances.sqlite_instance,
            GraphQLTestEnvironments.user_code_in_host_process,
            GraphQLTestExecutionManagers.sync_execution_manager,
            test_id='sqlite_subprocess_start',
        )

    @staticmethod
    def all_legacy_variants():
        return [
            GraphQLContextVariant.in_memory_in_process_start(),
            GraphQLContextVariant.sqlite_in_process_start(),
            GraphQLContextVariant.sqlite_subprocess_start(),
        ]


@contextmanager
def manage_graphql_context(instance_mgr, environment_mgr, em_mgr, recon_repo=None):
    recon_repo = recon_repo if recon_repo else get_main_recon_repo()
    with instance_mgr() as instance:
        with em_mgr(instance) as execution_manager:
            with environment_mgr(recon_repo, execution_manager) as environment:
                yield DagsterGraphQLContext(instance=instance, environments=[environment])


class _GraphQLContextTestSuite(six.with_metaclass(ABCMeta)):
    @abstractmethod
    def yield_graphql_context(self, request):
        pass

    @abstractmethod
    def recon_repo(self):
        pass

    @contextmanager
    def graphql_context_for_request(self, request):
        check.param_invariant(
            isinstance(request.param, GraphQLContextVariant),
            'request',
            'params in fixture must be List[GraphQLContextVariant]',
        )
        context_variant = request.param
        with manage_graphql_context(
            context_variant.instance_mgr,
            context_variant.environment_mgr,
            context_variant.em_mgr,
            self.recon_repo(),
        ) as graphql_context:
            yield graphql_context


def graphql_context_variants_fixture(context_variants):
    check.list_param(context_variants, 'context_variants', of_type=GraphQLContextVariant)

    def _wrap(fn):
        return pytest.fixture(
            name='graphql_context',
            params=[
                pytest.param(
                    context_variant,
                    id=context_variant.test_id,
                    marks=context_variant.marks + [Marks.graphql_context_test_suite],
                )
                for context_variant in context_variants
            ],
        )(fn)

    return _wrap


def make_graphql_context_test_suite(context_variants, recon_repo=None):
    '''
    Arguments:

    runs (List[GraphQLContextVariant]): List of runs to run per test in this class.
    recon_repo (ReconstructableRepository): Repository to run against. Defaults
    to "define_repository" in setup.py

    This is the base class factory for test suites in the dagster-graphql test.

    The goal of this suite is to make it straightforward to run tests
    against multiple graphql_contexts, have a coherent lifecycle for those
    contexts.

    GraphQLContextVariant has a number of static methods to provide common run configurations
    as well as common groups of run configuration

    One can also make bespoke GraphQLContextVariants which specific implementations
    of DagsterInstance, DagsterEnvironment, and so forth. See that class
    for more details.

Example:

class TestAThing(
    make_graphql_context_test_suite(
        context_variants=[GraphQLContextVariant.in_memory_in_process_start()]
    )
):
    def test_graphql_context_exists(self, graphql_context):
        assert graphql_context
    '''
    check.list_param(context_variants, 'context_variants', of_type=GraphQLContextVariant)
    recon_repo = check.inst_param(
        recon_repo if recon_repo else get_main_recon_repo(), 'recon_repo', ReconstructableRepository
    )

    class _SpecificTestSuiteBase(_GraphQLContextTestSuite):
        @graphql_context_variants_fixture(context_variants=context_variants)
        def yield_graphql_context(self, request):
            with self.graphql_context_for_request(request) as graphql_context:
                yield graphql_context

        def recon_repo(self):
            return recon_repo

    return _SpecificTestSuiteBase
