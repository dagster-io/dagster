import subprocess

import pytest
import yaml
from kubernetes.client import models
from schema.charts.dagster.subschema.concurrency import (
    Concurrency,
    ConcurrencyPools,
    ConcurrencyRuns,
    TagConcurrencyLimit,
)
from schema.charts.dagster.subschema.daemon import (
    BlockOpConcurrencyLimitedRuns,
    Daemon,
    QueuedRunCoordinatorConfig,
    RunCoordinator,
    RunCoordinatorConfig,
    RunCoordinatorType,
)
from schema.charts.dagster.values import DagsterHelmValues
from schema.utils.helm_template import HelmTemplate


@pytest.fixture(name="template")
def helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/configmap-instance.yaml",
        model=models.V1ConfigMap,
        namespace="test-namespace",
    )


def test_concurrency_disabled_by_default(template: HelmTemplate):
    """Concurrency block should not render when disabled (default)."""
    helm_values = DagsterHelmValues.construct()
    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    assert "concurrency" not in instance


def test_concurrency_enabled_empty(template: HelmTemplate):
    """Concurrency block renders when enabled, even with default values."""
    helm_values = DagsterHelmValues.construct(
        concurrency=Concurrency(enabled=True),
    )
    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    # With all None values, the concurrency block should be empty (but present)
    assert "concurrency" in instance


def test_concurrency_pools_config(template: HelmTemplate):
    """Test pools configuration renders correctly."""
    helm_values = DagsterHelmValues.construct(
        concurrency=Concurrency(
            enabled=True,
            pools=ConcurrencyPools(
                defaultLimit=10,
                granularity="op",
                opGranularityRunBuffer=2,
            ),
        ),
    )
    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    assert "concurrency" in instance
    concurrency = instance["concurrency"]
    assert concurrency["pools"]["default_limit"] == 10
    assert concurrency["pools"]["granularity"] == "op"
    assert concurrency["pools"]["op_granularity_run_buffer"] == 2


def test_concurrency_runs_config(template: HelmTemplate):
    """Test runs configuration renders correctly."""
    helm_values = DagsterHelmValues.construct(
        concurrency=Concurrency(
            enabled=True,
            runs=ConcurrencyRuns(
                maxConcurrentRuns=25,
            ),
        ),
    )
    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    assert "concurrency" in instance
    concurrency = instance["concurrency"]
    assert concurrency["runs"]["max_concurrent_runs"] == 25


def test_concurrency_tag_concurrency_limits(template: HelmTemplate):
    """Test tag_concurrency_limits renders correctly."""
    helm_values = DagsterHelmValues.construct(
        concurrency=Concurrency(
            enabled=True,
            runs=ConcurrencyRuns(
                tagConcurrencyLimits=[
                    TagConcurrencyLimit(key="database", limit=1),
                    TagConcurrencyLimit(
                        key="team",
                        value={"applyLimitPerUniqueValue": True},
                        limit=2,
                    ),
                ],
            ),
        ),
    )
    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    assert "concurrency" in instance
    concurrency = instance["concurrency"]
    tag_limits = concurrency["runs"]["tag_concurrency_limits"]
    assert len(tag_limits) == 2
    assert tag_limits[0]["key"] == "database"
    assert tag_limits[0]["limit"] == 1
    assert tag_limits[1]["key"] == "team"
    assert tag_limits[1]["value"] == {"applyLimitPerUniqueValue": True}
    assert tag_limits[1]["limit"] == 2


def test_concurrency_full_config(template: HelmTemplate):
    """Test full concurrency configuration renders correctly."""
    helm_values = DagsterHelmValues.construct(
        concurrency=Concurrency(
            enabled=True,
            pools=ConcurrencyPools(
                defaultLimit=5,
                granularity="run",
                opGranularityRunBuffer=1,
            ),
            runs=ConcurrencyRuns(
                maxConcurrentRuns=50,
                tagConcurrencyLimits=[
                    TagConcurrencyLimit(key="env", value="prod", limit=10),
                ],
            ),
        ),
    )
    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    concurrency = instance["concurrency"]
    assert concurrency["pools"]["default_limit"] == 5
    assert concurrency["pools"]["granularity"] == "run"
    assert concurrency["pools"]["op_granularity_run_buffer"] == 1
    assert concurrency["runs"]["max_concurrent_runs"] == 50
    assert len(concurrency["runs"]["tag_concurrency_limits"]) == 1


def test_concurrency_conflict_max_concurrent_runs(template: HelmTemplate):
    """Should fail if both concurrency and run_coordinator have maxConcurrentRuns."""
    helm_values = DagsterHelmValues.construct(
        concurrency=Concurrency(
            enabled=True,
            runs=ConcurrencyRuns(maxConcurrentRuns=25),
        ),
        dagsterDaemon=Daemon.construct(
            runCoordinator=RunCoordinator.construct(
                enabled=True,
                type=RunCoordinatorType.QUEUED,
                config=RunCoordinatorConfig.construct(
                    queuedRunCoordinator=QueuedRunCoordinatorConfig.construct(
                        maxConcurrentRuns=10,
                    ),
                ),
            ),
        ),
    )
    with pytest.raises(subprocess.CalledProcessError):
        template.render(helm_values)


def test_concurrency_conflict_tag_concurrency_limits(template: HelmTemplate):
    """Should fail if both concurrency and run_coordinator have tagConcurrencyLimits."""
    helm_values = DagsterHelmValues.construct(
        concurrency=Concurrency(
            enabled=True,
            runs=ConcurrencyRuns(
                tagConcurrencyLimits=[TagConcurrencyLimit(key="test", limit=1)],
            ),
        ),
        dagsterDaemon=Daemon.construct(
            runCoordinator=RunCoordinator.construct(
                enabled=True,
                type=RunCoordinatorType.QUEUED,
                config=RunCoordinatorConfig.construct(
                    queuedRunCoordinator=QueuedRunCoordinatorConfig.construct(
                        tagConcurrencyLimits=[{"key": "other", "limit": 2}],
                    ),
                ),
            ),
        ),
    )
    with pytest.raises(subprocess.CalledProcessError):
        template.render(helm_values)


def test_concurrency_conflict_op_granularity_run_buffer(template: HelmTemplate):
    """Should fail if both concurrency and run_coordinator have op slot buffer config."""
    helm_values = DagsterHelmValues.construct(
        concurrency=Concurrency(
            enabled=True,
            pools=ConcurrencyPools(opGranularityRunBuffer=2),
        ),
        dagsterDaemon=Daemon.construct(
            runCoordinator=RunCoordinator.construct(
                enabled=True,
                type=RunCoordinatorType.QUEUED,
                config=RunCoordinatorConfig.construct(
                    queuedRunCoordinator=QueuedRunCoordinatorConfig.construct(
                        blockOpConcurrencyLimitedRuns=BlockOpConcurrencyLimitedRuns(
                            enabled=True,
                            opConcurrencySlotBuffer=1,
                        ),
                    ),
                ),
            ),
        ),
    )
    with pytest.raises(subprocess.CalledProcessError):
        template.render(helm_values)


def test_concurrency_no_conflict_when_run_coordinator_disabled(template: HelmTemplate):
    """Should not conflict when run_coordinator is disabled."""
    helm_values = DagsterHelmValues.construct(
        concurrency=Concurrency(
            enabled=True,
            runs=ConcurrencyRuns(maxConcurrentRuns=25),
        ),
        dagsterDaemon=Daemon.construct(
            runCoordinator=RunCoordinator.construct(
                enabled=False,
            ),
        ),
    )
    # Should not raise
    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    assert instance["concurrency"]["runs"]["max_concurrent_runs"] == 25


def test_concurrency_no_conflict_when_only_one_set(template: HelmTemplate):
    """Should not conflict when concurrency is set but run_coordinator fields are not."""
    helm_values = DagsterHelmValues.construct(
        concurrency=Concurrency(
            enabled=True,
            runs=ConcurrencyRuns(maxConcurrentRuns=25),
        ),
        dagsterDaemon=Daemon.construct(
            runCoordinator=RunCoordinator.construct(
                enabled=True,
                type=RunCoordinatorType.QUEUED,
                config=RunCoordinatorConfig.construct(
                    queuedRunCoordinator=QueuedRunCoordinatorConfig.construct(
                        # maxConcurrentRuns is not set (None)
                        dequeueIntervalSeconds=30,
                    ),
                ),
            ),
        ),
    )
    # Should not raise
    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    assert instance["concurrency"]["runs"]["max_concurrent_runs"] == 25


def test_concurrency_zero_values(template: HelmTemplate):
    """Test that zero values render correctly (not treated as falsey)."""
    helm_values = DagsterHelmValues.construct(
        concurrency=Concurrency(
            enabled=True,
            pools=ConcurrencyPools(
                defaultLimit=0,
                opGranularityRunBuffer=0,
            ),
            runs=ConcurrencyRuns(
                maxConcurrentRuns=0,
            ),
        ),
    )
    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    concurrency = instance["concurrency"]
    assert concurrency["pools"]["default_limit"] == 0
    assert concurrency["pools"]["op_granularity_run_buffer"] == 0
    assert concurrency["runs"]["max_concurrent_runs"] == 0
