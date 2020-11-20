import pytest

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
    """
    Returns a str file path for a minimal kubeconfig file in the default location (~/.kube/config).
    """
    dir_path = tmp_path / ".kube"
    dir_path.mkdir()
    config_path = dir_path / "config"
    config_path.write_text(MINIMAL_KUBECONFIG_CONTENT)
    return str(config_path)
