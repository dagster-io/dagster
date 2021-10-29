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
    InputDefinition,
    Int,
    List,
    ModeDefinition,
    Output,
    OutputDefinition,
    RetryRequested,
    String,
    default_executors,
    file_relative_path,
    fs_io_manager,
    job,
    lambda_solid,
    op,
    pipeline,
    repository,
    resource,
    solid,
    graph,
)
from dagster.core.definitions.decorators import daily_schedule, schedule
from dagster.core.definitions.input import In
from dagster.core.definitions.output import Out
from dagster.core.test_utils import nesting_composite_job, nesting_composite_pipeline
from dagster.utils import merge_dicts, segfault
from dagster.utils.yaml_utils import merge_yamls
from dagster_aws.s3 import s3_pickle_io_manager, s3_resource
from dagster_gcp.gcs import gcs_pickle_io_manager, gcs_resource
from dagster_docker import docker_executor
from dagster_celery import celery_executor
from dagster_celery_k8s import celery_k8s_job_executor
from dagster_k8s.executor import k8s_job_executor


IS_BUILDKITE = bool(os.getenv("BUILDKITE"))


@op(ins={"word": In(String)}, config_schema={"factor": Int})
def multiply_the_word(context, word):
    return word * context.solid_config["factor"]


@op(ins={"word": In(String)}, config_schema={"factor": Int, "sleep_time": Int})
def multiply_the_word_slow(context, word):
    time.sleep(context.solid_config["sleep_time"])
    return word * context.solid_config["factor"]


@op
def count_letters(word):
    counts = defaultdict(int)
    for letter in word:
        counts[letter] += 1
    return dict(counts)


@op
def error_solid():
    raise Exception("Unusual error")


@op
def hanging_solid(_):
    while True:
        time.sleep(0.1)


@job(resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager})
def hanging_pipeline():
    hanging_solid()


@job
def demo_pipeline():
    count_letters(multiply_the_word())


@job(resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager})
def demo_pipeline_s3():
    count_letters(multiply_the_word())


def define_demo_pipeline_docker():
    @job(executor_def=docker_executor)
    def demo_pipeline_docker():
        count_letters(multiply_the_word())

    return demo_pipeline_docker


def define_demo_pipeline_docker_slow():
    @job(executor_def=docker_executor)
    def demo_pipeline_docker_slow():
        count_letters(multiply_the_word_slow())

    return demo_pipeline_docker_slow


@job(executor_def=celery_executor)
def demo_pipeline_celery():
    count_letters(multiply_the_word())


# def define_demo_pipeline_celery():
#     @job(executor_def=celery_executor)
#     def demo_pipeline_celery():
#         count_letters(multiply_the_word())

#     return demo_pipeline_celery


def define_docker_celery_pipeline():
    from dagster_celery_docker import celery_docker_executor

    @job(
        resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager},
        executor_def=celery_docker_executor,
    )
    def docker_celery_pipeline():
        count_letters(multiply_the_word())

    return docker_celery_pipeline


@job(resource_defs={"gcs": gcs_resource, "io_manager": gcs_pickle_io_manager})
def demo_pipeline_gcs():
    count_letters(multiply_the_word())


@job
def demo_error_job():
    error_solid()


@job(resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager})
def demo_error_job_s3():
    error_solid()


@op(
    out={
        "out_1": Out(Int, "out_1", is_required=False),
        "out_2": Out(Int, "out_2", is_required=False),
        "out_3": Out(Int, "out_3", is_required=False),
    }
)
def foo(_):
    yield Output(1, "out_1")


@op
def bar(input_arg):
    return input_arg


@job
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

    @job(executor_def=celery_executor)
    def long_running_pipeline_celery():
        for i in range(10):
            t = long_running_task.alias("first_%d" % i)()
            post_process.alias("post_process_%d" % i)(t)

    return long_running_pipeline_celery


large_pipeline_celery = nesting_composite_job(
    # celery_k8s_job_executor>
    depth=1,
    num_children=6,
    executor_def=celery_executor,
    name="large_pipeline_celery",
)

# def define_large_pipeline_celery():
#     return nesting_composite_job(
#         # celery_k8s_job_executor>
#         depth=1,
#         num_children=6,
#         execute_def=celery_executor,
#         name="large_pipeline_celery",
#     )


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


@graph(
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
def resources_limit_graph():
    resource_req_solid()


resources_limit_celery_job = resources_limit_graph.to_job(
    resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager},
    executor_def=celery_executor,
)


resources_limit_k8s_job = resources_limit_graph.to_job(
    resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager},
    executor_def=k8s_job_executor,
)


def define_schedules():
    @daily_schedule(
        name="daily_optional_outputs",
        pipeline_name=optional_outputs.name,
        start_date=datetime.datetime(2020, 1, 1),
    )
    def daily_optional_outputs(_date):
        return {}

    @schedule(
        job=large_pipeline_celery,  # ??
        # pipeline_name="large_pipeline_celery",
        cron_schedule="*/5 * * * *",
        environment_vars={
            key: os.environ.get(key)
            for key in [
                "DAGSTER_PG_PASSWORD",
                "DAGSTER_K8S_CELERY_BROKER",
                "DAGSTER_K8S_CELERY_BACKEND",
                "DAGSTER_K8S_PIPELINE_RUN_NAMESPACE",
                "DAGSTER_K8S_INSTANCE_CONFIG_MAP",
                "DAGSTER_K8S_PG_PASSWORD_SECRET",
                "DAGSTER_K8S_PIPELINE_RUN_ENV_CONFIGMAP",
                "DAGSTER_K8S_PIPELINE_RUN_IMAGE_PULL_POLICY",
                "KUBERNETES_SERVICE_HOST",
                "KUBERNETES_SERVICE_PORT",
            ]
            if key in os.environ
        },
    )
    def frequent_large_grpc_pipe():
        from dagster_celery_k8s.config import get_celery_engine_grpc_config

        cfg = get_celery_engine_grpc_config()
        cfg["storage"] = {"s3": {"config": {"s3_bucket": "dagster-scratch-80542c2"}}}
        return cfg

    @schedule(
        job=large_pipeline_celery,  # ??
        # pipeline_name="large_pipeline_celery",
        cron_schedule="*/5 * * * *",
        environment_vars={
            key: os.environ.get(key)
            for key in [
                "DAGSTER_PG_PASSWORD",
                "DAGSTER_K8S_CELERY_BROKER",
                "DAGSTER_K8S_CELERY_BACKEND",
                "DAGSTER_K8S_PIPELINE_RUN_IMAGE",
                "DAGSTER_K8S_PIPELINE_RUN_NAMESPACE",
                "DAGSTER_K8S_INSTANCE_CONFIG_MAP",
                "DAGSTER_K8S_PG_PASSWORD_SECRET",
                "DAGSTER_K8S_PIPELINE_RUN_ENV_CONFIGMAP",
                "DAGSTER_K8S_PIPELINE_RUN_IMAGE_PULL_POLICY",
                "KUBERNETES_SERVICE_HOST",
                "KUBERNETES_SERVICE_PORT",
            ]
            if key in os.environ
        },
    )
    def frequent_large_pipe():
        from dagster_celery_k8s.config import get_celery_engine_config

        cfg = get_celery_engine_config()
        cfg["storage"] = {"s3": {"config": {"s3_bucket": "dagster-scratch-80542c2"}}}
        return cfg

    @schedule(
        job=demo_pipeline_celery,  # ??
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
            get_celery_engine_config(additional_env_config_maps=additional_env_config_maps),
        )

    return {
        "daily_optional_outputs": daily_optional_outputs,
        "frequent_large_pipe": frequent_large_pipe,
        "frequent_large_grpc_pipe": frequent_large_grpc_pipe,
        "frequent_celery": frequent_celery,
    }


def define_step_retry_pipeline():
    @op
    def fail_first_time(context):
        event_records = context.instance.all_logs(context.run_id)
        for event_record in event_records:
            context.log.info(event_record.message)
            if "Started re-execution" in event_record.message:
                return "okay perfect"

        raise RetryRequested()

    @job(
        executor_def=celery_executor,
        resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager},
    )
    def retry_pipeline():
        fail_first_time()

    return retry_pipeline


@op
def slow_solid(_):
    time.sleep(100)


@graph()
def slow_graph():
    slow_solid()


slow_celery_job = slow_graph.to_job(
    resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager},
    executor_def=celery_executor,
)


slow_k8s_job = slow_graph.to_job(
    resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager},
    executor_def=k8s_job_executor,
)


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

    @job(
        resource_defs={
            "s3": s3_resource,
            "s3_resource_with_context_manager": s3_resource_with_context_manager,
            "io_manager": s3_pickle_io_manager,
        },
        # ?celery_k8s_job_executor
        executor_def=celery_executor,
    )
    def resource_pipeline():
        super_slow_solid()

    return resource_pipeline


def define_fan_in_fan_out_pipeline():
    @op(output_defs=[OutputDefinition(int)])
    def return_one(_):
        return 1

    @op(input_defs=[InputDefinition("num", int)])
    def add_one_fan(_, num):
        return num + 1

    @op(input_defs=[InputDefinition("nums", List[int])])
    def sum_fan_in(_, nums):
        return sum(nums)

    def construct_fan_in_level(source, level, fanout):
        fan_outs = []
        for i in range(0, fanout):
            fan_outs.append(add_one_fan.alias("add_one_fan_{}_{}".format(level, i))(source))

        return sum_fan_in.alias("sum_{}".format(level))(fan_outs)

    @job(
        resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager},
        # ?celery_k8s_job_executor
        executor_def=celery_executor,
    )
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


@job
def demo_airflow_execution_date_job():
    emit_airflow_execution_date()


@job(resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager})
def demo_airflow_execution_date_job_s3():
    emit_airflow_execution_date()


def define_hard_failer():
    @op(
        config_schema={"fail": Field(Bool, is_required=False, default_value=False)},
        output_defs=[OutputDefinition(Int)],
    )
    def hard_fail_or_0(context):
        if context.solid_config["fail"]:
            segfault()
        return 0

    @op(
        input_defs=[InputDefinition("n", Int)],
    )
    def increment(_, n):
        return n + 1

    @job(
        resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager},
        # ?celery_k8s_job_executor
        executor_def=celery_executor,
    )
    def hard_failer():
        increment(hard_fail_or_0())

    return hard_failer


def define_demo_k8s_executor_pipeline():
    @job(
        resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager},
        executor_def=k8s_job_executor,
    )
    def demo_k8s_executor_pipeline():
        count_letters(multiply_the_word())

    return demo_k8s_executor_pipeline


@op
def check_volume_mount(context):
    with open("/opt/dagster/test_mount_path/volume_mounted_file.yaml", "r") as mounted_file:
        contents = mounted_file.read()
        context.log.info(f"Contents of mounted file: {contents}")
        assert contents == "BAR_CONTENTS"


def define_volume_mount_pipeline():
    @job(
        resource_defs={"s3": s3_resource, "io_manager": s3_pickle_io_manager},
        executor_def=k8s_job_executor,
    )
    def volume_mount_pipeline():
        check_volume_mount()

    return volume_mount_pipeline


def define_demo_execution_repo():
    @repository
    def demo_execution_repo():
        return {
            "jobs": {
                "demo_pipeline_celery": demo_pipeline_celery,
                "demo_pipeline_docker": define_demo_pipeline_docker,
                "demo_pipeline_docker_slow": define_demo_pipeline_docker_slow,
                "large_pipeline_celery": large_pipeline_celery,
                "long_running_pipeline_celery": define_long_running_pipeline_celery,
                "optional_outputs": optional_outputs,
                "demo_pipeline": demo_pipeline,
                "demo_pipeline_s3": demo_pipeline_s3,
                "demo_pipeline_gcs": demo_pipeline_gcs,
                "demo_error_job": demo_error_job,
                "demo_error_job_s3": demo_error_job_s3,
                "resources_limit_celery_job": resources_limit_celery_job,
                "resources_limit_k8s_job": resources_limit_k8s_job,
                "retry_pipeline": define_step_retry_pipeline,
                "slow_celery_job": slow_celery_job,
                "slow_k8s_job": slow_k8s_job,
                "fan_in_fan_out_pipeline": define_fan_in_fan_out_pipeline,
                "resource_pipeline": define_resource_pipeline,
                "docker_celery_pipeline": define_docker_celery_pipeline,
                "demo_airflow_execution_date_job": demo_airflow_execution_date_job,
                "demo_airflow_execution_date_job_s3": demo_airflow_execution_date_job_s3,
                "hanging_pipeline": hanging_pipeline,
                "hard_failer": define_hard_failer,
                "demo_k8s_executor_pipeline": define_demo_k8s_executor_pipeline,
                "volume_mount_pipeline": define_volume_mount_pipeline,
            },
            "schedules": define_schedules(),
        }

    return demo_execution_repo
