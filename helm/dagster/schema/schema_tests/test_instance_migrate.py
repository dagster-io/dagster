import subprocess

import pytest
from kubernetes.client import models
from schema.charts.dagster.subschema.migrate import Migrate
from schema.charts.dagster.values import DagsterHelmValues
from schema.utils.helm_template import HelmTemplate


@pytest.fixture(name="template")
def helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/job-instance-migrate.yaml",
        model=models.V1Job,
    )


def test_job_instance_migrate_does_not_render(template: HelmTemplate, capsys):
    with pytest.raises(subprocess.CalledProcessError):
        helm_values_migrate_disabled = DagsterHelmValues.construct(migrate=Migrate(enabled=False))

        template.render(helm_values_migrate_disabled)

        _, err = capsys.readouterr()
        assert "Error: could not find template" in err


def test_job_instance_migrate_renders(template: HelmTemplate):
    helm_values_migrate_enabled = DagsterHelmValues.construct(migrate=Migrate(enabled=True))

    jobs = template.render(helm_values_migrate_enabled)

    assert len(jobs) == 1
