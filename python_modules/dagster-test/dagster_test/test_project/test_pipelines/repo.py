# pylint:disable=no-member
import datetime
import math
import os
import random
import time
from collections import defaultdict
from contextlib import contextmanager

import boto3
from dagster import (
    AssetMaterialization,
    Bool,
    Field,
    In,
    Int,
    IntSource,
    List,
    Output,
    RetryRequested,
    VersionStrategy,
    file_relative_path,
    fs_io_manager,
    job,
    op,
    repository,
    resource,
)
from dagster._core.definitions.decorators import daily_schedule, schedule
from dagster._core.definitions.output import Out
from dagster._core.test_utils import nesting_graph_pipeline
from dagster._legacy import (
    ModeDefinition,
    default_executors,
    pipeline,
)
from dagster._utils import segfault
from dagster._utils.merger import merge_dicts
from dagster._utils.yaml_utils import merge_yamls
from dagster_aws.s3 import s3_pickle_io_manager, s3_resource
from dagster_gcp.gcs import gcs_pickle_io_manager, gcs_resource

IS_BUILDKITE = bool(os.getenv("BUILDKITE"))


def image_pull_policy():
    # This is because when running local tests, we need to load the image into the kind cluster (and
    # then not attempt to pull it) because we don't want to require credentials for a private
    # registry / pollute the private registry / set up and network a local registry as a condition
    # of running tests
    if IS_BUILDKITE:
        return "Always"
    else:
        return "IfNotPresent"


def celery_mode_defs(resources=None, name="default"):
    from dagster_celery import celery_executor
    from dagster_celery_k8s import celery_k8s_job_executor

    resources = resources if resources else {"s3": s3_resource}
    resources = merge_dicts(resources, {"io_manager": s3_pickle_io_manager})
    return [
        ModeDefinition(
            name=name,
            resource_defs=resources
            if resources
            else {"s3": s3_resource, "io_manager": s3_pickle_io_manager},
            executor_defs=default_executors + [celery_executor, celery_k8s_job_executor],
        )
    ]


def k8s_mode_defs(resources=None, name="default"):
    from dagster_k8s.executor import k8s_job_executor

    resources = resources if resources else {"s3": s3_resource}
    resources = merge_dicts(resources, {"io_manager": s3_pickle_io_manager})

    return [
        ModeDefinition(
            name=name,
            resource_defs=resources
            if resources
            else {"s3": s3_resource, "io_manager": s3_pickle_io_manager},
            executor_defs=default_executors + [k8s_job_executor],
        )
    ]


def docker_mode_defs():
    from dagster_docker import docker_executor

    return [
        ModeDefinition(
            resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager},
            executor_defs=[docker_executor],
        )
    ]


@op(
    config_schema={
        "factor": IntSource,
        "should_segfault": Field(bool, is_required=False, default_value=False),
    },
)
def multiply_the_word(context, word: str) -> str:
    if context.op_config.get("should_segfault"):
        segfault()
    return word * context.op_config["factor"]


@op(
    config_schema={"factor": IntSource, "sleep_time": IntSource},
)
def multiply_the_word_slow(context, word: str) -> str:
    time.sleep(context.op_config["sleep_time"])
    return word * context.op_config["factor"]


@op
def count_letters(word: str):
    counts = defaultdict(int)
    for letter in word:
        counts[letter] += 1
    return dict(counts)


@op
def always_fail(context, word: str):
    raise Exception("Op Exception Message")


@op(
    config_schema={"factor": IntSource},
)
def multiply_the_word_op(context, word: str) -> str:
    return word * context.op_config["factor"]


@op(ins={"word": In()})
def count_letters_op(word):
    counts = defaultdict(int)
    for letter in word:
        counts[letter] += 1
    return dict(counts)


@op()
def error_solid():
    raise Exception("Unusual error")


@op
def hanging_solid(_):
    while True:
        time.sleep(0.1)


@op(config_schema={"looking_for": str})
def get_environment_solid(context):
    return os.environ.get(context.op_config["looking_for"])


@pipeline(
    mode_defs=[
        ModeDefinition(
            resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager},
        )
    ]
)
def hanging_pipeline():
    hanging_solid()


@pipeline(
    mode_defs=[
        ModeDefinition(
            resource_defs={"io_manager": fs_io_manager},
        )
    ]
)
def demo_pipeline():
    count_letters(multiply_the_word())


@pipeline(
    mode_defs=[
        ModeDefinition(
            resource_defs={"io_manager": fs_io_manager},
        )
    ]
)
def always_fail_pipeline():
    always_fail(multiply_the_word())


@pipeline(
    mode_defs=[
        ModeDefinition(
            resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager},
        )
    ]
)
def demo_pipeline_s3():
    count_letters(multiply_the_word())


def define_demo_pipeline_docker():
    @pipeline(mode_defs=docker_mode_defs())
    def demo_pipeline_docker():
        count_letters(multiply_the_word())

    return demo_pipeline_docker


@op
def fail_first_time(context):
    event_records = context.instance.all_logs(context.run_id)
    for event_record in event_records:
        context.log.info(event_record.message)
        if "Started re-execution" in event_record.message:
            return "okay perfect"

    raise RetryRequested()


def definie_step_retries_pipeline_docker():
    @pipeline(mode_defs=docker_mode_defs())
    def step_retries_pipeline_docker():
        fail_first_time()

    return step_retries_pipeline_docker


def define_demo_pipeline_docker_slow():
    @pipeline(mode_defs=docker_mode_defs())
    def demo_pipeline_docker_slow():
        count_letters(multiply_the_word_slow())

    return demo_pipeline_docker_slow


def define_demo_pipeline_celery():
    @pipeline(mode_defs=celery_mode_defs())
    def demo_pipeline_celery():
        count_letters(multiply_the_word())

    return demo_pipeline_celery


def define_demo_job_celery():
    from dagster_celery_k8s import celery_k8s_job_executor

    @job(
        resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager},
        executor_def=celery_k8s_job_executor,
    )
    def demo_job_celery():
        count_letters_op.alias("count_letters")(multiply_the_word_op.alias("multiply_the_word")())

    return demo_job_celery


@op(required_resource_keys={"buggy_resource"})
def hello(context):
    context.log.info("Hello, world from IMAGE 1")


def define_docker_celery_pipeline():
    from dagster_celery_docker import celery_docker_executor

    @resource
    def resource_with_output():
        print("writing to stdout")  # noqa: T201
        return 42

    @op(required_resource_keys={"resource_with_output"})
    def use_resource_with_output_solid():
        pass

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "s3": s3_resource,
                    "io_manager": s3_pickle_io_manager,
                    "resource_with_output": resource_with_output,
                },
                executor_defs=default_executors + [celery_docker_executor],
            )
        ]
    )
    def docker_celery_pipeline():
        count_letters(multiply_the_word())
        get_environment_solid()
        use_resource_with_output_solid()

    return docker_celery_pipeline


@pipeline(
    mode_defs=[
        ModeDefinition(
            resource_defs={"gcs": gcs_resource, "io_manager": gcs_pickle_io_manager},
        )
    ]
)
def demo_pipeline_gcs():
    count_letters(multiply_the_word())


@pipeline(
    mode_defs=[
        ModeDefinition(
            resource_defs={"io_manager": fs_io_manager},
        )
    ]
)
def demo_error_pipeline():
    error_solid()


# TODO: migrate test_project to crag
@op
def emit_airflow_execution_date_op(context):
    airflow_execution_date = context.pipeline_run.tags["airflow_execution_date"]
    yield AssetMaterialization(
        asset_key="airflow_execution_date",
        metadata={
            "airflow_execution_date": airflow_execution_date,
        },
    )
    yield Output(airflow_execution_date)


@op()
def error_op():
    raise Exception("Unusual error")


@job
def demo_error_job():
    error_solid()


@job
def demo_airflow_execution_date_job():
    emit_airflow_execution_date_op()


@pipeline(
    mode_defs=[
        ModeDefinition(
            resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager},
        )
    ]
)
def demo_error_pipeline_s3():
    error_solid()


@op(
    out={
        "out_1": Out(Int, is_required=False),
        "out_2": Out(Int, is_required=False),
        "out_3": Out(Int, is_required=False),
    }
)
def foo(_):
    yield Output(1, "out_1")


@op
def bar(_, input_arg):
    return input_arg


@pipeline(mode_defs=[ModeDefinition(resource_defs={"io_manager": fs_io_manager})])
def optional_outputs():
    foo_res = foo()
    bar.alias("first_consumer")(input_arg=foo_res.out_1)
    bar.alias("second_consumer")(input_arg=foo_res.out_2)
    bar.alias("third_consumer")(input_arg=foo_res.out_3)


def define_long_running_pipeline_celery():
    @op
    def long_running_task(context):
        iterations = 20 * 30  # 20 minutes
        for i in range(iterations):
            context.log.info(
                "task in progress [%d/100]%% complete" % math.floor(100.0 * float(i) / iterations)
            )
            time.sleep(2)
        return random.randint(0, iterations)

    @op
    def post_process(context, input_count):
        context.log.info("received input %d" % input_count)
        iterations = 60 * 2  # 2 hours
        for i in range(iterations):
            context.log.info(
                "post-process task in progress [%d/100]%% complete"
                % math.floor(100.0 * float(i) / iterations)
            )
            time.sleep(60)

    @pipeline(mode_defs=celery_mode_defs())
    def long_running_pipeline_celery():
        for i in range(10):
            t = long_running_task.alias("first_%d" % i)()
            post_process.alias("post_process_%d" % i)(t)

    return long_running_pipeline_celery


def define_large_pipeline_celery():
    return nesting_graph_pipeline(
        depth=1,
        num_children=6,
        mode_defs=celery_mode_defs(),
        name="large_pipeline_celery",
    )


@op(
    tags={
        "dagster-k8s/config": {
            "container_config": {
                "resources": {
                    "requests": {"cpu": "250m", "memory": "64Mi"},
                    "limits": {"cpu": "500m", "memory": "2560Mi"},
                }
            }
        }
    }
)
def resource_req_solid(context):
    context.log.info("running")


def define_resources_limit_pipeline():
    @pipeline(
        mode_defs=celery_mode_defs() + k8s_mode_defs(name="k8s"),
        tags={
            "dagster-k8s/config": {
                "container_config": {
                    "resources": {
                        "requests": {"cpu": "250m", "memory": "64Mi"},
                        "limits": {"cpu": "500m", "memory": "2560Mi"},
                    }
                }
            }
        },
    )
    def resources_limit_pipeline():
        resource_req_solid()

    return resources_limit_pipeline


def define_schedules():
    @daily_schedule(
        name="daily_optional_outputs",
        job_name=optional_outputs.name,
        start_date=datetime.datetime(2020, 1, 1),
    )
    def daily_optional_outputs(_date):
        return {}

    @schedule(
        job_name="demo_pipeline_celery",
        cron_schedule="* * * * *",
    )
    def frequent_celery():
        from dagster_celery_k8s.config import get_celery_engine_config

        additional_env_config_maps = ["test-aws-env-configmap"] if not IS_BUILDKITE else []

        return merge_dicts(
            merge_yamls(
                [
                    file_relative_path(__file__, os.path.join("..", "environments", "env.yaml")),
                    file_relative_path(__file__, os.path.join("..", "environments", "env_s3.yaml")),
                ]
            ),
            get_celery_engine_config(
                image_pull_policy=image_pull_policy(),
                additional_env_config_maps=additional_env_config_maps,
            ),
        )

    return {
        "daily_optional_outputs": daily_optional_outputs,
        "frequent_celery": frequent_celery,
    }


def define_step_retry_pipeline():
    @pipeline(mode_defs=celery_mode_defs() + k8s_mode_defs(name="k8s"))
    def retry_pipeline():
        fail_first_time()

    return retry_pipeline


def define_slow_pipeline():
    @op
    def slow_solid(_):
        time.sleep(100)

    @pipeline(mode_defs=celery_mode_defs() + k8s_mode_defs(name="k8s"))
    def slow_pipeline():
        slow_solid()

    return slow_pipeline


def define_resource_pipeline():
    @resource
    @contextmanager
    def s3_resource_with_context_manager(context):
        try:
            context.log.info("initializing s3_resource_with_context_manager")
            s3 = boto3.resource(
                "s3", region_name="us-west-1", use_ssl=True, endpoint_url=None
            ).meta.client
            yield s3
        finally:
            context.log.info("tearing down s3_resource_with_context_manager")
            bucket = "dagster-scratch-80542c2"
            key = "resource_termination_test/{}".format(context.run_id)
            s3.put_object(Bucket=bucket, Key=key, Body=b"foo")

    @op(required_resource_keys={"s3_resource_with_context_manager"})
    def super_slow_solid():
        time.sleep(1000)

    @pipeline(
        mode_defs=celery_mode_defs(
            resources={
                "s3": s3_resource,
                "s3_resource_with_context_manager": s3_resource_with_context_manager,
                "io_manager": s3_pickle_io_manager,
            }
        )
    )
    def resource_pipeline():
        super_slow_solid()

    return resource_pipeline


def define_fan_in_fan_out_pipeline():
    @op
    def return_one(_) -> int:
        return 1

    @op
    def add_one_fan(_, num: int) -> int:
        return num + 1

    @op(ins={"nums": In(List[int])})
    def sum_fan_in(_, nums):
        return sum(nums)

    def construct_fan_in_level(source, level, fanout):
        fan_outs = []
        for i in range(0, fanout):
            fan_outs.append(add_one_fan.alias("add_one_fan_{}_{}".format(level, i))(source))

        return sum_fan_in.alias("sum_{}".format(level))(fan_outs)

    @pipeline(mode_defs=celery_mode_defs())
    def fan_in_fan_out_pipeline():
        return_one_out = return_one()
        prev_level_out = return_one_out
        for level in range(0, 20):
            prev_level_out = construct_fan_in_level(prev_level_out, level, 2)

    return fan_in_fan_out_pipeline


@op
def emit_airflow_execution_date(context):
    airflow_execution_date = context.pipeline_run.tags["airflow_execution_date"]
    yield AssetMaterialization(
        asset_key="airflow_execution_date",
        metadata={
            "airflow_execution_date": airflow_execution_date,
        },
    )
    yield Output(airflow_execution_date)


@pipeline(
    mode_defs=[
        ModeDefinition(
            resource_defs={"io_manager": fs_io_manager},
        )
    ]
)
def demo_airflow_execution_date_pipeline():
    emit_airflow_execution_date()


@pipeline(
    mode_defs=[
        ModeDefinition(
            resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager},
        )
    ]
)
def demo_airflow_execution_date_pipeline_s3():
    emit_airflow_execution_date()


def define_hard_failer():
    @pipeline(mode_defs=celery_mode_defs())
    def hard_failer():
        @op(
            config_schema={"fail": Field(Bool, is_required=False, default_value=False)},
        )
        def hard_fail_or_0(context) -> int:
            if context.op_config["fail"]:
                segfault()
            return 0

        @op
        def increment(_, n: int):
            return n + 1

        increment(hard_fail_or_0())

    return hard_failer


def define_demo_k8s_executor_pipeline():
    @pipeline(
        mode_defs=k8s_mode_defs(),
    )
    def demo_k8s_executor_pipeline():
        count_letters(multiply_the_word())

    return demo_k8s_executor_pipeline


@op
def check_volume_mount(context):
    with open(
        "/opt/dagster/test_mount_path/volume_mounted_file.yaml", "r", encoding="utf8"
    ) as mounted_file:
        contents = mounted_file.read()
        context.log.info(f"Contents of mounted file: {contents}")
        assert contents == "BAR_CONTENTS"


def define_volume_mount_pipeline():
    @pipeline(
        mode_defs=k8s_mode_defs(name="k8s") + celery_mode_defs(name="celery"),
    )
    def volume_mount_pipeline():
        check_volume_mount()

    return volume_mount_pipeline


def define_memoization_pipeline():
    @op
    def foo_solid():
        return "foo"

    class BasicVersionStrategy(VersionStrategy):
        def get_op_version(self, _):
            return "foo"

    @pipeline(
        mode_defs=k8s_mode_defs(name="k8s") + celery_mode_defs(name="celery"),
        version_strategy=BasicVersionStrategy(),
    )
    def memoization_pipeline():
        foo_solid()

    return memoization_pipeline


def define_demo_execution_repo():
    @repository
    def demo_execution_repo():
        return {
            "pipelines": {
                "always_fail_pipeline": always_fail_pipeline,
                "demo_pipeline_celery": define_demo_pipeline_celery,
                "demo_pipeline_docker": define_demo_pipeline_docker,
                "demo_pipeline_docker_slow": define_demo_pipeline_docker_slow,
                "step_retries_pipeline_docker": definie_step_retries_pipeline_docker,
                "large_pipeline_celery": define_large_pipeline_celery,
                "long_running_pipeline_celery": define_long_running_pipeline_celery,
                "optional_outputs": optional_outputs,
                "demo_pipeline": demo_pipeline,
                "demo_pipeline_s3": demo_pipeline_s3,
                "demo_pipeline_gcs": demo_pipeline_gcs,
                "demo_error_pipeline": demo_error_pipeline,
                "demo_error_pipeline_s3": demo_error_pipeline_s3,
                "resources_limit_pipeline": define_resources_limit_pipeline,
                "retry_pipeline": define_step_retry_pipeline,
                "slow_pipeline": define_slow_pipeline,
                "fan_in_fan_out_pipeline": define_fan_in_fan_out_pipeline,
                "resource_pipeline": define_resource_pipeline,
                "docker_celery_pipeline": define_docker_celery_pipeline,
                "demo_airflow_execution_date_pipeline": demo_airflow_execution_date_pipeline,
                "demo_airflow_execution_date_pipeline_s3": demo_airflow_execution_date_pipeline_s3,
                "hanging_pipeline": hanging_pipeline,
                "hard_failer": define_hard_failer,
                "demo_k8s_executor_pipeline": define_demo_k8s_executor_pipeline,
                "volume_mount_pipeline": define_volume_mount_pipeline,
                "memoization_pipeline": define_memoization_pipeline,
            },
            "jobs": {
                "demo_error_job": demo_error_job,
                "demo_airflow_execution_date_job": demo_airflow_execution_date_job,
                "demo_job_celery": define_demo_job_celery,
            },
            "schedules": define_schedules(),
        }

    return demo_execution_repo
