import pickle

from dagster import (
    AssetsDefinition,
    DagsterInstance,
    DynamicOut,
    DynamicOutput,
    GraphIn,
    GraphOut,
    In,
    Int,
    Out,
    ResourceDefinition,
    StaticPartitionsDefinition,
    asset,
    build_input_context,
    build_output_context,
    graph,
    job,
    materialize,
    op,
    resource,
    with_resources,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.job_base import InMemoryJob
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster._core.events import DagsterEventType
from dagster._core.execution.api import create_execution_plan, execute_plan
from dagster._core.execution.plan.outputs import StepOutputHandle
from dagster._core.storage.dagster_run import (
    DagsterRun as DagsterRun,
)
from dagster._core.system_config.objects import ResolvedRunConfig
from dagster._core.types.dagster_type import resolve_dagster_type
from dagster._core.utils import make_new_run_id
from dagster_gcp.gcs import FakeConfigurableGCSClient, FakeGCSClient
from dagster_gcp.gcs.io_manager import (
    ConfigurablePickledObjectGCSIOManager,
    PickledObjectGCSIOManager,
    gcs_pickle_io_manager,
)
from dagster_gcp.gcs.resources import gcs_resource
from google.cloud import storage
from upath import UPath


@resource
def mock_gcs_resource(_):
    return FakeGCSClient()


def get_step_output(step_events, step_key, output_name="result"):
    for step_event in step_events:
        if (
            step_event.event_type == DagsterEventType.STEP_OUTPUT
            and step_event.step_key == step_key
            and step_event.step_output_data.output_name == output_name
        ):
            return step_event
    return None


def define_inty_job():
    @op(out=Out(Int, io_manager_key="io_manager"))
    def return_one():
        return 1

    @op(
        ins={"num": In(Int)},
        out=Out(Int, io_manager_key="io_manager"),
    )
    def add_one(num):
        return num + 1

    @job(resource_defs={"io_manager": gcs_pickle_io_manager, "gcs": gcs_resource})
    def basic_external_plan_execution():
        add_one(return_one())

    return basic_external_plan_execution


def test_gcs_pickle_io_manager_execution(gcs_bucket):
    inty_job = define_inty_job()

    run_config = {
        "resources": {
            "io_manager": {
                "config": {
                    "gcs_bucket": gcs_bucket,
                }
            }
        }
    }

    run_id = make_new_run_id()

    resolved_run_config = ResolvedRunConfig.build(inty_job, run_config=run_config)
    execution_plan = create_execution_plan(inty_job, run_config)

    assert execution_plan.get_step_by_key("return_one")

    step_keys = ["return_one"]
    instance = DagsterInstance.ephemeral()
    dagster_run = DagsterRun(job_name=inty_job.name, run_id=run_id, run_config=run_config)

    return_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(step_keys, inty_job, resolved_run_config),
            job=InMemoryJob(inty_job),
            run_config=run_config,
            dagster_run=dagster_run,
            instance=instance,
        )
    )

    assert get_step_output(return_one_step_events, "return_one")

    io_manager = PickledObjectGCSIOManager(gcs_bucket, storage.Client())
    step_output_handle = StepOutputHandle("return_one")
    context = build_input_context(
        upstream_output=build_output_context(
            step_key=step_output_handle.step_key,
            name=step_output_handle.output_name,
            run_id=run_id,
            dagster_type=resolve_dagster_type(int),
        ),
        dagster_type=resolve_dagster_type(int),
    )
    assert io_manager.load_input(context) == 1

    add_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(["add_one"], inty_job, resolved_run_config),
            job=InMemoryJob(inty_job),
            run_config=run_config,
            dagster_run=dagster_run,
            instance=instance,
        )
    )

    step_output_handle = StepOutputHandle("add_one")
    context = build_input_context(
        upstream_output=build_output_context(
            step_key=step_output_handle.step_key,
            name=step_output_handle.output_name,
            run_id=run_id,
            dagster_type=resolve_dagster_type(int),
        ),
        dagster_type=resolve_dagster_type(int),
    )

    assert get_step_output(add_one_step_events, "add_one")
    assert io_manager.load_input(context) == 2


def test_dynamic(gcs_bucket):
    @op(out=DynamicOut())
    def numbers():
        for i in range(3):
            yield DynamicOutput(i, mapping_key=str(i))

    @op
    def echo(_, x):
        return x

    @job(resource_defs={"io_manager": gcs_pickle_io_manager, "gcs": mock_gcs_resource})
    def dynamic():
        numbers().map(echo)

    result = dynamic.execute_in_process(
        run_config={"resources": {"io_manager": {"config": {"gcs_bucket": gcs_bucket}}}}
    )
    assert result.success


def test_asset_io_manager(gcs_bucket):
    @op
    def first_op(first_input):
        assert first_input == 5
        return first_input * 2

    @op
    def second_op(second_input):
        assert second_input == 10
        return second_input + 3

    @asset
    def upstream():
        return 2

    source1 = SourceAsset("source1", partitions_def=StaticPartitionsDefinition(["foo", "bar"]))

    fake_gcs_client = FakeGCSClient()
    bucket_obj = fake_gcs_client.bucket(gcs_bucket)

    # Pre-populate storage with source asset
    for partition_key in ["foo", "bar"]:
        path = UPath("assets", "source1", partition_key)
        bucket_obj.blob(str(path)).upload_from_string(pickle.dumps(1))

    @asset
    def downstream(upstream, source1):
        return 1 + upstream + source1["foo"] + source1["bar"]

    @graph(ins={"downstream": GraphIn()}, out={"asset3": GraphOut()})
    def graph_asset(downstream):
        return second_op(first_op(downstream))

    @asset(partitions_def=StaticPartitionsDefinition(["apple", "orange"]))
    def partitioned():
        return 8

    defs = Definitions(
        assets=[
            source1,
            upstream,
            downstream,
            AssetsDefinition.from_graph(graph_asset),
            partitioned,
        ],
        resources={
            "io_manager": gcs_pickle_io_manager.configured(
                {"gcs_bucket": gcs_bucket, "gcs_prefix": "assets"}
            ),
            "gcs": ResourceDefinition.hardcoded_resource(fake_gcs_client),
        },
        jobs=[define_asset_job("my_asset_job")],
    )
    asset_job = defs.get_job_def("my_asset_job")

    result = asset_job.execute_in_process(partition_key="apple")
    assert result.success
    assert fake_gcs_client.get_all_blob_paths() == {
        f"{gcs_bucket}/assets/upstream",
        f"{gcs_bucket}/assets/downstream",
        f"{gcs_bucket}/assets/partitioned/apple",
        f"{gcs_bucket}/assets/asset3",
        f"{gcs_bucket}/assets/storage/{result.run_id}/files/graph_asset.first_op/result",
        f"{gcs_bucket}/assets/source1/foo",
        f"{gcs_bucket}/assets/source1/bar",
    }


def test_nothing(gcs_bucket):
    @asset
    def asset1() -> None:
        ...

    @asset(deps=[asset1])
    def asset2() -> None:
        ...

    result = materialize(
        with_resources(
            [asset1, asset2],
            resource_defs={
                "io_manager": gcs_pickle_io_manager.configured(
                    {"gcs_bucket": gcs_bucket, "gcs_prefix": "assets"}
                ),
                "gcs": ResourceDefinition.hardcoded_resource(FakeGCSClient()),
            },
        )
    )

    handled_output_events = list(filter(lambda evt: evt.is_handled_output, result.all_node_events))
    assert len(handled_output_events) == 2

    for event in handled_output_events:
        assert len(event.event_specific_data.metadata) == 0


def test_asset_pythonic_io_manager(gcs_bucket):
    @op
    def first_op(first_input):
        assert first_input == 3
        return first_input * 2

    @op
    def second_op(second_input):
        assert second_input == 6
        return second_input + 3

    @asset
    def upstream():
        return 2

    @asset
    def downstream(upstream):
        return 1 + upstream

    @graph(ins={"downstream": GraphIn()}, out={"asset3": GraphOut()})
    def graph_asset(downstream):
        return second_op(first_op(downstream))

    @asset(partitions_def=StaticPartitionsDefinition(["apple", "orange"]))
    def partitioned():
        return 8

    fake_gcs_client = FakeConfigurableGCSClient()

    result = materialize(
        [upstream, downstream, AssetsDefinition.from_graph(graph_asset), partitioned],
        partition_key="apple",
        resources={
            "io_manager": ConfigurablePickledObjectGCSIOManager(
                gcs_bucket=gcs_bucket,
                gcs_prefix="assets",
                gcs=ResourceDefinition.hardcoded_resource(fake_gcs_client),
            ),
        },
    )
    assert result.success
    assert fake_gcs_client.get_client().get_all_blob_paths() == {
        f"{gcs_bucket}/assets/upstream",
        f"{gcs_bucket}/assets/downstream",
        f"{gcs_bucket}/assets/partitioned/apple",
        f"{gcs_bucket}/assets/asset3",
        f"{gcs_bucket}/assets/storage/{result.run_id}/files/graph_asset.first_op/result",
    }


def test_nothing_pythonic_io_manager(gcs_bucket):
    @asset
    def asset1() -> None:
        ...

    @asset(deps=[asset1])
    def asset2() -> None:
        ...

    result = materialize(
        with_resources(
            [asset1, asset2],
            resource_defs={
                "io_manager": ConfigurablePickledObjectGCSIOManager(
                    gcs_bucket=gcs_bucket,
                    gcs_prefix="assets",
                    gcs=ResourceDefinition.hardcoded_resource(FakeConfigurableGCSClient()),
                ),
            },
        )
    )

    handled_output_events = list(filter(lambda evt: evt.is_handled_output, result.all_node_events))
    assert len(handled_output_events) == 2

    for event in handled_output_events:
        assert len(event.event_specific_data.metadata) == 0
