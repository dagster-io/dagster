import json
from unittest import mock

import pytest
from dagster import job, op, repository
from dagster._config import process_config, resolve_to_config_type
from dagster._core.definitions.reconstruct import reconstructable
from dagster._core.execution.api import create_execution_plan
from dagster._core.execution.context.system import PlanData, PlanOrchestrationContext
from dagster._core.execution.context_creation_job import create_context_free_log_manager
from dagster._core.execution.retries import RetryMode
from dagster._core.executor.init import InitExecutorContext
from dagster._core.executor.step_delegating.step_handler.base import StepHandlerContext
from dagster._core.remote_representation.handle import RepositoryHandle
from dagster._core.storage.fs_io_manager import fs_io_manager
from dagster._core.test_utils import (
    create_run_for_test,
    environ,
    in_process_test_workspace,
    instance_for_test,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._grpc.types import ExecuteStepArgs
from dagster._utils.hosted_user_process import remote_job_from_recon_job
from dagster_k8s.container_context import K8sContainerContext
from dagster_k8s.executor import _K8S_EXECUTOR_CONFIG_SCHEMA, K8sStepHandler, k8s_job_executor
from dagster_k8s.job import UserDefinedDagsterK8sConfig


@job(
    executor_def=k8s_job_executor,
    resource_defs={"io_manager": fs_io_manager},
)
def bar():
    @op
    def foo():
        return 1

    foo()


RESOURCE_TAGS = {
    "limits": {"cpu": "500m", "memory": "2560Mi"},
    "requests": {"cpu": "250m", "memory": "64Mi"},
}

OTHER_RESOURCE_TAGS = {
    "limits": {"cpu": "1000m", "memory": "1280Mi"},
    "requests": {"cpu": "500m", "memory": "128Mi"},
}


VOLUME_MOUNTS_TAGS = [{"name": "volume1", "mount_path": "foo/bar", "sub_path": "file.txt"}]

OTHER_VOLUME_MOUNTS_TAGS = [{"name": "volume2", "mount_path": "baz/quux", "sub_path": "voom.txt"}]

THIRD_RESOURCES_TAGS = {
    "limits": {"cpu": "5000m", "memory": "2560Mi"},
    "requests": {"cpu": "2500m", "memory": "1280Mi"},
}


@job(
    executor_def=k8s_job_executor,
    resource_defs={"io_manager": fs_io_manager},
)
def bar_with_resources():
    @op(tags={"dagster-k8s/config": {"container_config": {"resources": RESOURCE_TAGS}}})
    def foo():
        return 1

    foo()


@job(
    executor_def=k8s_job_executor,
    resource_defs={"io_manager": fs_io_manager},
    tags={
        "dagster-k8s/config": {
            "container_config": {
                "resources": RESOURCE_TAGS,
                "volume_mounts": VOLUME_MOUNTS_TAGS,
            }
        }
    },
)
def bar_with_tags_in_job_and_op():
    expected_resources = RESOURCE_TAGS
    user_defined_k8s_config_with_resources = UserDefinedDagsterK8sConfig(
        container_config={"resources": expected_resources},
    )
    json.dumps(user_defined_k8s_config_with_resources.to_dict())

    @op(tags={"dagster-k8s/config": {"container_config": {"resources": OTHER_RESOURCE_TAGS}}})
    def foo():
        return 1

    foo()


@job(
    executor_def=k8s_job_executor,
    resource_defs={"io_manager": fs_io_manager},
)
def bar_with_images():
    @op(tags={"dagster-k8s/config": {"container_config": {"image": "new-image"}}})
    def foo():
        return 1

    foo()


@repository
def bar_repo():
    return [bar]


@pytest.fixture
def python_origin_with_container_context():
    container_context_config = {
        "k8s": {
            "env_vars": ["BAZ_TEST=baz_val"],
            "resources": {
                "requests": {"cpu": "256m", "memory": "128Mi"},
                "limits": {"cpu": "1000m", "memory": "2000Mi"},
            },
            "scheduler_name": "my-other-scheduler",
        }
    }

    python_origin = reconstructable(bar).get_python_origin()
    return python_origin._replace(
        repository_origin=python_origin.repository_origin._replace(
            container_context=container_context_config,
        )
    )


@pytest.fixture
def mock_load_incluster_config():
    with mock.patch("kubernetes.config.load_incluster_config") as the_mock:
        yield the_mock


@pytest.fixture
def mock_load_kubeconfig_file():
    with mock.patch("kubernetes.config.load_kube_config") as the_mock:
        yield the_mock


def test_executor_init_without_k8s_run_launcher(
    mock_load_incluster_config, mock_load_kubeconfig_file
):
    with instance_for_test() as instance:  # no k8s run launcher
        _get_executor(
            instance,
            reconstructable(bar),
            {},
        )
        mock_load_incluster_config.assert_called()
        mock_load_kubeconfig_file.assert_not_called()


def test_executor_init_without_k8s_run_launcher_with_config(
    mock_load_incluster_config, mock_load_kubeconfig_file
):
    with instance_for_test() as instance:  # no k8s run launcher
        _get_executor(
            instance,
            reconstructable(bar),
            {"load_incluster_config": False, "kubeconfig_file": "hello_file.py"},
        )
        mock_load_incluster_config.assert_not_called()
        mock_load_kubeconfig_file.assert_called_with("hello_file.py")


def test_executor_init_without_k8s_run_launcher_with_default_kubeconfig(
    mock_load_incluster_config, mock_load_kubeconfig_file
):
    with instance_for_test() as instance:  # no k8s run launcher
        _get_executor(
            instance,
            reconstructable(bar),
            {
                "load_incluster_config": False,
            },
        )
        mock_load_incluster_config.assert_not_called()
        mock_load_kubeconfig_file.assert_called_with(None)


def _get_executor(instance, job_def, executor_config=None):
    process_result = process_config(
        resolve_to_config_type(_K8S_EXECUTOR_CONFIG_SCHEMA),
        executor_config or {},
    )
    assert process_result.success, str(process_result.errors)

    return k8s_job_executor.executor_creation_fn(
        InitExecutorContext(
            job=job_def,
            executor_def=k8s_job_executor,
            executor_config=process_result.value,
            instance=instance,
        )
    )


def _step_handler_context(job_def, dagster_run, instance, executor):
    execution_plan = create_execution_plan(job_def)
    log_manager = create_context_free_log_manager(instance, dagster_run)

    plan_context = PlanOrchestrationContext(
        plan_data=PlanData(
            job=job_def,
            dagster_run=dagster_run,
            instance=instance,
            execution_plan=execution_plan,
            raise_on_error=True,
            retry_mode=RetryMode.DISABLED,
        ),
        log_manager=log_manager,
        executor=executor,
        output_capture=None,
    )

    execute_step_args = ExecuteStepArgs(
        reconstructable(bar).get_python_origin(),
        dagster_run.run_id,
        ["foo"],
        print_serialized_events=False,
    )

    return StepHandlerContext(
        instance=instance,
        plan_context=plan_context,
        steps=execution_plan.steps,
        execute_step_args=execute_step_args,
    )


def test_executor_init_override_in_cluster_config(
    k8s_run_launcher_instance,
    mock_load_incluster_config,
    mock_load_kubeconfig_file,
):
    k8s_run_launcher_instance.run_launcher  # noqa: B018
    mock_load_kubeconfig_file.reset_mock()
    _get_executor(
        k8s_run_launcher_instance,
        reconstructable(bar),
        {
            "env_vars": ["FOO_TEST=foo_val"],
            "scheduler_name": "my-scheduler",
            "load_incluster_config": True,
            "kubeconfig_file": None,
        },
    )
    mock_load_incluster_config.assert_called()
    mock_load_kubeconfig_file.assert_not_called()


def test_executor_init_override_kubeconfig_file(
    k8s_run_launcher_instance,
    mock_load_incluster_config,
    mock_load_kubeconfig_file,
):
    k8s_run_launcher_instance.run_launcher  # noqa: B018
    mock_load_kubeconfig_file.reset_mock()
    _get_executor(
        k8s_run_launcher_instance,
        reconstructable(bar),
        {
            "env_vars": ["FOO_TEST=foo_val"],
            "scheduler_name": "my-scheduler",
            "kubeconfig_file": "fake_file",
        },
    )
    mock_load_incluster_config.assert_not_called()
    mock_load_kubeconfig_file.assert_called_with("fake_file")


def test_executor_init(
    k8s_run_launcher_instance,
    mock_load_incluster_config,
    mock_load_kubeconfig_file,
    kubeconfig_file,
):
    resources = {
        "requests": {"memory": "64Mi", "cpu": "250m"},
        "limits": {"memory": "128Mi", "cpu": "500m"},
    }

    executor = _get_executor(
        k8s_run_launcher_instance,
        reconstructable(bar),
        {
            "env_vars": ["FOO_TEST=foo"],
            "resources": resources,
            "scheduler_name": "my-scheduler",
        },
    )

    mock_load_incluster_config.assert_not_called()
    mock_load_kubeconfig_file.assert_called_with(kubeconfig_file)

    run = create_run_for_test(
        k8s_run_launcher_instance,
        job_name="bar",
        job_code_origin=reconstructable(bar).get_python_origin(),
    )

    step_handler_context = _step_handler_context(
        job_def=reconstructable(bar),
        dagster_run=run,
        instance=k8s_run_launcher_instance,
        executor=executor,
    )

    # env vars from both launcher and the executor

    assert executor._step_handler._get_container_context(  # noqa: SLF001  # noqa: SLF001
        step_handler_context
    ).run_k8s_config.container_config["env"] == [
        {"name": "BAR_TEST", "value": "bar"},
        {"name": "FOO_TEST", "value": "foo"},
    ]

    assert (
        executor._step_handler._get_container_context(  # noqa: SLF001  # noqa: SLF001
            step_handler_context
        ).run_k8s_config.container_config["resources"]
        == resources
    )

    assert (
        executor._step_handler._get_container_context(  # noqa: SLF001  # noqa: SLF001
            step_handler_context
        ).run_k8s_config.pod_spec_config["scheduler_name"]
        == "my-scheduler"
    )


def test_executor_init_container_context(
    k8s_run_launcher_instance, python_origin_with_container_context
):
    executor = _get_executor(
        k8s_run_launcher_instance,
        reconstructable(bar),
        {"env_vars": ["FOO_TEST=foo"], "max_concurrent": 4},
    )

    run = create_run_for_test(
        k8s_run_launcher_instance,
        job_name="bar",
        job_code_origin=python_origin_with_container_context,
    )

    step_handler_context = _step_handler_context(
        job_def=reconstructable(bar),
        dagster_run=run,
        instance=k8s_run_launcher_instance,
        executor=executor,
    )

    # env vars from both launcher and the executor

    assert executor._step_handler._get_container_context(  # noqa: SLF001  # noqa: SLF001
        step_handler_context
    ).run_k8s_config.container_config["env"] == [
        {"name": "BAR_TEST", "value": "bar"},
        {"name": "BAZ_TEST", "value": "baz_val"},
        {"name": "FOO_TEST", "value": "foo"},
    ]
    assert executor._max_concurrent == 4  # noqa: SLF001
    assert (
        executor._step_handler._get_container_context(  # noqa: SLF001  # noqa: SLF001
            step_handler_context
        ).run_k8s_config.container_config["resources"]
        == python_origin_with_container_context.repository_origin.container_context["k8s"][
            "resources"
        ]
    )

    assert (
        executor._step_handler._get_container_context(  # noqa: SLF001  # noqa: SLF001
            step_handler_context
        ).run_k8s_config.pod_spec_config["scheduler_name"]
        == "my-other-scheduler"
    )


@pytest.fixture
def k8s_instance(kubeconfig_file):
    default_config = {
        "service_account_name": "webserver-admin",
        "instance_config_map": "dagster-instance",
        "postgres_password_secret": "dagster-postgresql-secret",
        "dagster_home": "/opt/dagster/dagster_home",
        "job_image": "fake_job_image",
        "load_incluster_config": False,
        "kubeconfig_file": kubeconfig_file,
    }
    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster_k8s",
                "class": "K8sRunLauncher",
                "config": default_config,
            }
        }
    ) as instance:
        yield instance


def test_step_handler(kubeconfig_file, k8s_instance):
    mock_k8s_client_batch_api = mock.MagicMock()
    handler = K8sStepHandler(
        image="bizbuz",
        container_context=K8sContainerContext(
            namespace="foo",
        ),
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
    )

    recon_job = reconstructable(bar)
    loadable_target_origin = LoadableTargetOrigin(python_file=__file__, attribute="bar_repo")

    with instance_for_test() as instance:
        with in_process_test_workspace(instance, loadable_target_origin) as workspace:
            location = workspace.get_code_location(workspace.code_location_names[0])
            repo_handle = RepositoryHandle.from_location(
                repository_name="bar_repo",
                code_location=location,
            )
            fake_remote_job = remote_job_from_recon_job(
                recon_job,
                op_selection=None,
                repository_handle=repo_handle,
            )
            run = create_run_for_test(
                k8s_instance,
                job_name="bar",
                remote_job_origin=fake_remote_job.get_remote_origin(),
                job_code_origin=recon_job.get_python_origin(),
            )
            list(
                handler.launch_step(
                    _step_handler_context(
                        job_def=reconstructable(bar),
                        dagster_run=run,
                        instance=k8s_instance,
                        executor=_get_executor(
                            k8s_instance,
                            reconstructable(bar),
                        ),
                    )
                )
            )

    # Check that user defined k8s config was passed down to the k8s job.
    mock_method_calls = mock_k8s_client_batch_api.method_calls
    assert len(mock_method_calls) > 0
    method_name, _args, kwargs = mock_method_calls[0]
    assert method_name == "create_namespaced_job"
    assert kwargs["body"].spec.template.spec.containers[0].image == "bizbuz"
    assert kwargs["body"].spec.template.spec.automount_service_account_token

    # appropriate labels applied
    labels = kwargs["body"].spec.template.metadata.labels
    assert labels["dagster/code-location"] == "in_process"
    assert labels["dagster/job"] == "bar"
    assert labels["dagster/run-id"] == run.run_id


def test_step_handler_user_defined_config(kubeconfig_file, k8s_instance):
    mock_k8s_client_batch_api = mock.MagicMock()
    with environ({"FOO_TEST": "bar"}):
        handler = K8sStepHandler(
            image="bizbuz",
            container_context=K8sContainerContext(
                namespace="foo",
                env_vars=["FOO_TEST"],
                resources={
                    "requests": {"cpu": "128m", "memory": "64Mi"},
                    "limits": {"cpu": "500m", "memory": "1000Mi"},
                },
            ),
            load_incluster_config=False,
            kubeconfig_file=kubeconfig_file,
            k8s_client_batch_api=mock_k8s_client_batch_api,
        )

        run = create_run_for_test(
            k8s_instance,
            job_name="bar",
            job_code_origin=reconstructable(bar_with_resources).get_python_origin(),
        )
        list(
            handler.launch_step(
                _step_handler_context(
                    job_def=reconstructable(bar_with_resources),
                    dagster_run=run,
                    instance=k8s_instance,
                    executor=_get_executor(
                        k8s_instance,
                        reconstructable(bar_with_resources),
                    ),
                )
            )
        )

        # Check that user defined k8s config was passed down to the k8s job.
        mock_method_calls = mock_k8s_client_batch_api.method_calls
        assert len(mock_method_calls) > 0
        method_name, _args, kwargs = mock_method_calls[0]
        assert method_name == "create_namespaced_job"
        assert kwargs["body"].spec.template.spec.containers[0].image == "bizbuz"
        job_resources = kwargs["body"].spec.template.spec.containers[0].resources.to_dict()
        job_resources.pop("claims", None)
        assert job_resources == RESOURCE_TAGS

        env_vars = {
            env.name: env.value for env in kwargs["body"].spec.template.spec.containers[0].env
        }
        assert env_vars["FOO_TEST"] == "bar"


def test_step_handler_image_override(kubeconfig_file, k8s_instance):
    mock_k8s_client_batch_api = mock.MagicMock()
    handler = K8sStepHandler(
        image="bizbuz",
        container_context=K8sContainerContext(namespace="foo"),
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
    )

    run = create_run_for_test(
        k8s_instance,
        job_name="bar",
        job_code_origin=reconstructable(bar_with_images).get_python_origin(),
    )
    list(
        handler.launch_step(
            _step_handler_context(
                job_def=reconstructable(bar_with_images),
                dagster_run=run,
                instance=k8s_instance,
                executor=_get_executor(
                    k8s_instance,
                    reconstructable(bar_with_images),
                ),
            )
        )
    )

    # Check that user defined k8s config was passed down to the k8s job.
    mock_method_calls = mock_k8s_client_batch_api.method_calls
    assert len(mock_method_calls) > 0
    method_name, _args, kwargs = mock_method_calls[0]
    assert method_name == "create_namespaced_job"
    assert kwargs["body"].spec.template.spec.containers[0].image == "new-image"


def test_step_handler_with_container_context(
    kubeconfig_file, k8s_instance, python_origin_with_container_context
):
    with environ({"FOO_TEST": "bar"}):
        mock_k8s_client_batch_api = mock.MagicMock()
        handler = K8sStepHandler(
            image="bizbuz",
            container_context=K8sContainerContext(
                namespace="foo",
                env_vars=["FOO_TEST"],
            ),
            load_incluster_config=False,
            kubeconfig_file=kubeconfig_file,
            k8s_client_batch_api=mock_k8s_client_batch_api,
        )

        # Additional env vars come from container context on the run
        run = create_run_for_test(
            k8s_instance,
            job_name="bar",
            job_code_origin=python_origin_with_container_context,
        )
        list(
            handler.launch_step(
                _step_handler_context(
                    job_def=reconstructable(bar),
                    dagster_run=run,
                    instance=k8s_instance,
                    executor=_get_executor(
                        k8s_instance,
                        reconstructable(bar),
                    ),
                )
            )
        )

        # Check that user defined k8s config was passed down to the k8s job.
        mock_method_calls = mock_k8s_client_batch_api.method_calls
        assert len(mock_method_calls) > 0
        method_name, _args, kwargs = mock_method_calls[0]
        assert method_name == "create_namespaced_job"
        assert kwargs["body"].spec.template.spec.containers[0].image == "bizbuz"

        envs = {env.name: env.value for env in kwargs["body"].spec.template.spec.containers[0].env}

        assert envs["FOO_TEST"] == "bar"
        assert envs["BAZ_TEST"] == "baz_val"


def test_step_raw_k8s_config_inheritance(
    k8s_run_launcher_instance, python_origin_with_container_context
):
    container_context_config = {
        "k8s": {
            "run_k8s_config": {"container_config": {"volume_mounts": OTHER_VOLUME_MOUNTS_TAGS}},
        }
    }

    python_origin = reconstructable(bar_with_tags_in_job_and_op).get_python_origin()

    python_origin_with_container_context = python_origin._replace(
        repository_origin=python_origin.repository_origin._replace(
            container_context=container_context_config
        )
    )

    # Verifies that raw k8s config for step pods is pulled from the container context and
    # executor-level config and dagster-k8s/config tags on the op, but *not* from tags on the job
    executor = _get_executor(
        k8s_run_launcher_instance,
        reconstructable(bar_with_tags_in_job_and_op),
        {
            "step_k8s_config": {  # injected into every step
                "container_config": {
                    "working_dir": "MY_WORKING_DIR",  # set on every step
                    "resources": THIRD_RESOURCES_TAGS,  # overridden at the op level, so ignored
                }
            }
        },
    )

    run = create_run_for_test(
        k8s_run_launcher_instance,
        job_name="bar_with_tags_in_job_and_op",
        job_code_origin=python_origin_with_container_context,
    )

    step_handler_context = _step_handler_context(
        job_def=reconstructable(bar_with_tags_in_job_and_op),
        dagster_run=run,
        instance=k8s_run_launcher_instance,
        executor=executor,
    )

    container_context = executor._step_handler._get_container_context(  # noqa: SLF001
        step_handler_context
    )

    raw_k8s_config = container_context.run_k8s_config

    assert raw_k8s_config.container_config["resources"] == OTHER_RESOURCE_TAGS
    assert raw_k8s_config.container_config["working_dir"] == "MY_WORKING_DIR"
    assert raw_k8s_config.container_config["volume_mounts"] == OTHER_VOLUME_MOUNTS_TAGS
