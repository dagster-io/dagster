import math
import os
import random
import time
from collections import defaultdict
from contextlib import contextmanager
from typing import Mapping, Optional

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
from dagster._core.definitions.decorators import schedule
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.output import Out
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.test_utils import nesting_graph_job
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


_S3_RESOURCES = {
    "io_manager": s3_pickle_io_manager,
    "s3": s3_resource,
}


def apply_platform_settings(
    job_def: JobDefinition,
    platform: str,
    resources: Optional[Mapping[str, ResourceDefinition]] = None,
) -> JobDefinition:
    from dagster_celery import celery_executor
    from dagster_celery_docker import celery_docker_executor
    from dagster_celery_k8s import celery_k8s_job_executor
    from dagster_docker import docker_executor
    from dagster_k8s.executor import k8s_job_executor

    resources = resources if resources else {"s3": s3_resource}
    resources = merge_dicts(resources, {"io_manager": s3_pickle_io_manager})
    if platform == "k8s":
        executor = k8s_job_executor
    elif platform == "celery":
        executor = celery_executor
    elif platform == "celery_docker":
        executor = celery_docker_executor
    elif platform == "celery_k8s":
        executor = celery_k8s_job_executor
    elif platform == "docker":
        executor = docker_executor
    else:
        raise Exception(f"Unknown platform: {platform}")

    return job_def.with_top_level_resources(resources).with_executor_def(executor)


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


@op(ins={"word": In()})
def count_letters_op(word):
    counts = defaultdict(int)
    for letter in word:
        counts[letter] += 1
    return dict(counts)


@op
def hanging_op(_):
    while True:
        time.sleep(0.1)


@op(config_schema={"looking_for": str})
def get_environment(context):
    return os.environ.get(context.op_config["looking_for"])


@job(resource_defs=_S3_RESOURCES)
def hanging_job():
    hanging_op()


@job
def demo_job():
    count_letters(multiply_the_word())


@job
def demo_job_slow():
    count_letters(multiply_the_word_slow())


@job
def always_fail_job():
    always_fail(multiply_the_word())


demo_job_s3 = demo_job.with_top_level_resources(
    _S3_RESOURCES,
)


def define_demo_job_docker():
    return apply_platform_settings(demo_job, "docker")


def define_demo_job_docker_slow():
    return apply_platform_settings(demo_job_slow, "docker")


@op
def fail_first_time(context):
    event_records = context.instance.all_logs(context.run_id)
    for event_record in event_records:
        context.log.info(event_record.message)
        if "Started re-execution" in event_record.message:
            return "okay perfect"

    raise RetryRequested()


@job
def step_retries_job():
    fail_first_time()


def define_step_retries_job_docker():
    return apply_platform_settings(step_retries_job, "docker")


def define_demo_job_celery():
    return apply_platform_settings(demo_job, "celery")


@op(required_resource_keys={"buggy_resource"})
def hello(context):
    context.log.info("Hello, world from IMAGE 1")


def define_docker_celery_job():
    from dagster_celery_docker import celery_docker_executor

    @resource
    def resource_with_output():
        print("writing to stdout")  # noqa: T201
        print("{}")  # noqa: T201
        return 42

    @op(required_resource_keys={"resource_with_output"})
    def use_resource_with_output():
        pass

    @job(
        resource_defs={
            "s3": s3_resource,
            "io_manager": s3_pickle_io_manager,
            "resource_with_output": resource_with_output,
        },
        executor_def=celery_docker_executor,
    )
    def docker_celery_job():
        count_letters(multiply_the_word())
        get_environment()
        use_resource_with_output()

    return docker_celery_job


demo_job_gcs = demo_job.with_top_level_resources(
    resource_defs={"gcs": gcs_resource, "io_manager": gcs_pickle_io_manager},
)


def demo_job_gcs():
    count_letters(multiply_the_word())


@op
def error_op():
    raise Exception("Unusual error")


@job
def demo_error_job():
    error_op()


demo_error_job_s3 = demo_error_job.with_top_level_resources(
    _S3_RESOURCES,
)


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


@job
def optional_outputs():
    foo_res = foo()
    bar.alias("first_consumer")(input_arg=foo_res.out_1)
    bar.alias("second_consumer")(input_arg=foo_res.out_2)
    bar.alias("third_consumer")(input_arg=foo_res.out_3)


def define_long_running_job_celery():
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

    @job
    def long_running_job_celery():
        for i in range(10):
            t = long_running_task.alias("first_%d" % i)()
            post_process.alias("post_process_%d" % i)(t)

    return apply_platform_settings(long_running_job_celery, "celery_k8s")


def define_large_job_celery():
    job_def = nesting_graph_job(
        depth=1,
        num_children=6,
        name="large_job_celery",
    )
    return apply_platform_settings(job_def, "celery_k8s")


_resources_limit_tags = {
    "dagster-k8s/config": {
        "container_config": {
            "resources": {
                "requests": {"cpu": "250m", "memory": "64Mi"},
                "limits": {"cpu": "500m", "memory": "2560Mi"},
            }
        }
    }
}


@op(tags=_resources_limit_tags)
def resource_req_op(context):
    context.log.info("running")


@job(tags=_resources_limit_tags)
def resources_limit_job_k8s():
    resource_req_op()


def define_resources_limit_job_k8s():
    return apply_platform_settings(resources_limit_job_k8s, "k8s")


def define_resources_limit_job_celery_k8s():
    return apply_platform_settings(resources_limit_job_k8s, "celery_k8s")


def define_schedules():
    @schedule(
        cron_schedule="@daily",
        name="daily_optional_outputs",
        job_name=optional_outputs.name,
    )
    def daily_optional_outputs(_context):
        return {}

    @schedule(
        job_name="demo_job_celery",
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


@job
def retry_job():
    fail_first_time()


def define_retry_job_k8s():
    return apply_platform_settings(retry_job, "k8s")


def define_retry_job_celery_k8s():
    return apply_platform_settings(retry_job, "celery_k8s")


@op
def slow_op(_):
    time.sleep(100)


@job
def slow_job():
    slow_op()


def define_slow_job_k8s():
    return apply_platform_settings(slow_job, "k8s")


def define_slow_job_celery_k8s():
    return apply_platform_settings(slow_job, "celery_k8s")


def define_resource_job():
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
            key = f"resource_termination_test/{context.run_id}"
            s3.put_object(Bucket=bucket, Key=key, Body=b"foo")

    @op(required_resource_keys={"s3_resource_with_context_manager"})
    def super_slow_solid():
        time.sleep(1000)

    @job
    def resource_job():
        super_slow_solid()

    return apply_platform_settings(
        resource_job,
        "celery",
        resources={
            "s3": s3_resource,
            "s3_resource_with_context_manager": s3_resource_with_context_manager,
            "io_manager": s3_pickle_io_manager,
        },
    )


def define_fan_in_fan_out_job():
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
            fan_outs.append(add_one_fan.alias(f"add_one_fan_{level}_{i}")(source))

        return sum_fan_in.alias(f"sum_{level}")(fan_outs)

    @job
    def fan_in_fan_out_job():
        return_one_out = return_one()
        prev_level_out = return_one_out
        for level in range(0, 20):
            prev_level_out = construct_fan_in_level(prev_level_out, level, 2)

    return apply_platform_settings(fan_in_fan_out_job, "celery")


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


@job(
    resource_defs={"io_manager": fs_io_manager},
)
def demo_airflow_execution_date_job():
    emit_airflow_execution_date()


@job(
    resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager},
)
def demo_airflow_execution_date_job_s3():
    emit_airflow_execution_date()


def define_hard_failer():
    @job
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

    return apply_platform_settings(hard_failer, "celery")


def define_demo_k8s_executor_job():
    from dagster_k8s.executor import k8s_job_executor

    @job(
        resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager},
        executor_def=k8s_job_executor,
    )
    def demo_k8s_executor_job():
        count_letters(multiply_the_word())

    return demo_k8s_executor_job


@op
def check_volume_mount(context):
    with open(
        "/opt/dagster/test_mount_path/volume_mounted_file.yaml", "r", encoding="utf8"
    ) as mounted_file:
        contents = mounted_file.read()
        context.log.info(f"Contents of mounted file: {contents}")
        assert contents == "BAR_CONTENTS"


def define_k8s_volume_mount_job():
    from dagster_k8s.executor import k8s_job_executor

    @job(
        resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager},
        executor_def=k8s_job_executor,
    )
    def volume_mount_job():
        check_volume_mount()

    return volume_mount_job


def define_celery_volume_mount_job():
    from dagster_celery import celery_executor

    @job(
        resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager},
        executor_def=celery_executor,
    )
    def volume_mount_job():
        check_volume_mount()

    return volume_mount_job


@op
def foo_op():
    return "foo"


class BasicVersionStrategy(VersionStrategy):
    def get_op_version(self, _):
        return "foo"


@job(version_strategy=BasicVersionStrategy())
def memoization_job():
    foo_op()


def define_memoization_job_k8s():
    return apply_platform_settings(memoization_job, "k8s")


def define_memoization_job_celery_k8s():
    return apply_platform_settings(memoization_job, "celery_k8s")


def define_demo_execution_repo():
    @repository
    def demo_execution_repo():
        return {
            "jobs": {
                "always_fail_job": always_fail_job,
                "celery_volume_mount_job": define_celery_volume_mount_job,
                "demo_job": demo_job,
                "demo_job_s3": demo_job_s3,
                "demo_airflow_execution_date_job": demo_airflow_execution_date_job,
                "demo_airflow_execution_date_job_s3": demo_airflow_execution_date_job_s3,
                "demo_error_job": demo_error_job,
                "demo_error_job_s3": demo_error_job_s3,
                "demo_job_celery": define_demo_job_celery,
                "demo_job_docker": define_demo_job_docker,
                "demo_job_docker_slow": define_demo_job_docker_slow,
                "demo_job_gcs": demo_job_gcs,
                "demo_k8s_executor_job": define_demo_k8s_executor_job,
                "docker_celery_job": define_docker_celery_job,
                "fan_in_fan_out_job": define_fan_in_fan_out_job,
                "hanging_job": hanging_job,
                "hard_failer": define_hard_failer,
                "k8s_volume_mount_job": define_k8s_volume_mount_job,
                "large_job_celery": define_large_job_celery,
                "long_running_job_celery": define_long_running_job_celery,
                "memoization_job_celery_k8s": define_memoization_job_celery_k8s,
                "memoization_job_k8s": define_memoization_job_k8s,
                "optional_outputs": optional_outputs,
                "resources_limit_job_k8s": define_resources_limit_job_k8s,
                "resources_limit_job_celery_k8s": define_resources_limit_job_celery_k8s,
                "resource_job": define_resource_job,
                "retry_job_celery_k8s": define_retry_job_celery_k8s,
                "retry_job_k8s": define_retry_job_k8s,
                "slow_job_celery_k8s": define_slow_job_celery_k8s,
                "slow_job_k8s": define_slow_job_k8s,
                "step_retries_job_docker": define_step_retries_job_docker,
            },
            "schedules": define_schedules(),
        }

    return demo_execution_repo
