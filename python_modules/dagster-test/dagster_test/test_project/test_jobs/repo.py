import math
import os
import random
import time
from collections import defaultdict
from contextlib import contextmanager
from typing import Any, Callable, Mapping, Optional, Union

import boto3
from dagster import (
    AssetMaterialization,
    Bool,
    DagsterEvent,
    Field,
    In,
    Int,
    IntSource,
    List,
    Output,
    RetryPolicy,
    RetryRequested,
    file_relative_path,
    graph,
    job,
    op,
    repository,
    resource,
    schedule,
)
from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.output import Out
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.execution.plan.objects import StepSuccessData
from dagster._core.test_utils import nesting_graph, poll_for_step_start
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

_GCS_RESOURCES = {
    "io_manager": gcs_pickle_io_manager,
    "gcs": gcs_resource,
}


def define_job(
    graph_def: GraphDefinition,
    platform: Optional[str] = None,
    extra_resources: Optional[Mapping[str, ResourceDefinition]] = None,
    name: Optional[str] = None,
    **kwargs: Any,  # forwarded to graph_def.to_job
) -> Union[JobDefinition, Callable[[], JobDefinition]]:
    if not name:
        base_name = graph_def.name.rsplit("_", 1)[0]  # remove "_graph" suffix
        suffix = f"_job_{platform}" if platform else "_job"
        name = f"{base_name}{suffix}"
    job_def = graph_def.to_job(name=name, **kwargs)

    if platform:
        return lambda: apply_platform_settings(job_def, platform, extra_resources or {})
    else:
        return job_def


def apply_platform_settings(
    job_def: JobDefinition,
    platform: Optional[str],
    extra_resources: Mapping[str, ResourceDefinition] = {},
) -> JobDefinition:
    if platform == "k8s":
        from dagster_k8s.executor import k8s_job_executor

        executor = k8s_job_executor
        resources = _S3_RESOURCES
    elif platform == "celery":
        from dagster_celery import celery_executor

        executor = celery_executor
        resources = _S3_RESOURCES
    elif platform == "celery_docker":
        from dagster_celery_docker import celery_docker_executor

        executor = celery_docker_executor
        resources = _S3_RESOURCES
    elif platform == "celery_k8s":
        from dagster_celery_k8s import celery_k8s_job_executor

        executor = celery_k8s_job_executor
        resources = _S3_RESOURCES
    elif platform == "docker":
        from dagster_docker import docker_executor

        executor = docker_executor
        resources = _S3_RESOURCES
    elif platform == "s3":
        executor = None
        resources = _S3_RESOURCES
    elif platform == "gcs":
        executor = None
        resources = _GCS_RESOURCES
    elif platform:
        raise Exception(f"Unknown platform: {platform}")
    else:
        executor = None
        resources = {}

    job_def = job_def.with_top_level_resources({**resources, **extra_resources})
    return job_def.with_executor_def(executor) if executor else job_def


@op(
    config_schema={
        "factor": IntSource,
        "should_segfault": Field(bool, is_required=False, default_value=False),
    },
    retry_policy=RetryPolicy(
        max_retries=2,
    ),
)
def multiply_the_word(context, word: str) -> str:
    if context.op_config.get("should_segfault"):
        segfault()
    return word * context.op_config["factor"]


@op
def count_letters(word: str):
    counts = defaultdict(int)
    for letter in word:
        counts[letter] += 1
    return dict(counts)


@graph
def demo_graph():
    count_letters(multiply_the_word())


@op
def always_fail(context, word: str):
    raise Exception("Op Exception Message")


@op(
    config_schema={"factor": IntSource, "sleep_time": IntSource},
)
def multiply_the_word_slow(context, word: str) -> str:
    time.sleep(context.op_config["sleep_time"])
    return word * context.op_config["factor"]


@graph
def demo_slow_graph():
    count_letters(multiply_the_word_slow())


@op
def hanging_op(_):
    while True:
        time.sleep(0.1)


@op(config_schema={"looking_for": str})
def get_environment(context):
    return os.environ.get(context.op_config["looking_for"])


@graph
def hanging_graph():
    hanging_op()


@graph
def always_fail_graph():
    always_fail(multiply_the_word())


@op
def fail_first_time(context):
    event_records = context.instance.all_logs(context.run_id)
    for event_record in event_records:
        context.log.info(event_record.message)
        if "Started re-execution" in event_record.message:
            return "okay perfect"

    raise RetryRequested()


@graph
def step_retries_graph():
    fail_first_time()


@op(required_resource_keys={"buggy_resource"})
def hello(context):
    context.log.info("Hello, world from IMAGE 1")


@resource
def resource_with_output():
    print("writing to stdout")  # noqa: T201
    print("{}")  # noqa: T201
    return 42


@op(required_resource_keys={"resource_with_output"})
def use_resource_with_output():
    pass


@graph
def demo_resource_output_graph():
    count_letters(multiply_the_word())
    get_environment()
    use_resource_with_output()


@op
def error_op():
    raise Exception("Unusual error")


@graph
def demo_error_graph():
    error_op()


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


@graph
def optional_outputs_graph():
    foo_res = foo()
    bar.alias("first_consumer")(input_arg=foo_res.out_1)
    bar.alias("second_consumer")(input_arg=foo_res.out_2)
    bar.alias("third_consumer")(input_arg=foo_res.out_3)


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


@graph
def long_running_graph():
    for i in range(10):
        t = long_running_task.alias("first_%d" % i)()
        post_process.alias("post_process_%d" % i)(t)


large_graph = nesting_graph(depth=1, num_children=6, name="large_graph")

resources_limit_tags = {
    "dagster-k8s/config": {
        "container_config": {
            "resources": {
                "requests": {"cpu": "250m", "memory": "64Mi"},
                "limits": {"cpu": "500m", "memory": "2560Mi"},
            }
        }
    }
}


@op(tags=resources_limit_tags)
def resource_req_op(context):
    context.log.info("running")


@graph
def resources_limit_graph():
    resource_req_op()


@job(tags=resources_limit_tags)
def resources_limit_job_k8s():
    resource_req_op()


def define_schedules():
    @schedule(
        cron_schedule="@daily",
        name="daily_optional_outputs",
        job_name="optional_outputs_job",
    )
    def daily_optional_outputs(_context):
        return {}

    @schedule(
        job_name="demo_job_celery_k8s",
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


@graph
def retry_graph():
    fail_first_time()


@op
def slow_op(_):
    time.sleep(100)


@graph
def slow_graph():
    slow_op()


@op
def slow_execute_k8s_op(context):
    # lazily import, since this repo is used in docker-tests and we can avoid the k8s import
    from dagster_k8s import execute_k8s_job

    execute_k8s_job(
        context,
        image="busybox",
        command=["/bin/sh", "-c"],
        args=["sleep 1200; echo HI"],
        namespace=context.op_config["namespace"],
        k8s_job_name=context.op_config["k8s_job_name"],
    )


@graph
def slow_execute_k8s_op_graph():
    slow_execute_k8s_op()


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


@graph
def resource_graph():
    super_slow_solid()


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


@graph
def fan_in_fan_out_graph():
    return_one_out = return_one()
    prev_level_out = return_one_out
    for level in range(0, 20):
        prev_level_out = construct_fan_in_level(prev_level_out, level, 2)


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


@graph
def demo_airflow_execution_date_graph():
    emit_airflow_execution_date()


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


@graph
def hard_failer_graph():
    increment(hard_fail_or_0())


@op
def check_volume_mount(context):
    with open(
        "/opt/dagster/test_mount_path/volume_mounted_file.yaml", "r", encoding="utf8"
    ) as mounted_file:
        contents = mounted_file.read()
        context.log.info(f"Contents of mounted file: {contents}")
        assert contents == "BAR_CONTENTS"


@graph
def volume_mount_graph():
    check_volume_mount()


@op
def op_that_emits_duplicate_step_success_event(context):
    # Wait for the other op to start so that it will be terminated mid-execution
    poll_for_step_start(context.instance, context.dagster_run.run_id, message="hanging_op")

    # emits a duplicate step success event which will mess up the execution
    # machinery and fail the run worker
    yield DagsterEvent.step_success_event(
        context._step_execution_context,  # noqa
        StepSuccessData(duration_ms=50.0),
    )
    yield Output(5)


@graph
def fails_run_worker_graph():
    hanging_op()
    op_that_emits_duplicate_step_success_event()


@op
def foo_op():
    return "foo"


def define_demo_execution_repo():
    @repository
    def demo_execution_repo():
        return {
            "jobs": {
                "always_fail_job": define_job(always_fail_graph),
                "demo_job": define_job(demo_graph),
                "demo_job_s3": define_job(demo_graph, "s3"),
                "demo_airflow_execution_date_job": define_job(demo_airflow_execution_date_graph),
                "demo_airflow_execution_date_job_s3": define_job(
                    demo_airflow_execution_date_graph, "s3"
                ),
                "demo_error_job": define_job(demo_error_graph),
                "demo_error_job_s3": define_job(demo_error_graph, "s3"),
                "demo_job_celery_k8s": define_job(demo_graph, "celery_k8s"),
                "demo_job_docker": define_job(demo_graph, "docker"),
                "demo_slow_job_docker": define_job(demo_slow_graph, "docker"),
                "demo_job_gcs": define_job(demo_graph, "gcs"),
                "demo_job_k8s": define_job(demo_graph, "k8s"),
                "docker_celery_job": define_job(
                    demo_resource_output_graph,
                    "celery_docker",
                    name="docker_celery_job",
                    extra_resources={"resource_with_output": resource_with_output},
                ),
                "fan_in_fan_out_job": define_job(fan_in_fan_out_graph),
                "hanging_job": define_job(hanging_graph),
                "hard_failer_job_celery_k8s": define_job(hard_failer_graph, "celery_k8s"),
                "volume_mount_job_k8s": define_job(volume_mount_graph, "k8s"),
                "large_job_celery": define_job(large_graph, "celery"),
                "long_running_job_celery_k8s": define_job(long_running_graph, "celery_k8s"),
                "optional_outputs_job": define_job(optional_outputs_graph),
                "resources_limit_job_k8s": define_job(
                    resources_limit_graph, "k8s", tags=resources_limit_tags
                ),
                "resources_limit_job_celery_k8s": define_job(
                    resources_limit_graph, "celery_k8s", tags=resources_limit_tags
                ),
                "resource_job_celery_k8s": define_job(
                    resource_graph,
                    "celery_k8s",
                    extra_resources={
                        "s3_resource_with_context_manager": s3_resource_with_context_manager
                    },
                ),
                "retry_job_celery_k8s": define_job(retry_graph, "celery_k8s"),
                "retry_job_k8s": define_job(retry_graph, "k8s"),
                "slow_job_celery_k8s": define_job(slow_graph, "celery_k8s"),
                "slow_job_k8s": define_job(slow_graph, "k8s"),
                "slow_execute_k8s_op_job": define_job(slow_execute_k8s_op_graph),
                "step_retries_job_docker": define_job(step_retries_graph, "docker"),
                "volume_mount_job_celery_k8s": define_job(volume_mount_graph, "celery_k8s"),
                "fails_run_worker_job_docker": define_job(fails_run_worker_graph, "docker"),
            },
            "schedules": define_schedules(),
        }

    return demo_execution_repo
