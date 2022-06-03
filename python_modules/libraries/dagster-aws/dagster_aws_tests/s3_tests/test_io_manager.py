from dagster_aws.s3.io_manager import s3_pickle_io_manager
from dagster_aws.s3.utils import construct_s3_client

from dagster import (
    GraphIn,
    GraphOut,
    In,
    Int,
    Out,
    Output,
    StaticPartitionsDefinition,
    VersionStrategy,
    asset,
    build_assets_job,
    graph,
    job,
    op,
    resource,
)
from dagster.core.asset_defs.assets import AssetsDefinition
from dagster.core.test_utils import instance_for_test


@resource
def s3_test_resource(_):
    return construct_s3_client(max_attempts=5)


def define_inty_job():
    @op(out=Out(Int))
    def return_one():
        return 1

    @op(
        ins={"num": In(Int)},
        out=Out(Int),
    )
    def add_one(num):
        return num + 1

    @job(
        resource_defs={
            "io_manager": s3_pickle_io_manager,
            "s3": s3_test_resource,
        }
    )
    def basic_external_plan_execution():
        add_one(return_one())

    return basic_external_plan_execution


def test_s3_pickle_io_manager_execution(mock_s3_bucket):
    assert not len(list(mock_s3_bucket.objects.all()))
    inty_job = define_inty_job()

    run_config = {"resources": {"io_manager": {"config": {"s3_bucket": mock_s3_bucket.name}}}}

    result = inty_job.execute_in_process(run_config)

    assert result.output_for_node("return_one") == 1
    assert result.output_for_node("add_one") == 2

    assert len(list(mock_s3_bucket.objects.all())) == 2


def define_multiple_output_job():
    @op(
        out={
            "foo": Out(Int),
            "foobar": Out(Int),
        }
    )
    def return_two_outputs():
        yield Output(10, "foobar")
        yield Output(5, "foo")

    @job(resource_defs={"io_manager": s3_pickle_io_manager, "s3": s3_test_resource})
    def output_prefix_execution_plan():
        return_two_outputs()

    return output_prefix_execution_plan


def test_s3_pickle_io_manager_prefix(mock_s3_bucket):
    assert not len(list(mock_s3_bucket.objects.all()))

    prefixy_job = define_multiple_output_job()

    run_config = {"resources": {"io_manager": {"config": {"s3_bucket": mock_s3_bucket.name}}}}

    result = prefixy_job.execute_in_process(run_config)

    assert result.output_for_node("return_two_outputs", "foo") == 5
    assert result.output_for_node("return_two_outputs", "foobar") == 10

    assert len(list(mock_s3_bucket.objects.all())) == 2


def test_memoization_s3_io_manager(mock_s3_bucket):
    class BasicVersionStrategy(VersionStrategy):
        def get_solid_version(self, _):
            return "foo"

    @op
    def basic():
        return "foo"

    @job(
        resource_defs={"io_manager": s3_pickle_io_manager, "s3": s3_test_resource},
        version_strategy=BasicVersionStrategy(),
    )
    def memoized():
        basic()

    run_config = {"resources": {"io_manager": {"config": {"s3_bucket": mock_s3_bucket.name}}}}
    with instance_for_test() as instance:
        result = memoized.execute_in_process(run_config=run_config, instance=instance)
        assert result.success
        assert result.output_for_node("basic") == "foo"

        result = memoized.execute_in_process(run_config=run_config, instance=instance)
        assert result.success
        assert len(result.all_node_events) == 0


def define_assets_job(bucket):
    @op
    def first_op(first_input):
        assert first_input == 2
        return first_input * 2

    @op
    def second_op(second_input):
        assert second_input == 4
        return second_input + 3

    @asset
    def asset1():
        return 1

    @asset
    def asset2(asset1):
        assert asset1 == 1
        return asset1 + 1

    @graph(ins={"asset2": GraphIn()}, out={"asset3": GraphOut()})
    def graph_asset(asset2):
        return second_op(first_op(asset2))

    @asset(partitions_def=StaticPartitionsDefinition(["apple", "orange"]))
    def partitioned():
        return 8

    return build_assets_job(
        name="assets",
        assets=[asset1, asset2, AssetsDefinition.from_graph(graph_asset), partitioned],
        resource_defs={
            "io_manager": s3_pickle_io_manager.configured({"s3_bucket": bucket}),
            "s3": s3_test_resource,
        },
    )


def test_s3_pickle_io_manager_asset_execution(mock_s3_bucket):
    assert not len(list(mock_s3_bucket.objects.all()))
    inty_job = define_assets_job(mock_s3_bucket.name)

    result = inty_job.execute_in_process(partition_key="apple")

    assert result.output_for_node("asset1") == 1
    assert result.output_for_node("asset2") == 2
    assert result.output_for_node("graph_asset.first_op") == 4
    assert result.output_for_node("graph_asset.second_op") == 7

    objects = list(mock_s3_bucket.objects.all())
    assert len(objects) == 5
    assert {(o.bucket_name, o.key) for o in objects} == {
        ("test-bucket", "dagster/asset1"),
        ("test-bucket", "dagster/asset2"),
        ("test-bucket", "dagster/asset3"),
        ("test-bucket", "dagster/partitioned/apple"),
        (
            "test-bucket",
            "/".join(["dagster", "storage", result.run_id, "graph_asset.first_op", "result"]),
        ),
    }
