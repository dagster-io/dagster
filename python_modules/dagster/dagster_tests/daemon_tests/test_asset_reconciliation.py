import pytest

from dagster import SourceAsset, asset, repository
from dagster._daemon.asset_reconciliation import execute_asset_reconciliation_iteration


@repository
def repo1():
    @asset
    def asset1():
        ...

    return [asset1]


@repository
def repo2():
    asset1 = SourceAsset("asset1")

    @asset
    def asset2(asset1):
        ...

    return [asset1, asset2]


@pytest.fixture(name="instance_module_scoped", scope="module")
def instance_module_scoped_fixture():
    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster._core.launcher.sync_in_memory_run_launcher",
                "class": "SyncInMemoryRunLauncher",
            }
        }
    ) as instance:
        yield instance


@pytest.fixture(name="instance", scope="function")
def instance_fixture(instance_module_scoped):
    instance_module_scoped.wipe()
    instance_module_scoped.wipe_all_schedules()
    yield instance_module_scoped


def workspace_load_target(attribute=None):
    return InProcessTestWorkspaceLoadTarget(
        InProcessRepositoryLocationOrigin(
            loadable_target_origin=loadable_target_origin(attribute=attribute),
            location_name="test_location",
        )
    )


@pytest.fixture(name="workspace_context", scope="module")
def workspace_fixture(instance_module_scoped):
    with create_test_daemon_workspace_context(
        workspace_load_target=workspace_load_target(), instance=instance_module_scoped
    ) as workspace_context:
        yield workspace_context


@pytest.fixture(name="external_repo", scope="module")
def external_repo_fixture(workspace_context):
    return next(
        iter(workspace_context.create_request_context().get_workspace_snapshot().values())
    ).repository_location.get_repository("the_repo")


def loadable_target_origin(attribute=None):
    return LoadableTargetOrigin(
        executable_path=sys.executable,
        module_name="dagster_tests.daemon_tests.test_backfill",
        working_directory=os.getcwd(),
        attribute=attribute,
    )


def test_source_asset_matches_upstream_asset(instance, workspace_context, external_repo):
    """
    - The upstream asset should get updated and then the downstream asset should get updated
    - Diamond stuff
    """
    execute_asset_reconciliation_iteration(workspace_context)
