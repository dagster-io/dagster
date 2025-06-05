from dagster.components.lib.executable_component.component import ExecutableComponent


class K8sPipeComponent(ExecutableComponent): ...


import pytest


@pytest.mark.default
def test_pipes_component_client(namespace, cluster_provider):
    assert namespace
    # assert cluster_provider.kubeconfig_file == "/path/to/kubeconfig"
    assert cluster_provider
