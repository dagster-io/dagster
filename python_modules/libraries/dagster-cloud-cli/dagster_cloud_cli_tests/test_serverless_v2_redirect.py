"""Serverless on Kubernetes redirects PEX builds to Docker."""

import pytest
from dagster_cloud_cli import gql
from dagster_cloud_cli.commands.ci import (
    DISABLE_PEX_DOCKER_REDIRECT_ENV_VAR,
    BuildStrategy,
    _resolve_build_strategy,  # pyright: ignore[reportPrivateUsage]
)
from dagster_cloud_cli.commands.serverless import (
    _build_pex_docker_bundle_kwargs,  # pyright: ignore[reportPrivateUsage]
    _should_redirect_pex_to_docker,  # pyright: ignore[reportPrivateUsage]
)
from dagster_cloud_cli.core import pex_builder


class _NullClient:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _registry(is_harbor: bool) -> dict:
    return {"registry_url": "registry.example", "is_harbor": is_harbor}


@pytest.mark.parametrize(
    "requested, is_harbor, expected",
    [
        (BuildStrategy.pex, True, BuildStrategy.pex_docker),
        # Classic serverless pushes to ECR and keeps its PEX runtime.
        (BuildStrategy.pex, False, BuildStrategy.pex),
        # A docker build is never rewritten, whatever the registry.
        (BuildStrategy.docker, True, BuildStrategy.docker),
        (BuildStrategy.docker, False, BuildStrategy.docker),
    ],
)
def test_resolve_build_strategy(monkeypatch, requested, is_harbor, expected):
    monkeypatch.setattr(
        "dagster_cloud_cli.commands.ci.utils.get_registry_info",
        lambda url, deployment: _registry(is_harbor),
    )
    assert _resolve_build_strategy(requested, "https://url", "prod") == expected


def test_rollback_to_ecr_keeps_the_python_executable(monkeypatch):
    """A rolled-back org still has its Kubernetes tenant and agent running, on purpose.

    Only the registry moves back to ECR, and that is what routes the location to the classic
    agent -- which does run PEX. Keying on running agents instead would convert these builds to
    Docker during the one operation meant to put things back as they were.
    """
    monkeypatch.setattr(
        "dagster_cloud_cli.commands.ci.utils.get_registry_info",
        lambda url, deployment: _registry(False),
    )
    assert _resolve_build_strategy(BuildStrategy.pex, "https://url", "prod") == BuildStrategy.pex


def test_resolve_build_strategy_falls_back_when_lookup_fails(monkeypatch):
    """A failed registry lookup must not break a build that works today."""

    def _boom(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr("dagster_cloud_cli.commands.ci.utils.get_registry_info", _boom)
    assert _resolve_build_strategy(BuildStrategy.pex, "https://url", "prod") == BuildStrategy.pex


def test_escape_hatch_skips_the_redirect(monkeypatch):
    """The opt-out builds what was asked for, without consulting the registry at all."""

    def _should_not_be_called(*args, **kwargs):
        raise AssertionError("registry lookup should be skipped when the redirect is disabled")

    monkeypatch.setattr(
        "dagster_cloud_cli.commands.ci.utils.get_registry_info", _should_not_be_called
    )
    monkeypatch.setenv(DISABLE_PEX_DOCKER_REDIRECT_ENV_VAR, "1")

    assert _resolve_build_strategy(BuildStrategy.pex, "https://url", "prod") == BuildStrategy.pex


# --- serverless deploy-python-executable path -------------------------------------------------


@pytest.mark.parametrize("is_harbor, expected", [(True, True), (False, False)])
def test_serverless_command_redirects_on_harbor(monkeypatch, is_harbor, expected):
    monkeypatch.setattr(gql, "graphql_client_from_url", lambda *a, **kw: _NullClient())
    monkeypatch.setattr(gql, "get_ecr_info", lambda client: _registry(is_harbor))

    assert _should_redirect_pex_to_docker("https://url", "token", "prod") is expected


def test_serverless_command_falls_back_when_lookup_fails(monkeypatch):
    def _boom(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(gql, "graphql_client_from_url", _boom)
    assert _should_redirect_pex_to_docker("https://url", "token", "prod") is False


def test_serverless_command_escape_hatch(monkeypatch):
    def _should_not_be_called(*args, **kwargs):
        raise AssertionError("registry lookup should be skipped when the redirect is disabled")

    monkeypatch.setattr(gql, "graphql_client_from_url", _should_not_be_called)
    monkeypatch.setenv(DISABLE_PEX_DOCKER_REDIRECT_ENV_VAR, "1")

    assert _should_redirect_pex_to_docker("https://url", "token", "prod") is False


def test_deployment_name_is_read_back_rather_than_assumed(monkeypatch):
    """--deployment is optional and the GitHub action encodes it in the url instead, so the
    bundle must not fall back to a guessed deployment.
    """
    captured: dict = {}

    def _fake_build(**kw):
        captured.update(kw)
        return type("O", (), {"image": "img"})()

    monkeypatch.setattr(gql, "graphql_client_from_url", lambda *a, **kw: _NullClient())
    monkeypatch.setattr(gql, "get_ecr_info", lambda client: _registry(True))
    monkeypatch.setattr(gql, "fetch_deployment_name", lambda client: "branch-abc")
    monkeypatch.setattr(
        "dagster_cloud_cli.commands.serverless.build_pex_docker_bundle", _fake_build
    )

    location = pex_builder.parse_workspace.Location(
        "loc", directory=".", build_folder=".", location_file="f"
    )
    _build_pex_docker_bundle_kwargs(
        url="https://org.dagster.cloud/branch-abc",
        api_token="token",
        location=location,
        build_method=pex_builder.deps.BuildMethod.LOCAL,
        deployment=None,
        kwargs={},
    )
    assert captured["deployment_name"] == "branch-abc"
