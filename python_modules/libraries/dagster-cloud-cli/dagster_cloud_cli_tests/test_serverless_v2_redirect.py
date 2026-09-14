"""Serverless on Kubernetes redirects PEX builds to Docker."""

import pytest
from dagster_cloud_cli.commands.ci import (
    DISABLE_PEX_DOCKER_REDIRECT_ENV_VAR,
    BuildStrategy,
    _resolve_build_strategy,  # pyright: ignore[reportPrivateUsage]
)


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
