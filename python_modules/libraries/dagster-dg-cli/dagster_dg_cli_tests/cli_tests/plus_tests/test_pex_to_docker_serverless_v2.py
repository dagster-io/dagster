"""Serverless v2 (K8s) redirects PEX builds to Docker."""

import importlib.resources
import json

import pytest
from dagster_dg_cli.cli.plus.build import (
    _gql_client_from_env_or_config,  # pyright: ignore[reportPrivateUsage]
    get_agent_type_and_platform_from_graphql,
)
from dagster_dg_cli.cli.plus.constants import DgPlusAgentPlatform, DgPlusAgentType
from dagster_shared.plus.config import DagsterPlusCliConfig


class _FakeGqlClient:
    def __init__(self, agent_type: str, agents: list[dict]):
        self._response = {"currentDeployment": {"agentType": agent_type}, "agents": agents}

    def execute_arbitrary(self, query: str) -> dict:
        return self._response


def _agent(launcher_class: str, status: str = "RUNNING") -> dict:
    return {"status": status, "metadata": [{"key": "type", "value": json.dumps(launcher_class)}]}


@pytest.mark.parametrize(
    "agent_type, launcher_class, expected_platform",
    [
        # Serverless v2 runs ServerlessK8sUserCodeLauncher -> K8S -> identifies v2.
        ("SERVERLESS", "ServerlessK8sUserCodeLauncher", DgPlusAgentPlatform.K8S),
        # Classic (ECS-backed) Serverless.
        ("SERVERLESS", "ServerlessEcsUserCodeLauncher", DgPlusAgentPlatform.ECS),
        # Hybrid detection is unchanged.
        ("HYBRID", "K8sUserCodeLauncher", DgPlusAgentPlatform.K8S),
        ("HYBRID", "EcsUserCodeLauncher", DgPlusAgentPlatform.ECS),
    ],
)
def test_detects_platform_for_serverless_and_hybrid(
    agent_type: str, launcher_class: str, expected_platform: DgPlusAgentPlatform
):
    client = _FakeGqlClient(agent_type, [_agent(launcher_class)])
    resolved_type, resolved_platform = get_agent_type_and_platform_from_graphql(client)  # ty: ignore[invalid-argument-type]
    assert resolved_type == DgPlusAgentType(agent_type)
    assert resolved_platform == expected_platform


def test_mixed_agents_resolve_to_k8s_deterministically():
    """A mixed v1+v2 org (both a K8s and an ECS agent running during migration) must resolve to
    K8S — the v2 signal that drives the PEX->Docker redirect — regardless of agent order. K8s is
    listed first here, which the old last-wins loop resolved to ECS.
    """
    client = _FakeGqlClient(
        "SERVERLESS",
        [_agent("ServerlessK8sUserCodeLauncher"), _agent("ServerlessEcsUserCodeLauncher")],
    )
    _, resolved_platform = get_agent_type_and_platform_from_graphql(client)  # ty: ignore[invalid-argument-type]
    assert resolved_platform == DgPlusAgentPlatform.K8S


def test_gql_client_none_without_credentials(monkeypatch):
    for var in (
        "DAGSTER_CLOUD_ORGANIZATION",
        "DAGSTER_CLOUD_API_TOKEN",
        "DAGSTER_CLOUD_URL",
        "DAGSTER_CLOUD_DEPLOYMENT",
    ):
        monkeypatch.delenv(var, raising=False)
    assert _gql_client_from_env_or_config(DagsterPlusCliConfig()) is None


def test_pex_bundle_dockerfile_installs_into_default_site_packages():
    dockerfile = (
        importlib.resources.files("dagster_cloud_cli")
        .joinpath("commands/serverless/pex_bundle.Dockerfile")
        .read_text(encoding="utf-8")
    )
    # base image is parameterized by an ARG (built with --build-arg PYTHON_VERSION)
    assert "ARG PYTHON_VERSION" in dockerfile
    assert "FROM python:${PYTHON_VERSION}-slim" in dockerfile
    # both pexes are unpacked at BUILD time (not executed at runtime)
    assert "pex-tools /pexes/deps-*.pex venv" in dockerfile
    assert "pex-tools /pexes/source-*.pex venv" in dockerfile
    # contents installed into the DEFAULT site-packages so the default interpreter finds them
    # without any custom PYTHONPATH (which the agent's launch does not preserve)
    assert "/usr/local/lib/python${PYTHON_VERSION}/site-packages" in dockerfile
    # console scripts land in the default bin with a system-interpreter shebang
    assert "#!/usr/local/bin/python${PYTHON_VERSION}" in dockerfile
    assert "/usr/local/bin/" in dockerfile
    # image relies on no custom env and runs no PEX at runtime (no PYTHONPATH/PATH set, no ENTRYPOINT)
    assert "ENV " not in dockerfile
    assert "ENTRYPOINT" not in dockerfile
