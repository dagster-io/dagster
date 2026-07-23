import logging
import re
import time
from contextlib import contextmanager
from unittest import mock
from unittest.mock import Mock

import pytest
from dagster._core.test_utils import instance_for_test
from dagster._utils.merger import merge_dicts
from dagster_cloud.workspace.kubernetes.launcher import (
    DEFAULT_DEPLOYMENT_STARTUP_TIMEOUT,
    DEFAULT_IMAGE_PULL_GRACE_PERIOD,
    K8sUserCodeLauncher,
)
from dagster_cloud.workspace.kubernetes.utils import (
    DEFS_STATE_CONFIG_MAP_NAME_PREFIX,
    DEFS_STATE_MOUNT_PATH,
    DEFS_STATE_OVERRIDE_ENV,
    DEFS_STATE_OVERRIDE_FILENAME,
    DEFS_STATE_VOLUME_NAME,
    SERVER_SPEC_VERSION_LABEL_KEY,
    SERVER_SPEC_VERSION_V2,
    construct_code_location_deployment,
    construct_code_location_service,
    construct_defs_state_config_map,
    defs_state_config_map_name,
    get_deployment_failure_debug_info,
    get_k8s_human_readable_label,
    unique_k8s_resource_name,
)
from dagster_cloud.workspace.user_code_launcher import (
    DEFAULT_SERVER_PROCESS_STARTUP_TIMEOUT,
    DagsterCloudGrpcServer,
    UserCodeLauncherEntry,
)
from dagster_cloud_cli.core.workspace import CodeLocationDeployData
from dagster_k8s.container_context import K8sContainerContext
from dagster_k8s.job import UserDefinedDagsterK8sConfig
from kubernetes.client.rest import ApiException


def test_config():
    assert K8sUserCodeLauncher.config_type()


# From the failure you get when you make a k8s deployment with an invalid nmae
K8S_SERVICE_REGEX = "[a-z]([-a-z0-9]*[a-z0-9])?"

MINIMAL_KUBECONFIG_CONTENT = """
apiVersion: v1
kind: Config

current-context: fake-context
contexts:
  - context:
      cluster: fake-cluster
    name: fake-context
clusters:
  - cluster: {}
    name: fake-cluster
"""


@pytest.fixture
def kubeconfig_file(tmp_path):
    """Returns a str file path for a minimal kubeconfig file in the default location (~/.kube/config)."""
    dir_path = tmp_path / ".kube"
    dir_path.mkdir()
    config_path = dir_path / "config"
    config_path.write_text(MINIMAL_KUBECONFIG_CONTENT)
    return str(config_path)


@contextmanager
def k8s_instance(user_code_launcher_overrides=None):
    with mock.patch("kubernetes.config.load_incluster_config"):
        with instance_for_test(
            {
                "instance_class": {
                    "module": "dagster_cloud",
                    "class": "DagsterCloudAgentInstance",
                },
                "user_code_launcher": {
                    "module": "dagster_cloud.workspace.kubernetes",
                    "class": "K8sUserCodeLauncher",
                    "config": merge_dicts(
                        {
                            "dagster_home": "MY_DAGSTER_HOME",
                            "instance_config_map": "MY_INSTANCE_CONFIG_MAP",
                            "service_account_name": "MY_SERVICE_ACCOUNT_NAME",
                        },
                        user_code_launcher_overrides or {},
                    ),
                },
                "dagster_cloud_api": {
                    "url": "http://localhost:2874",
                    "agent_token": "FAKE_TOKEN",
                },
                "compute_logs": {
                    "module": "dagster._core.storage.noop_compute_log_manager",
                    "class": "NoOpComputeLogManager",
                },
            }
        ) as instance:
            yield instance


def test_default_instance():
    with k8s_instance() as instance:
        assert (
            instance.user_code_launcher._deployment_startup_timeout  # noqa: SLF001
            == DEFAULT_DEPLOYMENT_STARTUP_TIMEOUT
        )
        assert (
            instance.user_code_launcher._server_process_startup_timeout  # noqa: SLF001
            == DEFAULT_SERVER_PROCESS_STARTUP_TIMEOUT
        )

        assert (
            instance.user_code_launcher._image_pull_grace_period  # noqa: SLF001
            == DEFAULT_IMAGE_PULL_GRACE_PERIOD
        )

        assert instance.user_code_launcher._labels == {}  # noqa: SLF001
        assert instance.user_code_launcher._resources == {}  # noqa: SLF001


def test_timeout_overrides():
    with k8s_instance(
        {
            "deployment_startup_timeout": 123,
            "server_process_startup_timeout": 456,
            "image_pull_grace_period": 789,
        }
    ) as instance:
        assert instance.user_code_launcher._deployment_startup_timeout == 123  # noqa: SLF001
        assert instance.user_code_launcher._server_process_startup_timeout == 456  # noqa: SLF001
        assert instance.user_code_launcher._image_pull_grace_period == 789  # noqa: SLF001


def test_labels():
    with k8s_instance({"labels": {"foo": "bar"}}) as instance:
        assert instance.user_code_launcher._labels == {"foo": "bar"}  # noqa: SLF001


def test_env_vars():
    env_vars = ["FOO_ENV_VAR", "BAR_ENV_VAR=BAR_VALUE"]

    with k8s_instance({"env_vars": env_vars}) as instance:
        assert instance.user_code_launcher._env_vars == env_vars  # noqa: SLF001


def test_volumes_instance():
    with k8s_instance(
        {
            "volume_mounts": [{"name": "foo", "mountPath": "biz/buz", "subPath": "file.txt"}],
            "volumes": [
                {"name": "foo", "configMap": {"name": "settings-cm"}},
            ],
        }
    ) as instance:
        assert instance.user_code_launcher._volume_mounts == [  # noqa: SLF001
            {
                "name": "foo",
                "mount_path": "biz/buz",
                "sub_path": "file.txt",
            }
        ]
        assert instance.user_code_launcher._volumes == [  # noqa: SLF001
            {"name": "foo", "config_map": {"name": "settings-cm"}}
        ]


def test_resources_instance():
    resources = {
        "requests": {"cpu": "250m", "memory": "64Mi"},
        "limits": {"cpu": "500m", "memory": "2560Mi"},
    }
    with k8s_instance({"resources": resources}) as instance:
        assert instance.user_code_launcher._resources == resources  # noqa: SLF001


def test_security_context_instance():
    sacred_rites_of_debugging = {"capabilities": {"add": ["SYS_PTRACE"]}}

    with k8s_instance({"security_context": sacred_rites_of_debugging}) as instance:
        assert (
            instance.user_code_launcher._security_context  # noqa: SLF001
            == sacred_rites_of_debugging
        )


def test_sanitize_k8s_name():
    assert "foobar-sandbox-" in unique_k8s_resource_name("SandBox", "fOo_bAr")
    assert "!" not in unique_k8s_resource_name("sandbox", "sillyname!")
    assert len(unique_k8s_resource_name("sandbox", "extralong name" * 100)) <= 63
    assert "-location" not in unique_k8s_resource_name("hyphen", "-location")

    assert re.match(K8S_SERVICE_REGEX, unique_k8s_resource_name("sandbox", "foo_bar"))
    assert re.match(K8S_SERVICE_REGEX, unique_k8s_resource_name("22fast2furious", "33-iscompany"))

    assert "iscompany-22fast2furious" in unique_k8s_resource_name("22fast2furious", "33-iscompany")

    assert re.match(K8S_SERVICE_REGEX, unique_k8s_resource_name("222", "333"))


def test_get_k8s_human_readable_label():
    assert get_k8s_human_readable_label("foo_bar") == "foo_bar"
    assert "!" not in get_k8s_human_readable_label("sillyname!")


def test_construct_code_location_service():
    resource_name = unique_k8s_resource_name("sandbox", "biz.buz")

    container_context = K8sContainerContext(
        labels={"foo_label": "bar"},
        server_k8s_config=UserDefinedDagsterK8sConfig.from_dict(
            {
                "service_metadata": {
                    "annotations": {"foo_service": "bar"},
                    "labels": {"extra_label": "extra_value"},
                },
                "service_spec_config": {"cluster_ip": "None"},
            }
        ),
    )

    with k8s_instance() as instance:
        server_timestamp = time.time()

        obj = construct_code_location_service(
            "sandbox",
            "biz.buz",
            resource_name,
            container_context,
            instance,
            server_timestamp,
        ).to_dict()

        assert obj
        assert obj["metadata"]["name"] == resource_name
        assert obj["metadata"]["labels"]["foo_label"] == "bar"
        assert obj["metadata"]["labels"]["managed_by"] == "K8sUserCodeLauncher"
        assert obj["metadata"]["labels"]["location_name"] == "biz.buz"
        assert obj["metadata"]["labels"]["agent_id"] == instance.instance_uuid
        assert obj["metadata"]["labels"]["server_timestamp"] == str(server_timestamp)
        assert obj["metadata"]["labels"]["extra_label"] == "extra_value"

        assert obj["metadata"]["annotations"] == {"foo_service": "bar"}
        assert obj["spec"]["cluster_ip"] == "None"


def test_construct_code_location_service_with_service_spec_config():
    resource_name = unique_k8s_resource_name("sandbox", "biz.buz")

    container_context = K8sContainerContext(
        server_k8s_config=UserDefinedDagsterK8sConfig.from_dict(
            {
                "service_spec_config": {"cluster_ip": "None"},
            }
        ),
    )

    with k8s_instance() as instance:
        server_timestamp = time.time()

        obj = construct_code_location_service(
            "sandbox",
            "biz.buz",
            resource_name,
            container_context,
            instance,
            server_timestamp,
        ).to_dict()

        assert obj
        assert obj["spec"]["cluster_ip"] == "None"
        assert obj["spec"]["selector"] == {"user-deployment": resource_name}
        assert obj["spec"]["ports"][0]["name"] == "grpc"
        assert obj["spec"]["ports"][0]["protocol"] == "TCP"


def test_construct_code_location_deployment():
    resource_name = unique_k8s_resource_name("sandbox", "foobar")

    container_context = K8sContainerContext(
        image_pull_policy="IfNotPresent",
        env_secrets=["dagster-cloud-agent-token"],
        env_config_maps=["user-config-map"],
        service_account_name="dagster",
        image_pull_secrets=[{"name": "test-image-pull-secret"}],
        volume_mounts=[{"name": "foo", "mount_path": "biz/buz", "sub_path": "file.txt"}],
        volumes=[
            {"name": "foo", "config_map": {"name": "settings-cm"}},
        ],
        labels={"foo_label": "bar"},
        resources={
            "requests": {"cpu": "250m", "memory": "64Mi"},
            "limits": {"cpu": "500m", "memory": "2560Mi"},
        },
    )

    with k8s_instance() as instance:
        server_timestamp = time.time()
        obj = construct_code_location_deployment(
            instance,
            deployment_name="sandbox",
            location_name="foobar_",
            k8s_deployment_name=resource_name,
            metadata=CodeLocationDeployData("bizbuz", package_name="blim"),
            container_context=container_context,
            args=["ls"],
            server_timestamp=server_timestamp,
        ).to_dict()

        assert obj
        assert obj["metadata"]["name"] == resource_name
        assert obj["metadata"]["labels"]["foo_label"] == "bar"
        assert obj["metadata"]["labels"]["managed_by"] == "K8sUserCodeLauncher"
        assert obj["metadata"]["labels"]["location_name"] == "foobar"
        assert obj["metadata"]["labels"]["agent_id"] == instance.instance_uuid
        assert obj["metadata"]["labels"]["server_timestamp"] == str(server_timestamp)

        assert len(obj["spec"]["template"]["spec"]["containers"]) == 1

        assert obj["spec"]["template"]["metadata"]["labels"]["foo_label"] == "bar"
        assert obj["spec"]["template"]["metadata"]["labels"]["managed_by"] == "K8sUserCodeLauncher"
        assert obj["spec"]["template"]["metadata"]["labels"]["location_name"] == "foobar"
        assert obj["spec"]["template"]["metadata"]["labels"]["agent_id"] == instance.instance_uuid

        assert obj["spec"]["template"]["spec"]["containers"][0]["image"] == "bizbuz"
        assert (
            obj["spec"]["template"]["spec"]["containers"][0]["image_pull_policy"] == "IfNotPresent"
        )

        assert len(obj["spec"]["template"]["spec"]["containers"][0]["env_from"]) == 2
        assert (
            obj["spec"]["template"]["spec"]["containers"][0]["env_from"][0]["config_map_ref"][
                "name"
            ]
            == "user-config-map"
        )
        assert (
            obj["spec"]["template"]["spec"]["containers"][0]["env_from"][1]["secret_ref"]["name"]
            == "dagster-cloud-agent-token"
        )

        assert obj["spec"]["template"]["spec"]["containers"][0]["args"] == ["ls"]
        assert obj["spec"]["template"]["spec"]["service_account_name"] == "dagster"
        assert obj["spec"]["template"]["spec"]["image_pull_secrets"] == [
            {"name": "test-image-pull-secret"}
        ]

        assert len(obj["spec"]["template"]["spec"]["volumes"]) == 1
        foo_volumes = [
            volume
            for volume in obj["spec"]["template"]["spec"]["volumes"]
            if volume["name"] == "foo"
        ]
        assert len(foo_volumes) == 1
        assert foo_volumes[0]["config_map"]["name"] == "settings-cm"

        assert len(obj["spec"]["template"]["spec"]["containers"][0]["volume_mounts"]) == 1
        foo_volumes_mounts = [
            volume
            for volume in obj["spec"]["template"]["spec"]["containers"][0]["volume_mounts"]
            if volume["name"] == "foo"
        ]
        assert len(foo_volumes_mounts) == 1

        assert obj["spec"]["template"]["spec"]["scheduler_name"] is None

        with pytest.raises(
            Exception, match=r"Unexpected keys in model class V1Volume: {'invalid_key'}"
        ):
            container_context = K8sContainerContext(
                image_pull_policy="IfNotPresent",
                env_secrets=["dagster-cloud-agent-token"],
                env_config_maps=["user-config-map"],
                service_account_name="dagster",
                image_pull_secrets=[{"name": "test-image-pull-secret"}],
                volume_mounts=[{"name": "foo", "mount_path": "biz/buz", "sub_path": "file.txt"}],
                volumes=[
                    {"name": "foo", "invalid_key": "settings-secret"},
                ],
                labels={},
                resources={},
            )
            construct_code_location_deployment(  # ty: ignore[missing-argument]
                instance,
                deployment_name="sandbox",
                location_name="foobar_",
                k8s_deployment_name=resource_name,
                metadata=CodeLocationDeployData("bizbuz", package_name="blim"),
                container_context=container_context,
                server_timestamp=time.time(),
            )


def test_construct_code_location_deployment_scheduler_name():
    resource_name = unique_k8s_resource_name("sandbox", "foobar")
    with k8s_instance() as instance:
        container_context = K8sContainerContext(
            image_pull_policy="IfNotPresent",
            env_secrets=["dagster-cloud-agent-token"],
            env_config_maps=["user-config-map"],
            service_account_name="dagster",
            image_pull_secrets=[{"name": "test-image-pull-secret"}],
            volume_mounts=[{"name": "foo", "mount_path": "biz/buz", "sub_path": "file.txt"}],
            volumes=[
                {"name": "foo", "config_map": {"name": "settings-cm"}},
            ],
            labels={"foo_label": "bar"},
            resources={
                "requests": {"cpu": "250m", "memory": "64Mi"},
                "limits": {"cpu": "500m", "memory": "2560Mi"},
            },
            scheduler_name="test-scheduler",
        )
        obj = construct_code_location_deployment(
            instance,
            deployment_name="sandbox",
            location_name="foobar_",
            k8s_deployment_name=resource_name,
            metadata=CodeLocationDeployData("bizbuz", package_name="blim"),
            container_context=container_context,
            args=["ls"],
            server_timestamp=time.time(),
        ).to_dict()

        assert obj
        assert obj["spec"]["template"]["spec"]["scheduler_name"] == "test-scheduler"


def test_construct_code_location_deployment_security_context():
    resource_name = unique_k8s_resource_name("sandbox", "foobar")
    with k8s_instance() as instance:
        container_context = K8sContainerContext(
            image_pull_policy="IfNotPresent",
            env_secrets=["dagster-cloud-agent-token"],
            env_config_maps=["user-config-map"],
            service_account_name="dagster",
            image_pull_secrets=[{"name": "test-image-pull-secret"}],
            volume_mounts=[{"name": "foo", "mount_path": "biz/buz", "sub_path": "file.txt"}],
            volumes=[
                {"name": "foo", "config_map": {"name": "settings-cm"}},
            ],
            labels={"foo_label": "bar"},
            resources={
                "requests": {"cpu": "250m", "memory": "64Mi"},
                "limits": {"cpu": "500m", "memory": "2560Mi"},
            },
            security_context={"capabilities": {"add": ["SYS_PTRACE"]}},
        )
        obj = construct_code_location_deployment(
            instance,
            deployment_name="sandbox",
            location_name="foobar_",
            k8s_deployment_name=resource_name,
            metadata=CodeLocationDeployData("bizbuz", package_name="blim"),
            container_context=container_context,
            args=["ls"],
            server_timestamp=time.time(),
        ).to_dict()

        assert obj
        assert obj["spec"]["template"]["spec"]["containers"][0]["security_context"]["capabilities"][
            "add"
        ] == ["SYS_PTRACE"]


def test_construct_code_location_deployment_with_raw_k8s_config():
    resource_name = unique_k8s_resource_name("sandbox", "foobar")
    with k8s_instance() as instance:
        container_context = K8sContainerContext(
            image_pull_policy="IfNotPresent",
            env_secrets=["dagster-cloud-agent-token"],
            env_config_maps=["user-config-map"],
            service_account_name="dagster",
            image_pull_secrets=[{"name": "test-image-pull-secret"}],
            volume_mounts=[{"name": "foo", "mount_path": "biz/buz", "sub_path": "file.txt"}],
            volumes=[
                {"name": "foo", "config_map": {"name": "settings-cm"}},
            ],
            labels={"foo_label": "bar"},
            resources={
                "requests": {"cpu": "250m", "memory": "64Mi"},
                "limits": {"cpu": "500m", "memory": "2560Mi"},
            },
            scheduler_name="the_scheduler_name",
            server_k8s_config=UserDefinedDagsterK8sConfig.from_dict(
                {
                    "container_config": {
                        "name": "fooba",
                        "command": ["echo", "SERVER_OVERRIDE"],
                        "env": [{"name": "extra_key", "value": "extra_value"}],
                        "env_from": [{"config_map_ref": {"name": "that_config_map"}}],
                        "volume_mounts": [
                            {"name": "other_foo", "mount_path": "baz/boz", "sub_path": "foo.txt"}
                        ],
                        "resources": {
                            "requests": {"cpu": "500m", "memory": "128Mi"},
                            "limits": {"cpu": "250m", "memory": "5120Mi"},
                        },
                        "security_context": {"capabilities": {"add": ["SYS_PTRACE"]}},
                    },
                    "pod_template_spec_metadata": {
                        "namespace": "my_override_namespace",
                        "labels": {"my_other_label": "baz"},
                    },
                    "pod_spec_config": {
                        "dns_policy": "server_override_value",
                        "containers": [{"image": "sidecar_image", "name": "the_sidecar"}],
                        "image_pull_secrets": [{"name": "other-image-pull-secret"}],
                        "service_account_name": "other-service-account-name",
                        "volumes": [{"name": "other_foo", "config_map": {"name": "other-cm"}}],
                        "scheduler_name": "my_custom_scheduler_name",
                    },
                    "service_metadata": {"annotations": {"foo_service": "bar"}},
                    "service_spec_config": {"cluster_ip": "None"},
                    "deployment_metadata": {"annotations": {"foo_deployment": "baz"}},
                }
            ),
        )
        obj = construct_code_location_deployment(
            instance,
            deployment_name="sandbox",
            location_name="foobar_",
            k8s_deployment_name=resource_name,
            metadata=CodeLocationDeployData("bizbuz", package_name="blim"),
            container_context=container_context,
            args=["ls"],
            server_timestamp=time.time(),
        ).to_dict()

        assert obj

        deployment_metadata = obj["metadata"]
        assert deployment_metadata["annotations"] == {
            "foo_deployment": "baz",
        }

        pod_spec = obj["spec"]["template"]["spec"]
        assert pod_spec["dns_policy"] == "server_override_value"
        assert pod_spec["image_pull_secrets"][0]["name"] == "test-image-pull-secret"
        assert pod_spec["image_pull_secrets"][1]["name"] == "other-image-pull-secret"
        assert pod_spec["service_account_name"] == "other-service-account-name"
        assert pod_spec["scheduler_name"] == "my_custom_scheduler_name"

        assert pod_spec["volumes"][1]["name"] == "other_foo"

        containers = pod_spec["containers"]
        assert len(containers) == 2

        assert containers[1]["name"] == "the_sidecar"
        assert containers[1]["image"] == "sidecar_image"

        container = containers[0]

        assert container["name"] == "fooba"
        assert container["command"] == ["echo", "SERVER_OVERRIDE"]

        envs = {env["name"]: env["value"] for env in container["env"]}
        assert envs["extra_key"] == "extra_value"

        assert container["env_from"][2]["config_map_ref"]["name"] == "that_config_map"
        assert {
            "name": "other_foo",
            "mount_path": "baz/boz",
            "sub_path": "foo.txt",
        }.items() <= container["volume_mounts"][1].items()
        container["resources"].pop("claims", None)
        assert container["resources"] == {
            "requests": {"cpu": "500m", "memory": "128Mi"},
            "limits": {"cpu": "250m", "memory": "5120Mi"},
        }

        assert container["security_context"]["capabilities"]["add"] == ["SYS_PTRACE"]

        pod_metadata = obj["spec"]["template"]["metadata"]
        assert pod_metadata["namespace"] == "my_override_namespace"
        assert pod_metadata["labels"]["my_other_label"] == "baz"


def test_launch_k8s_server(kubeconfig_file):
    mock_k8s_apps_api_client = mock.MagicMock()
    mock_k8s_core_api_client = mock.MagicMock()
    with k8s_instance() as instance:
        user_code_launcher = K8sUserCodeLauncher(
            dagster_home="/opt/dagster/dagster_home",
            instance_config_map="dagster-instance",
            service_account_name="MY_SERVICE_ACCOUNT_NAME",
            namespace="default",
            kubeconfig_file=kubeconfig_file,
            k8s_apps_api_client=mock_k8s_apps_api_client,
            k8s_core_api_client=mock_k8s_core_api_client,
            server_k8s_config={
                "container_config": {"command": ["echo", "SERVER"], "tty": True},
                "pod_template_spec_metadata": {
                    "namespace": "my_server_namespace",
                    "labels": {"foo": "bar"},
                },
                "pod_spec_config": {"dns_policy": "server_value"},
                "deployment_metadata": {"annotations": {"foo_deployment": "bar_value"}},
                "service_metadata": {"annotations": {"foo_service": "bar_value"}},
                "service_spec_config": {"cluster_ip": "None"},
            },
            run_k8s_config={
                "container_config": {"command": ["echo", "RUN"]},
                "pod_template_spec_metadata": {"namespace": "my_run_namespace"},
                "pod_spec_config": {"dns_policy": "run_value"},
            },
            only_allow_user_defined_k8s_config_fields={
                "container_config": {
                    "command": True,
                },
                "pod_template_spec_metadata": {"labels": True},
                "pod_spec_config": {
                    "dns_policy": True,
                },
                "deployment_metadata": {"annotations": True},
                "service_metadata": {"annotations": True},
                "service_spec_config": {"cluster_ip": True},
                "namespace": True,
            },
            only_allow_user_defined_env_vars=["FOO", "BAR"],
        )
        user_code_launcher.register_instance(instance)

        user_code_launcher._start_new_server_spinup(  # noqa: SLF001
            deployment_name="acme",
            location_name="sandbox",
            desired_entry=UserCodeLauncherEntry(
                CodeLocationDeployData("bizbuz", package_name="blim"), time.time()
            ),
        )

        mock_method_calls = mock_k8s_apps_api_client.method_calls
        assert len(mock_method_calls) > 0
        method_name, _args, kwargs = mock_method_calls[0]
        assert method_name == "create_namespaced_deployment"

        body = kwargs["body"].to_dict()

        pod_spec = body["spec"]["template"]["spec"]
        pod_metadata = body["spec"]["template"]["metadata"]

        container = pod_spec["containers"][0]

        assert container["image"] == "bizbuz"
        assert container["command"] == ["echo", "SERVER"]

        assert pod_spec["dns_policy"] == "server_value"
        assert pod_metadata["namespace"] == "my_server_namespace"

        # Verify service creation includes service_spec_config. Index by name —
        # the core client also sees `create_namespaced_config_map` for the
        # defs_state override mount, so positional indexing is brittle.
        service_method_calls = mock_k8s_core_api_client.method_calls
        service_create = next(
            c for c in service_method_calls if c[0] == "create_namespaced_service"
        )
        _, service_args, _service_kwargs = service_create
        service_body = service_args[1].to_dict()
        assert service_body["spec"]["cluster_ip"] == "None"

        assert (
            user_code_launcher.run_launcher().run_k8s_config == user_code_launcher._run_k8s_config  # noqa: SLF001
        )

        # code server allowlist fields not included on run launcher
        assert user_code_launcher.run_launcher().only_allow_user_defined_k8s_config_fields == {
            "container_config": {"command": True, "env": True},
            "namespace": True,
            "pod_spec_config": {"dns_policy": True},
            "pod_template_spec_metadata": {"labels": True},
        }

        # Disallowed raw k8s fields are rejected
        with pytest.raises(
            Exception,
            match=r"Attempted to create a pod with fields that violated the allowed list: pod_template_spec_metadata.annotations",
        ):
            user_code_launcher._start_new_server_spinup(  # noqa: SLF001
                deployment_name="acme",
                location_name="sandbox",
                desired_entry=UserCodeLauncherEntry(
                    CodeLocationDeployData(
                        "bizbuz",
                        package_name="blim",
                        container_context={
                            "k8s": {
                                "server_k8s_config": {
                                    "pod_template_spec_metadata": {
                                        "annotations": {"foo_annot": "bar_annot"}
                                    }
                                }
                            }
                        },
                    ),
                    time.time(),
                ),
            )

        # Allowlisted raw k8s fields are allowed

        user_code_launcher._start_new_server_spinup(  # noqa: SLF001
            deployment_name="acme",
            location_name="sandbox",
            desired_entry=UserCodeLauncherEntry(
                CodeLocationDeployData(
                    "bizbuz",
                    package_name="blim",
                    container_context={
                        "env_vars": ["DAGSTER_CLOUD_LOCATION_NAME=sandbox"],
                        "k8s": {
                            "namespace": "my_override_namespace",
                            "server_k8s_config": {
                                "container_config": {
                                    "command": ["echo", "SERVER_OVERRIDE"],
                                    "env": [
                                        {"name": "FOO", "value": "FOO_VAL"},
                                        {"name": "BAZ", "value": "BAZ_VAL"},
                                        {"name": "BAR", "value": "BAR_VAL"},
                                    ],
                                },
                                "pod_template_spec_metadata": {
                                    "labels": {"baz": "quux"},
                                },
                                "pod_spec_config": {"dns_policy": "server_override_value"},
                            },
                        },
                    },
                ),
                time.time(),
            ),
        )

        # server_k8s_config values on the code location override the ones on the instance config

        mock_method_calls = mock_k8s_apps_api_client.method_calls
        method_name, _args, kwargs = mock_method_calls[1]
        assert method_name == "create_namespaced_deployment"

        namespace = kwargs["namespace"]
        assert namespace == "my_override_namespace"

        body = kwargs["body"].to_dict()

        pod_spec = body["spec"]["template"]["spec"]
        pod_metadata = body["spec"]["template"]["metadata"]

        container = pod_spec["containers"][0]

        assert container["command"] == ["echo", "SERVER_OVERRIDE"]
        assert container[
            "tty"
        ]  # still keeps keys from the instance config if they weren't supplied
        env_names = {env["name"] for env in container["env"]}
        assert {"FOO", "BAR", "DAGSTER_CLOUD_LOCATION_NAME"} <= env_names

        # "BAZ" excluded since it wasn't in the only_allow_user_defined_env_vars list
        assert "BAZ" not in env_names

        assert pod_spec["dns_policy"] == "server_override_value"
        assert pod_metadata["labels"]["baz"] == "quux"
        assert pod_metadata["labels"]["foo"] == "bar"

        # Ensure that agent_id was properly set on deployment
        deployment_labels = body["metadata"]["labels"]
        assert deployment_labels["agent_id"] == instance.instance_uuid

        # Verify service_spec_config from location-level container_context is applied
        # This exercises the persisted code-location container_context path
        # (K8sContainerContext.create_from_config -> job.py config_type_container_context)

        user_code_launcher._start_new_server_spinup(  # noqa: SLF001
            deployment_name="acme",
            location_name="sandbox",
            desired_entry=UserCodeLauncherEntry(
                CodeLocationDeployData(
                    "bizbuz",
                    package_name="blim",
                    container_context={
                        "k8s": {
                            "namespace": "my_override_namespace",
                            "server_k8s_config": {
                                "container_config": {
                                    "command": ["echo", "SERVER_OVERRIDE"],
                                },
                                "service_spec_config": {"cluster_ip": "None"},
                            },
                        }
                    },
                ),
                time.time(),
            ),
        )

        # Verify the service was created with service_spec_config from location context
        service_calls = [
            call
            for call in mock_k8s_core_api_client.method_calls
            if call[0] == "create_namespaced_service"
        ]
        latest_service = service_calls[-1]
        service_body = latest_service[1][1].to_dict()
        assert service_body["spec"]["cluster_ip"] == "None"

        # Create a server with merge_behavior SHALLOW - labels are replaced rather than added

        user_code_launcher._start_new_server_spinup(  # noqa: SLF001
            deployment_name="acme",
            location_name="sandbox",
            desired_entry=UserCodeLauncherEntry(
                CodeLocationDeployData(
                    "bizbuz",
                    package_name="blim",
                    container_context={
                        "k8s": {
                            "namespace": "my_override_namespace",
                            "server_k8s_config": {
                                "container_config": {
                                    "command": ["echo", "SERVER_OVERRIDE"],
                                },
                                "pod_template_spec_metadata": {
                                    "labels": {"baz": "quux"},
                                },
                                "pod_spec_config": {"dns_policy": "server_override_value"},
                                "merge_behavior": "SHALLOW",
                            },
                        }
                    },
                ),
                time.time(),
            ),
        )
        mock_method_calls = mock_k8s_apps_api_client.method_calls
        method_name, _args, kwargs = mock_method_calls[-1]
        assert method_name == "create_namespaced_deployment"

        body = kwargs["body"].to_dict()

        pod_spec = body["spec"]["template"]["spec"]
        pod_metadata = body["spec"]["template"]["metadata"]
        assert pod_metadata["labels"]["baz"] == "quux"
        assert "foo" not in pod_metadata["labels"]


@pytest.fixture
def core_api_client(mocker):
    return mocker.Mock()


@pytest.fixture
def apps_api_client(mocker):
    api_client = mocker.Mock()
    replicaset_mock = Mock()
    replicaset_mock.metadata.name = "test-replicaset"
    api_client.list_namespaced_replica_set.return_value.items = [replicaset_mock]
    return api_client


@pytest.fixture
def mock_dagster_k8s_client():
    with mock.patch(
        "dagster_cloud.workspace.kubernetes.utils.DagsterKubernetesClient.production_client"
    ) as mock_dagster_k8s_client:
        api_client_mock = Mock()
        api_client_mock.get_pod_debug_info.return_value = "Pod debug info"
        mock_dagster_k8s_client.return_value = api_client_mock
        yield mock_dagster_k8s_client


def test_get_deployment_failure_debug_info_no_replicaset_warnings(
    core_api_client, apps_api_client, mock_dagster_k8s_client
):
    namespace = "default"
    k8s_deployment_name = "test-deployment"

    core_api_client.list_namespaced_event.return_value.items = []

    pod_mock = Mock()
    pod_mock.metadata.name = "test-pod"
    pod_list = [pod_mock]

    result = get_deployment_failure_debug_info(
        k8s_deployment_name,
        namespace,
        core_api_client,
        pod_list,
        logging.getLogger("test"),
        apps_api_client,
    )

    assert (
        result
        == """Pod debug info

No warning events for replicaset test-replicaset.

For more information about the failure, run `kubectl describe pod test-pod` or `kubectl describe deployment test-deployment` in your cluster."""
    )


def test_get_deployment_failure_debug_info_with_replicaset_warnings(
    core_api_client, apps_api_client, mock_dagster_k8s_client
):
    namespace = "default"
    k8s_deployment_name = "test-deployment"

    event_mock = Mock()
    event_mock.reason = "FailedCreate"
    event_mock.message = "Error creating: pod already exists"
    event_mock.count = 10
    core_api_client.list_namespaced_event.return_value.items = [event_mock]

    pod_mock = Mock()
    pod_mock.metadata.name = "test-pod"
    pod_list = [pod_mock]

    result = get_deployment_failure_debug_info(
        k8s_deployment_name,
        namespace,
        core_api_client,
        pod_list,
        logging.getLogger("test"),
        apps_api_client,
    )

    assert (
        result
        == """Pod debug info

Warning events for replicaset test-replicaset:
FailedCreate: Error creating: pod already exists (x10)

For more information about the failure, run `kubectl describe pod test-pod` or `kubectl describe deployment test-deployment` in your cluster."""
    )


def test_get_deployment_failure_debug_info_with_exceptions(
    core_api_client, apps_api_client, caplog
):
    namespace = "default"
    k8s_deployment_name = "test-deployment"

    apps_api_client.list_namespaced_replica_set.side_effect = Exception("Replicaset error")

    core_api_client.list_namespaced_event.return_value.items = []

    pod_list = []

    with caplog.at_level(logging.ERROR, logger="test"):
        result = get_deployment_failure_debug_info(
            k8s_deployment_name,
            namespace,
            core_api_client,
            pod_list,
            logging.getLogger("test"),
            apps_api_client,
        )

        assert (
            result
            == "For more information about the failure, run `kubectl describe deployment test-deployment` in your cluster."
        )

        records = [r for r in caplog.records if r.name == "test"]
        assert len(records) == 1
        assert "Failure fetching replicaset debug info" in str(records[0])


def test_construct_code_location_service_custom_port(monkeypatch):
    """Test that construct_code_location_service uses DAGSTER_CLOUD_CODE_SERVER_PORT env var."""
    monkeypatch.setenv("DAGSTER_CLOUD_CODE_SERVER_PORT", "5000")

    resource_name = unique_k8s_resource_name("sandbox", "biz.buz")
    container_context = K8sContainerContext()

    with k8s_instance() as instance:
        server_timestamp = time.time()
        obj = construct_code_location_service(
            "sandbox",
            "biz.buz",
            resource_name,
            container_context,
            instance,
            server_timestamp,
        ).to_dict()

        assert obj["spec"]["ports"][0]["port"] == 5000


def test_construct_code_location_deployment_custom_port(monkeypatch):
    """Test that construct_code_location_deployment uses DAGSTER_CLOUD_CODE_SERVER_PORT env var."""
    monkeypatch.setenv("DAGSTER_CLOUD_CODE_SERVER_PORT", "5000")

    resource_name = unique_k8s_resource_name("sandbox", "foobar")
    container_context = K8sContainerContext()

    with k8s_instance() as instance:
        obj = construct_code_location_deployment(
            instance,
            deployment_name="sandbox",
            location_name="foobar_",
            k8s_deployment_name=resource_name,
            metadata=CodeLocationDeployData("bizbuz", package_name="blim"),
            container_context=container_context,
            args=["ls"],
            server_timestamp=time.time(),
        ).to_dict()

        container_env = obj["spec"]["template"]["spec"]["containers"][0]["env"]
        port_env = next(e for e in container_env if e["name"] == "DAGSTER_CLI_API_GRPC_PORT")
        assert port_env["value"] == "5000"


def test_construct_code_location_deployment_default_server_replica_count():
    resource_name = unique_k8s_resource_name("sandbox", "foobar")
    with k8s_instance() as instance:
        obj = construct_code_location_deployment(
            instance,
            deployment_name="sandbox",
            location_name="foobar_",
            k8s_deployment_name=resource_name,
            metadata=CodeLocationDeployData("bizbuz", package_name="blim"),
            container_context=K8sContainerContext(),
            args=["ls"],
            server_timestamp=time.time(),
        ).to_dict()

        # Single-replica default leaves spec.replicas unset (k8s defaults to 1) and
        # does not inject a readiness probe.
        assert "replicas" not in obj["spec"] or obj["spec"]["replicas"] is None
        assert obj["spec"]["template"]["spec"]["containers"][0].get("readiness_probe") is None


def test_construct_code_location_deployment_server_replica_count_injects_probe():
    resource_name = unique_k8s_resource_name("sandbox", "foobar")
    with k8s_instance() as instance:
        obj = construct_code_location_deployment(
            instance,
            deployment_name="sandbox",
            location_name="foobar_",
            k8s_deployment_name=resource_name,
            metadata=CodeLocationDeployData("bizbuz", package_name="blim"),
            container_context=K8sContainerContext(server_replica_count=3),
            args=["ls"],
            server_timestamp=time.time(),
            server_replica_count=3,
        ).to_dict()

        assert obj["spec"]["replicas"] == 3
        # The Dagster gRPC server only binds its port after user code is loaded,
        # so a tcpSocket probe gates routing on user-code-imported.
        from dagster_cloud.workspace.user_code_launcher.utils import get_code_server_port

        probe = obj["spec"]["template"]["spec"]["containers"][0]["readiness_probe"]
        assert probe["tcp_socket"]["port"] == get_code_server_port()


def test_construct_code_location_deployment_server_replica_count_preserves_user_probe():
    resource_name = unique_k8s_resource_name("sandbox", "foobar")
    user_probe = {
        "http_get": {"path": "/healthz", "port": 8080},
        "period_seconds": 7,
    }
    with k8s_instance() as instance:
        container_context = K8sContainerContext(
            server_replica_count=2,
            server_k8s_config=UserDefinedDagsterK8sConfig.from_dict(
                {"container_config": {"readiness_probe": user_probe}}
            ),
        )
        obj = construct_code_location_deployment(
            instance,
            deployment_name="sandbox",
            location_name="foobar_",
            k8s_deployment_name=resource_name,
            metadata=CodeLocationDeployData("bizbuz", package_name="blim"),
            container_context=container_context,
            args=["ls"],
            server_timestamp=time.time(),
            server_replica_count=2,
        ).to_dict()

        assert obj["spec"]["replicas"] == 2
        # User-supplied probe is left alone — we do not overwrite with the default tcpSocket.
        probe = obj["spec"]["template"]["spec"]["containers"][0]["readiness_probe"]
        assert probe["http_get"]["path"] == "/healthz"
        assert probe["http_get"]["port"] == 8080
        assert probe["period_seconds"] == 7
        assert "tcp_socket" not in probe or probe["tcp_socket"] is None


def test_k8s_container_context_server_replica_count_from_config():
    container_context = K8sContainerContext.create_from_config(
        {"k8s": {"server_replica_count": 4}},
    )
    assert container_context.server_replica_count == 4


def test_k8s_container_context_server_replica_count_merge_override():
    base = K8sContainerContext(server_replica_count=2)
    override = K8sContainerContext(server_replica_count=5)
    assert base.merge(override).server_replica_count == 5
    # An explicit None on the right side should not clobber a set base value.
    assert base.merge(K8sContainerContext()).server_replica_count == 2


# ---------------------------------------------------------------------------
# defs_state_info override ConfigMap (dormant mount + v2 label)
# ---------------------------------------------------------------------------


def test_defs_state_config_map_name_deterministic_and_under_63_chars():
    # Same k8s Deployment name ⇒ same CM name (reload/cleanup depend on this).
    name_a = defs_state_config_map_name("sandbox-acme-abc123")
    name_b = defs_state_config_map_name("sandbox-acme-abc123")
    assert name_a == name_b
    assert name_a.startswith(DEFS_STATE_CONFIG_MAP_NAME_PREFIX)
    # K8s resource-name limit; the prefix(19) + sha1(40) budget must fit.
    assert len(name_a) <= 63
    # Even with pathological inputs, the deterministic hash keeps us under the limit.
    huge = defs_state_config_map_name("x" * 500)
    assert len(huge) <= 63
    # Per-INCARNATION, not per-location: two incarnations of the same location
    # (different uuid suffixes) must own distinct CMs, so removing the old
    # server can never delete the CM the live replacement mounts.
    assert defs_state_config_map_name("sandbox-acme-abc123") != defs_state_config_map_name(
        "sandbox-acme-def456"
    )


def test_construct_defs_state_config_map_shape():
    with k8s_instance() as instance:
        ts = time.time()
        cm = construct_defs_state_config_map(
            deployment_name="acme",
            location_name="sandbox",
            k8s_deployment_name="sandbox-acme-abc123",
            instance=instance,
            server_timestamp=ts,
            serialized_defs_state_info='{"some": "json"}',
        ).to_dict()
        assert cm["metadata"]["name"] == defs_state_config_map_name("sandbox-acme-abc123")
        labels = cm["metadata"]["labels"]
        assert labels["managed_by"] == "K8sUserCodeLauncher"
        assert labels["location_name"] == "sandbox"
        assert labels["deployment_name"] == "acme"
        assert labels["server_timestamp"] == str(ts)
        assert cm["data"] == {DEFS_STATE_OVERRIDE_FILENAME: '{"some": "json"}'}


def test_construct_code_location_deployment_no_mount_by_default():
    """Sanity: without mount_defs_state_config_map=True, the spec is unchanged."""
    resource_name = unique_k8s_resource_name("acme", "sandbox")
    with k8s_instance() as instance:
        obj = construct_code_location_deployment(
            instance,
            deployment_name="acme",
            location_name="sandbox",
            k8s_deployment_name=resource_name,
            metadata=CodeLocationDeployData("img", package_name="pkg"),
            container_context=K8sContainerContext(),
            args=["ls"],
            server_timestamp=time.time(),
        ).to_dict()
    pod_spec = obj["spec"]["template"]["spec"]
    container = pod_spec["containers"][0]
    volume_names = {v["name"] for v in (pod_spec.get("volumes") or [])}
    mount_names = {m["name"] for m in (container.get("volume_mounts") or [])}
    assert DEFS_STATE_VOLUME_NAME not in volume_names
    assert DEFS_STATE_VOLUME_NAME not in mount_names
    assert SERVER_SPEC_VERSION_LABEL_KEY not in obj["metadata"]["labels"]
    assert SERVER_SPEC_VERSION_LABEL_KEY not in pod_spec.get("metadata", {}).get("labels", {})


def test_construct_code_location_deployment_with_mount_injects_volume_mount_and_label():
    resource_name = unique_k8s_resource_name("acme", "sandbox")
    with k8s_instance() as instance:
        obj = construct_code_location_deployment(
            instance,
            deployment_name="acme",
            location_name="sandbox",
            k8s_deployment_name=resource_name,
            metadata=CodeLocationDeployData("img", package_name="pkg"),
            container_context=K8sContainerContext(),
            args=["ls"],
            server_timestamp=time.time(),
            mount_defs_state_config_map=True,
        ).to_dict()

    pod_spec = obj["spec"]["template"]["spec"]
    container = pod_spec["containers"][0]

    volume = next(v for v in pod_spec["volumes"] if v["name"] == DEFS_STATE_VOLUME_NAME)
    # Volume references THIS incarnation's CM (keyed on the k8s Deployment name).
    assert volume["config_map"]["name"] == defs_state_config_map_name(resource_name)
    # optional: True so a manually-deleted CM doesn't block pod startup.
    assert volume["config_map"]["optional"] is True

    mount = next(m for m in container["volume_mounts"] if m["name"] == DEFS_STATE_VOLUME_NAME)
    assert mount["mount_path"] == DEFS_STATE_MOUNT_PATH
    assert mount["read_only"] is True
    # INVARIANT: never use subPath — ConfigMap live-updates don't propagate to subPath mounts.
    assert "sub_path" not in mount or mount["sub_path"] is None

    # Spec-version label on Deployment metadata AND pod template metadata.
    assert obj["metadata"]["labels"][SERVER_SPEC_VERSION_LABEL_KEY] == SERVER_SPEC_VERSION_V2
    pod_labels = obj["spec"]["template"]["metadata"]["labels"]
    assert pod_labels[SERVER_SPEC_VERSION_LABEL_KEY] == SERVER_SPEC_VERSION_V2


def test_construct_code_location_deployment_rejects_user_volume_name_collision():
    """Defensive: error clearly if a user-supplied volume shadows our reserved name."""
    resource_name = unique_k8s_resource_name("acme", "sandbox")
    user_container_context = K8sContainerContext(
        volumes=[{"name": DEFS_STATE_VOLUME_NAME, "config_map": {"name": "user-cm"}}],
        volume_mounts=[{"name": DEFS_STATE_VOLUME_NAME, "mount_path": "/x"}],
    )
    with k8s_instance() as instance:
        with pytest.raises(Exception, match="collides with the reserved defs-state override"):
            construct_code_location_deployment(
                instance,
                deployment_name="acme",
                location_name="sandbox",
                k8s_deployment_name=resource_name,
                metadata=CodeLocationDeployData("img", package_name="pkg"),
                container_context=user_container_context,
                args=["ls"],
                server_timestamp=time.time(),
                mount_defs_state_config_map=True,
            )


def test_start_new_server_spinup_creates_config_map_for_standalone(kubeconfig_file):
    mock_apps = mock.MagicMock()
    mock_core = mock.MagicMock()
    with k8s_instance() as instance:
        launcher = K8sUserCodeLauncher(
            dagster_home="/opt/dagster/dagster_home",
            instance_config_map="dagster-instance",
            service_account_name="MY_SERVICE_ACCOUNT_NAME",
            namespace="default",
            kubeconfig_file=kubeconfig_file,
            k8s_apps_api_client=mock_apps,
            k8s_core_api_client=mock_core,
        )
        launcher.register_instance(instance)
        launcher._start_new_server_spinup(  # noqa: SLF001
            deployment_name="acme",
            location_name="sandbox",
            desired_entry=UserCodeLauncherEntry(
                CodeLocationDeployData("bizbuz", package_name="blim"), time.time()
            ),
        )

    # ConfigMap created BEFORE the Deployment so a racing new pod sees the pin.
    cm_calls = [
        (name, args, kw)
        for (name, args, kw) in mock_core.method_calls
        if name == "create_namespaced_config_map"
    ]
    assert len(cm_calls) == 1
    _, cm_args, _ = cm_calls[0]
    namespace_arg, body_arg = cm_args
    assert namespace_arg == "default"
    cm = body_arg.to_dict()
    # No pin yet (CodeLocationDeployData has defs_state_info=None) ⇒ empty file,
    # which the OSS-side reader treats as an explicit "no pin".
    assert cm["data"][DEFS_STATE_OVERRIDE_FILENAME] == ""

    # Deployment body carries v2 spec-version + the volume mount.
    deploy_name, _deploy_args, deploy_kw = next(
        c for c in mock_apps.method_calls if c[0] == "create_namespaced_deployment"
    )
    assert deploy_name == "create_namespaced_deployment"
    body = deploy_kw["body"].to_dict()
    assert body["metadata"]["labels"][SERVER_SPEC_VERSION_LABEL_KEY] == SERVER_SPEC_VERSION_V2

    # CM is named per-incarnation from the generated k8s Deployment name, and
    # the Deployment's volume references exactly that CM.
    k8s_deployment_name = body["metadata"]["name"]
    assert cm["metadata"]["name"] == defs_state_config_map_name(k8s_deployment_name)
    volume = next(
        v
        for v in body["spec"]["template"]["spec"]["volumes"]
        if v["name"] == DEFS_STATE_VOLUME_NAME
    )
    assert volume["config_map"]["name"] == defs_state_config_map_name(k8s_deployment_name)


def test_start_new_server_spinup_skips_config_map_for_pex(kubeconfig_file):
    """Multipex pods get pins via CreatePexServerArgs, not a CM. Skip entirely."""
    from dagster_cloud_cli.core.workspace import PexMetadata

    mock_apps = mock.MagicMock()
    mock_core = mock.MagicMock()
    with k8s_instance() as instance:
        launcher = K8sUserCodeLauncher(
            dagster_home="/opt/dagster/dagster_home",
            instance_config_map="dagster-instance",
            service_account_name="MY_SERVICE_ACCOUNT_NAME",
            namespace="default",
            kubeconfig_file=kubeconfig_file,
            k8s_apps_api_client=mock_apps,
            k8s_core_api_client=mock_core,
        )
        launcher.register_instance(instance)
        launcher._start_new_server_spinup(  # noqa: SLF001
            deployment_name="acme",
            location_name="sandbox",
            desired_entry=UserCodeLauncherEntry(
                CodeLocationDeployData(
                    "bizbuz",
                    package_name="blim",
                    pex_metadata=PexMetadata(pex_tag="files=deps-hash.pex:source-hash.pex"),
                ),
                time.time(),
            ),
        )
    cm_creates = [c for c in mock_core.method_calls if c[0] == "create_namespaced_config_map"]
    assert cm_creates == []

    deploy_name, _deploy_args, deploy_kw = next(
        c for c in mock_apps.method_calls if c[0] == "create_namespaced_deployment"
    )
    assert deploy_name == "create_namespaced_deployment"
    body = deploy_kw["body"].to_dict()
    # No v2 label, no override volume on the multipex Deployment.
    assert SERVER_SPEC_VERSION_LABEL_KEY not in body["metadata"]["labels"]
    volume_names = {v["name"] for v in (body["spec"]["template"]["spec"].get("volumes") or [])}
    assert DEFS_STATE_VOLUME_NAME not in volume_names


def test_start_new_server_spinup_skips_config_map_for_multi_replica(kubeconfig_file):
    mock_apps = mock.MagicMock()
    mock_core = mock.MagicMock()
    with k8s_instance() as instance:
        launcher = K8sUserCodeLauncher(
            dagster_home="/opt/dagster/dagster_home",
            instance_config_map="dagster-instance",
            service_account_name="MY_SERVICE_ACCOUNT_NAME",
            namespace="default",
            kubeconfig_file=kubeconfig_file,
            k8s_apps_api_client=mock_apps,
            k8s_core_api_client=mock_core,
        )
        launcher.register_instance(instance)
        # Force multi-replica via container_context (via metadata).
        launcher._start_new_server_spinup(  # noqa: SLF001
            deployment_name="acme",
            location_name="sandbox",
            desired_entry=UserCodeLauncherEntry(
                CodeLocationDeployData(
                    "bizbuz",
                    package_name="blim",
                    container_context={"k8s": {"server_replica_count": 3}},
                ),
                time.time(),
            ),
        )
    cm_creates = [c for c in mock_core.method_calls if c[0] == "create_namespaced_config_map"]
    assert cm_creates == []


def test_start_new_server_spinup_config_map_idempotent_on_409(kubeconfig_file):
    """Deterministic CM name ⇒ pre-existing CM from a prior spinup is replaced."""
    mock_apps = mock.MagicMock()
    mock_core = mock.MagicMock()
    mock_core.create_namespaced_config_map.side_effect = ApiException(status=409, reason="exists")

    with k8s_instance() as instance:
        launcher = K8sUserCodeLauncher(
            dagster_home="/opt/dagster/dagster_home",
            instance_config_map="dagster-instance",
            service_account_name="MY_SERVICE_ACCOUNT_NAME",
            namespace="default",
            kubeconfig_file=kubeconfig_file,
            k8s_apps_api_client=mock_apps,
            k8s_core_api_client=mock_core,
        )
        launcher.register_instance(instance)
        launcher._start_new_server_spinup(  # noqa: SLF001
            deployment_name="acme",
            location_name="sandbox",
            desired_entry=UserCodeLauncherEntry(
                CodeLocationDeployData("bizbuz", package_name="blim"), time.time()
            ),
        )
    replace_calls = [c for c in mock_core.method_calls if c[0] == "replace_namespaced_config_map"]
    assert len(replace_calls) == 1


def test_remove_server_handle_deletes_own_defs_state_config_map():
    """Removal deletes exactly this incarnation's CM (derived from handle.name) —
    never a CM belonging to a live replacement server for the same location.
    """
    from dagster_cloud.workspace.kubernetes.launcher import K8sHandle

    mock_apps = mock.MagicMock()
    mock_core = mock.MagicMock()
    with k8s_instance() as instance:
        launcher = K8sUserCodeLauncher(
            dagster_home="/opt/dagster/dagster_home",
            instance_config_map="dagster-instance",
            service_account_name="MY_SERVICE_ACCOUNT_NAME",
            namespace="default",
            k8s_apps_api_client=mock_apps,
            k8s_core_api_client=mock_core,
        )
        launcher.register_instance(instance)
        handle = K8sHandle(
            namespace="default",
            name="sandbox-acme-abc123",
            labels={},
            creation_timestamp=None,
        )
        launcher._remove_server_handle(handle)  # noqa: SLF001

    cm_deletes = [c for c in mock_core.method_calls if c[0] == "delete_namespaced_config_map"]
    assert len(cm_deletes) == 1
    _, args, _ = cm_deletes[0]
    cm_name_arg, namespace_arg = args
    assert cm_name_arg == defs_state_config_map_name("sandbox-acme-abc123")
    # A sibling incarnation's CM has a different name — untouched by construction.
    assert cm_name_arg != defs_state_config_map_name("sandbox-acme-def456")
    assert namespace_arg == "default"


def test_remove_server_handle_cm_404_is_swallowed():
    """Pre-v2 Deployment ⇒ no CM ⇒ delete returns 404 ⇒ swallowed (logged not raised)."""
    from dagster_cloud.workspace.kubernetes.launcher import K8sHandle

    mock_apps = mock.MagicMock()
    mock_core = mock.MagicMock()
    mock_core.delete_namespaced_config_map.side_effect = ApiException(status=404, reason="missing")
    with k8s_instance() as instance:
        launcher = K8sUserCodeLauncher(
            dagster_home="/opt/dagster/dagster_home",
            instance_config_map="dagster-instance",
            service_account_name="MY_SERVICE_ACCOUNT_NAME",
            namespace="default",
            k8s_apps_api_client=mock_apps,
            k8s_core_api_client=mock_core,
        )
        launcher.register_instance(instance)
        handle = K8sHandle(
            namespace="default",
            name="some-deployment-name",
            labels={},
            creation_timestamp=None,
        )
        # Should not raise.
        launcher._remove_server_handle(handle)  # noqa: SLF001


# ---------------------------------------------------------------------------
# defs_state_info override env var + supports_in_place_pin_reload (PR 3)
# ---------------------------------------------------------------------------


def test_construct_code_location_deployment_injects_env_var_when_mounted():
    """PR 3 activates the env var on v2 Deployments."""
    resource_name = unique_k8s_resource_name("acme", "sandbox")
    with k8s_instance() as instance:
        obj = construct_code_location_deployment(
            instance,
            deployment_name="acme",
            location_name="sandbox",
            k8s_deployment_name=resource_name,
            metadata=CodeLocationDeployData("img", package_name="pkg"),
            container_context=K8sContainerContext(),
            args=["ls"],
            server_timestamp=time.time(),
            mount_defs_state_config_map=True,
        ).to_dict()
    container = obj["spec"]["template"]["spec"]["containers"][0]
    envs = {e["name"]: e["value"] for e in container["env"]}
    assert (
        envs[DEFS_STATE_OVERRIDE_ENV] == f"{DEFS_STATE_MOUNT_PATH}/{DEFS_STATE_OVERRIDE_FILENAME}"
    )


def test_construct_code_location_deployment_no_env_var_when_not_mounted():
    resource_name = unique_k8s_resource_name("acme", "sandbox")
    with k8s_instance() as instance:
        obj = construct_code_location_deployment(
            instance,
            deployment_name="acme",
            location_name="sandbox",
            k8s_deployment_name=resource_name,
            metadata=CodeLocationDeployData("img", package_name="pkg"),
            container_context=K8sContainerContext(),
            args=["ls"],
            server_timestamp=time.time(),
        ).to_dict()
    container = obj["spec"]["template"]["spec"]["containers"][0]
    env_names = {e["name"] for e in (container.get("env") or [])}
    assert DEFS_STATE_OVERRIDE_ENV not in env_names


def _make_grpc_server_with_labels(labels: dict) -> DagsterCloudGrpcServer:
    """Stand-in for a DagsterCloudGrpcServer with a labeled server_handle."""
    from dagster_cloud.workspace.kubernetes.launcher import K8sHandle
    from dagster_cloud.workspace.user_code_launcher import ServerEndpoint

    return DagsterCloudGrpcServer(
        server_handle=K8sHandle(
            namespace="default",
            name="some-server",
            labels=labels,
            creation_timestamp=None,
        ),
        server_endpoint=ServerEndpoint(host="x", port=4000, socket=None),
        code_location_deploy_data=CodeLocationDeployData("img", package_name="pkg"),
    )


def test_supports_in_place_pin_reload_true_when_v2_label_present(kubeconfig_file):
    with k8s_instance() as instance:
        launcher = K8sUserCodeLauncher(
            dagster_home="/opt/dagster/dagster_home",
            instance_config_map="dagster-instance",
            service_account_name="MY_SERVICE_ACCOUNT_NAME",
            namespace="default",
            kubeconfig_file=kubeconfig_file,
        )
        launcher.register_instance(instance)
        launcher._grpc_servers[("acme", "sandbox")] = _make_grpc_server_with_labels(  # noqa: SLF001
            {SERVER_SPEC_VERSION_LABEL_KEY: SERVER_SPEC_VERSION_V2}
        )
        entry = UserCodeLauncherEntry(
            CodeLocationDeployData("img", package_name="pkg"), time.time()
        )
        assert launcher.supports_in_place_pin_reload(("acme", "sandbox"), entry) is True


def test_supports_in_place_pin_reload_false_for_legacy_deployment(kubeconfig_file):
    """Pre-v2 Deployments don't carry the label ⇒ fast path stays off."""
    with k8s_instance() as instance:
        launcher = K8sUserCodeLauncher(
            dagster_home="/opt/dagster/dagster_home",
            instance_config_map="dagster-instance",
            service_account_name="MY_SERVICE_ACCOUNT_NAME",
            namespace="default",
            kubeconfig_file=kubeconfig_file,
        )
        launcher.register_instance(instance)
        launcher._grpc_servers[("acme", "sandbox")] = _make_grpc_server_with_labels(  # noqa: SLF001
            {"managed_by": "K8sUserCodeLauncher"}  # no spec-version label
        )
        entry = UserCodeLauncherEntry(
            CodeLocationDeployData("img", package_name="pkg"), time.time()
        )
        assert launcher.supports_in_place_pin_reload(("acme", "sandbox"), entry) is False


def test_supports_in_place_pin_reload_false_when_multi_replica(kubeconfig_file):
    with k8s_instance() as instance:
        launcher = K8sUserCodeLauncher(
            dagster_home="/opt/dagster/dagster_home",
            instance_config_map="dagster-instance",
            service_account_name="MY_SERVICE_ACCOUNT_NAME",
            namespace="default",
            kubeconfig_file=kubeconfig_file,
        )
        launcher.register_instance(instance)
        launcher._grpc_servers[("acme", "sandbox")] = _make_grpc_server_with_labels(  # noqa: SLF001
            {SERVER_SPEC_VERSION_LABEL_KEY: SERVER_SPEC_VERSION_V2}
        )
        entry = UserCodeLauncherEntry(
            CodeLocationDeployData(
                "img",
                package_name="pkg",
                container_context={"k8s": {"server_replica_count": 3}},
            ),
            time.time(),
        )
        assert launcher.supports_in_place_pin_reload(("acme", "sandbox"), entry) is False


def test_supports_in_place_pin_reload_false_for_pex(kubeconfig_file):
    from dagster_cloud_cli.core.workspace import PexMetadata

    with k8s_instance() as instance:
        launcher = K8sUserCodeLauncher(
            dagster_home="/opt/dagster/dagster_home",
            instance_config_map="dagster-instance",
            service_account_name="MY_SERVICE_ACCOUNT_NAME",
            namespace="default",
            kubeconfig_file=kubeconfig_file,
        )
        launcher.register_instance(instance)
        launcher._grpc_servers[("acme", "sandbox")] = _make_grpc_server_with_labels(  # noqa: SLF001
            {SERVER_SPEC_VERSION_LABEL_KEY: SERVER_SPEC_VERSION_V2}
        )
        entry = UserCodeLauncherEntry(
            CodeLocationDeployData(
                "img",
                package_name="pkg",
                pex_metadata=PexMetadata(pex_tag="files=deps-hash.pex:source-hash.pex"),
            ),
            time.time(),
        )
        assert launcher.supports_in_place_pin_reload(("acme", "sandbox"), entry) is False


def test_supports_in_place_pin_reload_false_when_no_server_cached(kubeconfig_file):
    """Transient state: server not yet in _grpc_servers ⇒ fast path off."""
    with k8s_instance() as instance:
        launcher = K8sUserCodeLauncher(
            dagster_home="/opt/dagster/dagster_home",
            instance_config_map="dagster-instance",
            service_account_name="MY_SERVICE_ACCOUNT_NAME",
            namespace="default",
            kubeconfig_file=kubeconfig_file,
        )
        launcher.register_instance(instance)
        entry = UserCodeLauncherEntry(
            CodeLocationDeployData("img", package_name="pkg"), time.time()
        )
        assert launcher.supports_in_place_pin_reload(("acme", "sandbox"), entry) is False


def test_reload_pin_in_place_writes_config_map_then_calls_super(kubeconfig_file):
    """ConfigMap writes must happen BEFORE the RPC so a racing new pod sees the pin."""
    mock_core = mock.MagicMock()
    with k8s_instance() as instance:
        launcher = K8sUserCodeLauncher(
            dagster_home="/opt/dagster/dagster_home",
            instance_config_map="dagster-instance",
            service_account_name="MY_SERVICE_ACCOUNT_NAME",
            namespace="default",
            kubeconfig_file=kubeconfig_file,
            k8s_core_api_client=mock_core,
        )
        launcher.register_instance(instance)
        # Seed a running v2 server so the base class's RPC path has something
        # to send to (we'll mock the client below).
        launcher._grpc_servers[("acme", "sandbox")] = _make_grpc_server_with_labels(  # noqa: SLF001
            {SERVER_SPEC_VERSION_LABEL_KEY: SERVER_SPEC_VERSION_V2}
        )
        entry = UserCodeLauncherEntry(
            CodeLocationDeployData("img", package_name="pkg"), time.time()
        )

        call_order: list[str] = []
        mock_core.create_namespaced_config_map.side_effect = lambda *a, **kw: call_order.append(
            "cm"
        )

        with mock.patch(
            "dagster_cloud.workspace.user_code_launcher.user_code_launcher.DagsterCloudUserCodeLauncher._reload_pin_in_place"
        ) as mocked_super:
            mocked_super.side_effect = lambda *a, **kw: call_order.append("rpc")
            launcher._reload_pin_in_place(("acme", "sandbox"), entry)  # noqa: SLF001

        assert call_order == ["cm", "rpc"]


def test_reload_pin_in_place_cm_written_even_when_rpc_fails(kubeconfig_file):
    """If the gRPC RPC fails, the ConfigMap update has already landed — the
    safety property is that the CM is ALLOWED to be ahead of in-memory state.
    The base class doesn't advance _actual_entries on failure ⇒ reconciler retries.
    """
    mock_core = mock.MagicMock()
    with k8s_instance() as instance:
        launcher = K8sUserCodeLauncher(
            dagster_home="/opt/dagster/dagster_home",
            instance_config_map="dagster-instance",
            service_account_name="MY_SERVICE_ACCOUNT_NAME",
            namespace="default",
            kubeconfig_file=kubeconfig_file,
            k8s_core_api_client=mock_core,
        )
        launcher.register_instance(instance)
        launcher._grpc_servers[("acme", "sandbox")] = _make_grpc_server_with_labels(  # noqa: SLF001
            {SERVER_SPEC_VERSION_LABEL_KEY: SERVER_SPEC_VERSION_V2}
        )
        entry = UserCodeLauncherEntry(
            CodeLocationDeployData("img", package_name="pkg"), time.time()
        )

        with mock.patch(
            "dagster_cloud.workspace.user_code_launcher.user_code_launcher.DagsterCloudUserCodeLauncher._reload_pin_in_place",
            side_effect=Exception("simulated RPC failure"),
        ):
            with pytest.raises(Exception, match="simulated RPC failure"):
                launcher._reload_pin_in_place(("acme", "sandbox"), entry)  # noqa: SLF001

        cm_writes = [
            c
            for c in mock_core.method_calls
            if c[0] in ("create_namespaced_config_map", "replace_namespaced_config_map")
        ]
        assert len(cm_writes) == 1
        # _actual_entries advancement is the base class's responsibility; here
        # we asserted via the mock that the base wasn't allowed to run to that
        # advancement step. Reconciler will see actual!=desired and retry.
        assert ("acme", "sandbox") not in launcher._actual_entries  # noqa: SLF001
