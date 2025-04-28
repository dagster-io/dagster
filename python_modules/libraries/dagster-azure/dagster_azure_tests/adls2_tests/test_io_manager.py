from uuid import uuid4

import pytest
from azure.storage.filedatalake import DataLakeLeaseClient
from dagster import (
    AssetIn,
    AssetKey,
    DagsterInstance,
    DagsterRun,
    DynamicOut,
    DynamicOutput,
    GraphOut,
    In,
    Int,
    Out,
    asset,
    build_input_context,
    build_output_context,
    graph,
    op,
    resource,
)
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.job_base import InMemoryJob
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster._core.events import DagsterEventType
from dagster._core.execution.api import create_execution_plan, execute_plan
from dagster._core.system_config.objects import ResolvedRunConfig
from dagster._core.types.dagster_type import resolve_dagster_type
from dagster._core.utils import make_new_run_id
from dagster_azure.adls2 import create_adls2_client
from dagster_azure.adls2.io_manager import PickledObjectADLS2IOManager, adls2_pickle_io_manager
from dagster_azure.adls2.resources import adls2_resource
from dagster_azure.blob import create_blob_client
from dagster_azure.fakes import fake_adls2_resource
from upath import UPath


def fake_io_manager_factory(io_manager):
    @resource
    def fake_io_manager(_):
        return io_manager

    return fake_io_manager


def get_step_output(step_events, step_key, output_name="result"):
    for step_event in step_events:
        if (
            step_event.event_type == DagsterEventType.STEP_OUTPUT
            and step_event.step_key == step_key
            and step_event.step_output_data.output_name == output_name
        ):
            return step_event
    return None


def define_inty_job(adls_io_resource=adls2_resource):
    @op(out=Out(int))
    def return_one():
        return 1

    @op(
        ins={"num": In(Int)},
        out=DynamicOut(Int),
    )
    def add_one(num):
        yield DynamicOutput(num + 1, "foo")
        yield DynamicOutput(num + 1, "bar")

    @graph
    def basic_external_plan_execution():
        add_one(return_one())

    return basic_external_plan_execution.to_job(
        resource_defs={"io_manager": adls2_pickle_io_manager, "adls2": adls_io_resource}
    )


@pytest.mark.nettest
@pytest.mark.skip(
    "Blob this depends on does not exist. See"
    " https://linear.app/elementl/issue/CORE-83/test-adls2-pickle-io-manager-deletes-recursively-disabled-reenable-it"
)
def test_adls2_pickle_io_manager_deletes_recursively(storage_account, file_system, credential):
    job = define_inty_job()

    run_config = {
        "resources": {
            "io_manager": {"config": {"adls2_file_system": file_system}},
            "adls2": {
                "config": {
                    "storage_account": storage_account,
                    "credential": {"key": credential},
                }
            },
        }
    }

    run_id = make_new_run_id()

    resolved_run_config = ResolvedRunConfig.build(job, run_config=run_config)
    execution_plan = create_execution_plan(job, run_config)

    assert execution_plan.get_step_by_key("return_one")

    step_keys = ["return_one"]
    instance = DagsterInstance.ephemeral()
    dagster_run = DagsterRun(job_name=job.name, run_id=run_id, run_config=run_config)

    return_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(step_keys, job, resolved_run_config),
            job=InMemoryJob(job),
            run_config=run_config,
            dagster_run=dagster_run,
            instance=instance,
        )
    )

    assert get_step_output(return_one_step_events, "return_one")
    context = build_input_context(
        upstream_output=build_output_context(
            step_key="return_one",
            name="result",
            run_id=run_id,
            dagster_type=resolve_dagster_type(int),
        ),
        dagster_type=resolve_dagster_type(int),
    )

    io_manager = PickledObjectADLS2IOManager(
        file_system=file_system,
        adls2_client=create_adls2_client(storage_account, credential),
        blob_client=create_blob_client(storage_account, credential),
        lease_client_constructor=DataLakeLeaseClient,
    )
    assert io_manager.load_input(context) == 1

    # Verify that when the IO manager needs to delete recursively, it is able to do so,
    # by removing the whole path for the run
    recursive_path = UPath(
        io_manager.prefix,
        "storage",
        run_id,
    )
    io_manager.unlink(recursive_path)


@pytest.mark.nettest
@pytest.mark.skip(
    "Blob this depends on does not exist. See"
    " https://linear.app/elementl/issue/CORE-83/test-adls2-pickle-io-manager-deletes-recursively-disabled-reenable-it"
)
def test_adls2_pickle_io_manager_execution(storage_account, file_system, credential):
    job = define_inty_job()

    run_config = {
        "resources": {
            "io_manager": {"config": {"adls2_file_system": file_system}},
            "adls2": {
                "config": {
                    "storage_account": storage_account,
                    "credential": {"key": credential},
                }
            },
        }
    }

    run_id = make_new_run_id()

    resolved_run_config = ResolvedRunConfig.build(job, run_config=run_config)
    execution_plan = create_execution_plan(job, run_config)

    assert execution_plan.get_step_by_key("return_one")

    step_keys = ["return_one"]
    instance = DagsterInstance.ephemeral()
    dagster_run = DagsterRun(job_name=job.name, run_id=run_id, run_config=run_config)

    return_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(step_keys, job, resolved_run_config),
            job=InMemoryJob(job),
            run_config=run_config,
            dagster_run=dagster_run,
            instance=instance,
        )
    )

    assert get_step_output(return_one_step_events, "return_one")
    context = build_input_context(
        upstream_output=build_output_context(
            step_key="return_one",
            name="result",
            run_id=run_id,
            dagster_type=resolve_dagster_type(int),
        ),
        dagster_type=resolve_dagster_type(int),
    )

    io_manager = PickledObjectADLS2IOManager(
        file_system=file_system,
        adls2_client=create_adls2_client(storage_account, credential),
        blob_client=create_blob_client(storage_account, credential),
        lease_client_constructor=DataLakeLeaseClient,
    )
    assert io_manager.load_input(context) == 1

    add_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(["add_one"], job, resolved_run_config),
            job=InMemoryJob(job),
            dagster_run=dagster_run,
            run_config=run_config,
            instance=instance,
        )
    )

    context = build_input_context(
        upstream_output=build_output_context(
            step_key="add_one",
            name="result",
            run_id=run_id,
            mapping_key="foo",
            dagster_type=resolve_dagster_type(int),
        ),
        dagster_type=resolve_dagster_type(int),
    )

    assert get_step_output(add_one_step_events, "add_one")
    assert io_manager.load_input(context) == 2


@pytest.mark.skip(
    "Blob this depends on does not exist. See"
    " https://linear.app/elementl/issue/CORE-83/test-adls2-pickle-io-manager-deletes-recursively-disabled-reenable-it"
)
def test_asset_io_manager(storage_account, file_system, credential):
    # if you add new assets to this test, make sure that the output names include _id so that we don't
    # run into issues with the azure leasing system in CI
    # when this test is run for multiple python versions in parallel the azure leasing system will
    # cause failures if two tests try to access the same asset at the same time
    _id = f"{uuid4()}".replace("-", "")

    @op
    def first_op():
        return 5

    @op
    def second_op(op_1):
        assert op_1 == 5
        return op_1 + 1

    @graph(name=f"graph_asset_{_id}", out={f"asset3_{_id}": GraphOut()})
    def graph_asset():
        return second_op(first_op())

    @asset(
        name=f"upstream_{_id}",
        ins={"asset3": AssetIn(asset_key=AssetKey([f"asset3_{_id}"]))},  # pyright: ignore[reportCallIssue]
    )
    def upstream(asset3):
        return asset3 + 1

    SourceAsset(f"source1_{_id}", partitions_def=StaticPartitionsDefinition(["foo", "bar"]))

    # prepopulate storage with source asset
    io_manager = PickledObjectADLS2IOManager(
        file_system=file_system,
        adls2_client=create_adls2_client(storage_account, credential),
        blob_client=create_blob_client(storage_account, credential),
        lease_client_constructor=DataLakeLeaseClient,
    )
    for partition_key in ["foo", "bar"]:
        context = build_output_context(
            step_key=f"source1_{_id}",
            name="result",
            run_id=make_new_run_id(),
            dagster_type=resolve_dagster_type(int),
            partition_key=partition_key,
        )
        io_manager.handle_output(context, 1)

    @asset(
        name=f"downstream_{_id}",
        ins={"upstream": AssetIn(asset_key=AssetKey([f"upstream_{_id}"]))},  # pyright: ignore[reportCallIssue]
    )
    def downstream(upstream, source):
        assert upstream == 7
        return 1 + upstream + source["foo"] + source["bar"]

    asset_job = Definitions(
        assets=[upstream, downstream, AssetsDefinition.from_graph(graph_asset)],
        resources={"io_manager": adls2_pickle_io_manager, "adls2": adls2_resource},
        jobs=[define_asset_job("my_asset_job")],
    ).get_job_def("my_asset_job")

    run_config = {
        "resources": {
            "io_manager": {"config": {"adls2_file_system": file_system}},
            "adls2": {
                "config": {
                    "storage_account": storage_account,
                    "credential": {"key": credential},
                }
            },
        }
    }

    result = asset_job.execute_in_process(run_config=run_config)
    assert result.success


def test_with_fake_adls2_resource():
    job = define_inty_job(adls_io_resource=fake_adls2_resource)

    run_config = {
        "resources": {
            "io_manager": {"config": {"adls2_file_system": "fake_file_system"}},
            "adls2": {"config": {"account_name": "my_account"}},
        }
    }

    result = job.execute_in_process(run_config=run_config)
    assert result.success
