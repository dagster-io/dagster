import pytest
import yaml
from kubernetes.client import models
from schema.charts.dagster.subschema.scheduler import (
    DaemonSchedulerConfig,
    Scheduler,
    SchedulerConfig,
    SchedulerType,
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


def test_scheduler_config(template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        scheduler=Scheduler.construct(
            type=SchedulerType.DAEMON,
            config=SchedulerConfig.construct(
                daemonScheduler=DaemonSchedulerConfig.construct(
                    maxCatchupRuns=2,
                    maxTickRetries=2,
                ),
            ),
        )
    )
    configmaps = template.render(helm_values)
    assert len(configmaps) == 1
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    assert instance["scheduler"]["class"] == "DagsterDaemonScheduler"
    assert instance["scheduler"]["config"]["max_catchup_runs"] == 2
    assert instance["scheduler"]["config"]["max_tick_retries"] == 2
