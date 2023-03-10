import pytest
from dagster._core.test_utils import environ, instance_for_test

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
    """Returns a str file path for a minimal kubeconfig file in the default location (~/.kube/config).
    """
    dir_path = tmp_path / ".kube"
    dir_path.mkdir()
    config_path = dir_path / "config"
    config_path.write_text(MINIMAL_KUBECONFIG_CONTENT)
    return str(config_path)


LAUNCHER_RESOURCES = {
    "requests": {"cpu": "128m", "memory": "64Mi"},
    "limits": {"cpu": "500m", "memory": "1000Mi"},
}


@pytest.fixture
def k8s_run_launcher_instance(kubeconfig_file):  # pylint: disable=redefined-outer-name
    with environ({"BAR_TEST": "bar"}):
        with instance_for_test(
            overrides={
                "run_launcher": {
                    "class": "K8sRunLauncher",
                    "module": "dagster_k8s",
                    "config": {
                        "service_account_name": "dagit-admin",
                        "instance_config_map": "dagster-instance",
                        "postgres_password_secret": "dagster-postgresql-secret",
                        "dagster_home": "/opt/dagster/dagster_home",
                        "job_image": "fake_job_image",
                        "load_incluster_config": False,
                        "kubeconfig_file": kubeconfig_file,
                        "env_vars": ["BAR_TEST"],
                        "resources": LAUNCHER_RESOURCES,
                    },
                },
            }
        ) as instance:
            yield instance
